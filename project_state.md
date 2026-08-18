# Project State — Telecom Ticket Triage

## Meta
- Last updated: 2026-08-18
- Current phase: Phase 3 (Groq Synthetic Data Factory) — IN PROGRESS, blocked on Groq daily quota
- Completed phases: [0, 1, 2]
- Phase 3: code complete and working; data generation ~60% done, paused for quota reset
- Frontend stack: React + Vite + Tailwind + Framer Motion + Recharts
- Base model: Qwen2.5-3B
- Fine-tuning method: QLoRA (4-bit)

## Key decisions locked in
- GPU: NVIDIA RTX 2050, 4GB VRAM confirmed (driver caps at CUDA 11.7) — too tight for local training.
- Training location: GOOGLE COLAB (free T4, 16GB VRAM) — locked in, not a fallback. Local machine needs NO torch/CUDA/bitsandbytes.
- requirements.txt = local-only (CPU: groq, fastapi, pandas, sklearn, etc). training/requirements-colab.txt = training-only (torch, transformers, peft, bitsandbytes, trl, datasets, accelerate) — installed inside Colab in Phase 8, not locally.
- Groq: 3 separate Groq ACCOUNTS/signups (not 3 keys under 1 account) — confirmed genuinely independent daily quotas. GROQ_API_KEYS comma-separated in .env.
- GROQ_MODEL = openai/gpt-oss-120b (verified current/featured model as of Aug 2026; cheap, fast, JSON-mode capable).
- Groq response_format MUST be "json_schema" with strict:true, NOT the older "json_object" mode — gpt-oss-120b on Groq has a known bug where json_object mode intermittently fails validation (json_validate_failed with empty failed_generation). json_schema + strict:true uses constrained decoding and fixed this completely.
- Do NOT use the `reasoning_effort` param — not supported by the installed groq==0.9.0 SDK version, causes TypeError. Removed from groq_client.py.
- Groq SDK client instantiated with `max_retries=0` (Groq(api_key=key, max_retries=0)) so the SDK doesn't do its own internal blocking retry/sleep — our own GroqKeyPool handles all retry/backoff/key-rotation logic instead.
- Rate limit reality check: Groq's "tokens per day" (TPD) limit is enforced at the ORGANIZATION level (confirmed via error message showing org_id), not per-key. With 3 separate accounts this is fine (each account = its own org = its own TPD pool). If ever using multiple keys from ONE account, rotation would NOT help against TPD limits (only against RPM/RPD).
- Raw generation output format: JSONL first (data/raw/tickets_v1.0.jsonl), converted to CSV only after Phase 4 validation (matches Section 59 folder layout: raw/ vs processed/ vs splits/). User explicitly confirmed this choice over generating CSV directly.
- generate_tickets.py has RESUME support: tracks progress in data/manifests/progress_{version}.json (next_index, accepted, rejected, batch_id), safe to re-run same command anytime, auto-continues from where it left off. On EVERY key simultaneously daily-exhausted, script saves progress and exits cleanly (exit code 0) rather than hanging — safe to just re-run later.
- REJECTED a "merge in other-AI-generated data" shortcut on 2026-08-18: user found/considered a 2000-row file (telecom_tickets_2026-08-18.jsonl) but investigation showed it was only 48 unique review texts templated/repeated ~42x each via a rule-based generator (metadata: generation_source="web-generator", teacher_model="rule-based-classifier" — i.e., NOT real LLM output). Correctly rejected per Section 10 ("no repetitive templates") and Section 66 ("no fake logic"). Decision made: wait ~24h for genuine Groq quota reset and resume real generation rather than compromise data quality. Do NOT reconsider merging that file or similar templated data.
- Confidence threshold: not yet finalized — selected in Phase 10 (range 0.70-0.90).
- Database: SQLite for dev, Postgres-portable schema.
- Runtime cost target: ₹0 — Groq is offline-only, never a runtime dependency.
- Workflow note: user runs all commands themselves in their own PowerShell terminal (Windows, not WSL). Claude provides copy-pasteable PowerShell blocks (heredoc-style `@'...'@ | Out-File -FilePath ... -Encoding utf8` for multi-line files) rather than executing bash directly for this project's actual build steps. Claude's own sandbox was only used in Phase 1 to scaffold+zip the initial repo.

