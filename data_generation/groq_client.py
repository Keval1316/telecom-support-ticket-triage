"""
Reusable Groq client wrapper with multi-key rotation, per-key rate limiting,
retry-with-backoff, and structured-JSON parsing.
Never logs raw key values.
"""
import time
import json
import random
import re
from collections import deque
from typing import Optional

from groq import Groq


class KeyState:
    def __init__(self, key: str, index: int, rpm_limit: int, tpm_limit: int, rpd_limit: int):
        self.key = key
        self.index = index
        # max_retries=0: we own all retry/backoff logic ourselves, the SDK
        # must not sleep internally and block our key-rotation.
        self.client = Groq(api_key=key, max_retries=0)
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        self.rpd_limit = rpd_limit
        self.request_times = deque()
        self.token_events = deque()
        self.day_request_count = 0
        self.day_start = time.time()
        self.resting_until = 0.0
        self.daily_exhausted = False

    def _prune(self):
        now = time.time()
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()
        while self.token_events and now - self.token_events[0][0] > 60:
            self.token_events.popleft()
        if now - self.day_start > 86400:
            self.day_start = now
            self.day_request_count = 0
            self.daily_exhausted = False

    def has_headroom(self, est_tokens: int = 500) -> bool:
        self._prune()
        if time.time() < self.resting_until:
            return False
        if len(self.request_times) >= self.rpm_limit:
            return False
        used_tokens = sum(t for _, t in self.token_events)
        if used_tokens + est_tokens > self.tpm_limit:
            return False
        if self.day_request_count >= self.rpd_limit:
            return False
        return True

    def record_usage(self, tokens_used: int):
        now = time.time()
        self.request_times.append(now)
        self.token_events.append((now, tokens_used))
        self.day_request_count += 1

    def rest(self, seconds: float):
        self.resting_until = time.time() + seconds


class GroqKeyPool:
    """Round-robins across multiple Groq API keys, respecting each key's own budget."""

    def __init__(self, keys, rpm_limit=30, tpm_limit=6000, rpd_limit=14400):
        if not keys:
            raise ValueError("GroqKeyPool needs at least one API key")
        self.states = [KeyState(k, i, rpm_limit, tpm_limit, rpd_limit) for i, k in enumerate(keys)]
        self._rr_pointer = 0

    def _next_available_state(self, est_tokens: int) -> Optional[KeyState]:
        n = len(self.states)
        for offset in range(n):
            idx = (self._rr_pointer + offset) % n
            state = self.states[idx]
            if state.has_headroom(est_tokens):
                self._rr_pointer = (idx + 1) % n
                return state
        return None

    def all_daily_exhausted(self) -> bool:
        return all(s.daily_exhausted and time.time() < s.resting_until for s in self.states)

    def status_line(self) -> str:
        parts = []
        for s in self.states:
            tag = "EXHAUSTED" if (s.daily_exhausted and time.time() < s.resting_until) else "OK"
            parts.append(f"key{s.index}:{tag}")
        return " ".join(parts)

    def wait_for_any_key(self, est_tokens: int = 500, poll_interval: float = 2.0, max_wait: float = 120.0) -> Optional[KeyState]:
        waited = 0.0
        while waited < max_wait:
            if self.all_daily_exhausted():
                return None
            state = self._next_available_state(est_tokens)
            if state is not None:
                return state
            time.sleep(poll_interval)
            waited += poll_interval
        return None


class GenerationError(Exception):
    pass


class DailyQuotaExceeded(GenerationError):
    """Raised when ALL keys in the pool are currently daily-token-exhausted."""
    pass


def _extract_wait_seconds(msg: str) -> float:
    m = re.search(r"try again in\s+([\d.]+)m([\d.]+)s", msg)
    if m:
        return float(m.group(1)) * 60 + float(m.group(2))
    m = re.search(r"try again in\s+([\d.]+)s", msg)
    if m:
        return float(m.group(1))
    return 3600.0  # unknown format -> rest this key an hour, be conservative


def call_groq_structured(
    pool: GroqKeyPool,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_retries: int = 4,
    temperature: float = 1.0,
    max_tokens: int = 500,
):
    """
    Calls Groq with JSON mode. Retries malformed JSON on the SAME key,
    hops to a DIFFERENT key on generic rate limits, and benches a key for
    hours (not seconds) on a token-per-day limit while other keys keep going.
    Returns (parsed_dict, key_index_used).
    Raises DailyQuotaExceeded if every key is currently daily-exhausted.
    Raises GenerationError for other exhausted-retry cases.
    """
    last_error = None
    est_tokens = max_tokens + len(system_prompt.split()) + len(user_prompt.split())

    for attempt in range(max_retries):
        state = pool.wait_for_any_key(est_tokens=est_tokens)
        if state is None:
            if pool.all_daily_exhausted():
                raise DailyQuotaExceeded("All keys are currently daily-token-exhausted.")
            last_error = "timed out waiting for an available key"
            continue

        try:
            response = state.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "ticket_generation",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "review": {"type": "string"},
                                "category": {"type": "string", "enum": ["Billing", "Technical", "Account", "Refund", "General"]},
                                "priority": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
                                "department": {"type": "string", "enum": ["Finance", "Technical", "Account", "Refunds", "General Support"]},
                            },
                            "required": ["review", "category", "priority", "department"],
                            "additionalProperties": False,
                        },
                    },
                },
            )
            usage = getattr(response, "usage", None)
            tokens_used = usage.total_tokens if usage else est_tokens
            state.record_usage(tokens_used)

            content = response.choices[0].message.content
            parsed = json.loads(content)
            return parsed, state.index

        except json.JSONDecodeError as e:
            last_error = e
            continue

        except Exception as e:
            last_error = e
            msg = str(e).lower()
            if "tokens per day" in msg or "requests per day" in msg or " tpd" in msg or " rpd" in msg:
                wait_s = _extract_wait_seconds(msg)
                state.daily_exhausted = True
                state.rest(max(wait_s, 300.0))
                print(f"  [key{state.index} daily-exhausted, benched] pool status: {pool.status_line()}")
                continue
            elif "rate" in msg or "429" in msg:
                state.rest(15.0)
                continue
            else:
                time.sleep((2 ** attempt) + random.random())
                continue

    raise GenerationError(f"Failed after {max_retries} retries. Last error: {last_error}")