## Repo state (as of last commit)
- Full Section 59 folder layout in place (data/, data_generation/, training/, models/, backend/app/*, frontend/src/*, reports/, notebooks/, scripts/).
- Local venv (.venv) created, Python 3.12.5, Windows 11. requirements.txt installed and verified clean via scripts/local_env_check.py.
- .env populated with real GROQ_API_KEYS (3 keys, 3 separate accounts), GROQ_MODEL=openai/gpt-oss-120b, DATASET_VERSION=v1.0 (confirmed reverted from an abandoned v1.1 attempt).
- Files created and working in data_generation/:
  - schemas.py — Pydantic TicketFields/TicketMetadata/TicketRecord models
  - generation_config.py — .env-driven Config class, validated working (3 keys loaded)
  - scenario_plan.py — category/priority/department/scenario/difficulty weighted scenario plan builder, validated working (2000-item plan, realistic distribution)
  - groq_client.py — GroqKeyPool with per-key RPM/TPM/RPD tracking, round-robin rotation, TPD-exhaustion detection (benches a key for hours not seconds on "tokens per day" errors, raises DailyQuotaExceeded only when ALL keys are simultaneously exhausted), json_schema strict-mode structured output (FIXED from earlier json_object bug), max_retries=0 on the Groq SDK client itself
  - generate_tickets.py — main generation script with full resume support via progress_{version}.json, working correctly
  - deduplicate.py, validate_generated_data.py, balance_dataset.py — WRITTEN, not yet run (waiting on full dataset)
  - split_dataset.py, build_evaluation_datasets.py — WRITTEN, not yet run (Phase 5 prep, done early)
- scripts/local_env_check.py, scripts/rebuild_progress.py, scripts/diagnose_v1_dataset.py also created (utility/debug scripts used during Phase 3 troubleshooting).
- Git: commits made through Phase 2. Phase 3 code changes (all files above) are STAGED TO COMMIT — run `git add -A && git commit -m "Phase 3: Groq data generation pipeline complete"` if not already done before starting a new session.
- Datasets generated so far: data/raw/tickets_v1.0.jsonl — approx 1200+ REAL, unique, Groq-generated tickets (exact count unknown until generation resumes and finishes; was deduped once already to remove 13 exact-duplicate rows from an early pre-resume-logic restart, 2 minor index gaps at 980/981 accepted as negligible). This file is real data, keep it, do NOT delete.
- data/manifests/progress_v1.0.json exists and tracks the exact resume point — needed to continue generation. Do NOT delete this file.
- Model artifacts: none yet.

## Environment notes
- GPU available locally: yes, RTX 2050 4GB, but NOT used for training (Colab instead, confirmed).
- Groq accounts: 3 separate signups, all currently daily-quota-exhausted as of 2026-08-18 (hit ~1200/2000 tickets). Expected to reset ~24h from when each account was first exhausted (Groq resets appear to roll on a per-account basis, timing not perfectly synced across all 3 — script handles this fine automatically via per-key benching).
- Sandbox note: Claude's own sandbox has no Groq/HuggingFace network access; all real generation runs in the user's own PowerShell terminal.

## Open issues / blockers
- BLOCKED: waiting ~24h for Groq daily token quota to reset across the 3 accounts before generation can resume to completion (2000 target).
- Once generation finishes, the following pipeline must run IN THIS EXACT ORDER (none run yet):
  1. `python data_generation\deduplicate.py`
  2. `python data_generation\validate_generated_data.py`
  3. `python data_generation\balance_dataset.py`
  4. `python data_generation\split_dataset.py`
  5. `python data_generation\build_evaluation_datasets.py`
  - After these run, review `reports\dataset_report.md` together before moving to Phase 6 — check for severe imbalance (>10x ratio flagged automatically) or a high suspicious-combo/malformed count that might need a top-up generation run first.

## Next action
1. User waits for Groq quota reset (~24h from exhaustion on 2026-08-18), then re-runs `python data_generation\generate_tickets.py` (no config changes needed, auto-resumes).
2. Once `DONE. accepted=... rejected=...` prints (target ~2000), run the 5-step QC/split pipeline listed above in order.
3. Paste `reports\dataset_report.md` contents back to Claude for review before proceeding to Phase 6 (base model download).
4. Commit Phase 3 work to git if not already done.