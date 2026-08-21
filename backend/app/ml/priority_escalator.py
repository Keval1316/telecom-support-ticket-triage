"""
Phase 11 - Deterministic Priority Escalation & Safety Layer.
Post-inference safety guardrails:
1. Detects CRITICAL severity: medical emergencies, SIM/identity fraud, complete outages, financial fraud, legal action.
2. Detects HIGH severity: service suspension, double-charges, multi-day outages, call failures, refund delays.
3. Overrides model's predicted priority when safety conditions are met.
4. Automatically flags ticket for HUMAN_REVIEW on any escalation.
"""
import re
from typing import Dict, Optional

# ── CRITICAL escalation patterns ───────────────────────────────────────────────
# Match → Priority = Critical, escalated = True, routing = HUMAN_REVIEW
CRITICAL_PATTERNS = [
    # Medical / Life-safety dependency
    (
        r"\b(medical\s*emergency|hospital|ambulance|emergency\s*(call|service|contact|number)|"
        r"sos|life\s*support|oxygen\s*support|emergency|life.threatening|"
        r"call\s*(\d+\s*)?ambulance|need\s*(a\s*)?doctor|critical\s*patient)\b",
        "Emergency Hazard: Medical or life-safety service dependency",
    ),
    # SIM/Identity takeover
    (
        r"\b(sim\s*swap|sim\s*hijack|sim\s*clon(ing|ed)|unauthorized\s*sim|identity\s*theft|"
        r"account\s*hijack|someone\s*(else\s*)?(is\s*)?(using|accessing)\s*my\s*(number|account|sim)|"
        r"otp\s*(going|coming|received)\s*(to|on|by)\s*(someone|another|different|old|unknown|"
        r"other)\s*(person|number|device))\b",
        "Security Hazard: Unauthorized SIM/identity takeover attempt",
    ),
    # Financial fraud / unauthorized transactions
    (
        r"\b(fraud(ulent)?(\s*(transaction|charge|deduction|activity))?|"
        r"unauthorized\s*(deduction|charge|payment|transfer|transaction)|"
        r"money\s*(stolen|missing|disappeared|gone\s*missing)|hacked|"
        r"account\s*(compromised|breached|taken\s*over)|"
        r"(never|did\s*not|didn[''t]+)\s*(make|initiate|authorize|request)\s*(this|that|any|a)\s*"
        r"(transaction|payment|transfer|charge|purchase|request))\b",
        "Financial/Security Hazard: Suspected unauthorized transaction or account breach",
    ),
    # Major infrastructure / area outage
    (
        r"\b(complete\s*(network\s*)?(outage|failure|blackout|shutdown)|"
        r"entire\s*(area|city|town|colony|sector|building|floor|complex|zone)\s*(is\s*)?(down|dead|out|without\s*(network|internet|signal))|"
        r"tower\s*(collapsed|down|failed|not\s*working|dead)|"
        r"broadband\s*(completely|totally|fully|absolutely)\s*(dead|down|gone|failed|not\s*(working|responding))|"
        r"(whole|entire|complete)\s*(building|apartment|society|area|sector)\s*(has\s*)?"
        r"(no|lost|without)\s*(internet|signal|connectivity|service))\b",
        "Critical Infrastructure: Complete area or major infrastructure outage",
    ),
    # Legal / regulatory escalation
    (
        r"\b(police|fir\s*(filed|lodge)|file\s*(a\s*)?(police\s*)?complaint|"
        r"legal\s*(notice|action|case|proceedings)|consumer\s*(court|forum|protection)|"
        r"trai\s*complaint|nclt|court\s*(case|order)|lawyer|attorney|"
        r"going\s*to\s*(court|sue|file\s*a\s*case))\b",
        "Legal/Compliance Hazard: Formal legal or regulatory escalation",
    ),
]

# ── HIGH-PRIORITY boost patterns ───────────────────────────────────────────────
# Match → Priority set to High (if currently Medium or Low); escalated stays False
HIGH_PRIORITY_PATTERNS = [
    # Service suspended or cut off (handles "service has been suspended", "connection is disconnected", etc.)
    r"\b(service\s*(has\s*been\s*)?(suspended|cut\s*off|disconnected|blocked|terminated|stopped)|"
    r"(connection|account|number|line)\s*(has\s*been\s*)?(suspended|cut|blocked|disconnected|terminated)|"
    r"(postpaid|prepaid|broadband|internet|mobile)\s*(service\s*)?(has\s*been\s*)?(suspended|disconnected|blocked|cut\s*off)|"
    r"suspended\s*(without|despite|even\s*though|since))\b",

    # Double billing / duplicate charge
    r"\b(deducted?\s*twice|charged\s*twice|double\s*(charge|deduction|billing|payment)|"
    r"duplicate\s*(charge|payment|deduction|transaction)|"
    r"amount\s*(deducted|charged)\s*(twice|two\s*times|double|again)|"
    r"(same|extra)\s*amount\s*(deducted|charged)\s*(twice|again|twice))\b",

    # Multi-day service failure
    r"\b(since\s*(\d+\s*)?(days?|hours?)|for\s*(the\s*)?(\w+\s*)?(past\s+)?(\d+\s*)?(days?|hours?)|"
    r"past\s*(\d+\s*)?(days?|hours?)|last\s*(\d+\s*)?(days?|hours?)|"
    r"(2|3|4|5|6|7|two|three|four|five|six|seven)\s*days?\s*(back|ago|since|now)|"
    r"(not\s*working|down|dead|failed)\s*since\s*(yesterday|last\s*(night|evening|morning|week)))\b",

    # Complete call/SMS failure
    r"\b(no\s*(incoming|outgoing)\s*(calls?|sms|messages?)|"
    r"calls?\s*(dropping|dropped|failing|failed|not\s*connecting|not\s*going\s*through)|"
    r"unable\s*to\s*(make|receive|place|answer)\s*(any\s*)?calls?|"
    r"(can[''t]+|cannot)\s*(call|receive\s*calls?|make\s*calls?))\b",

    # Delayed / missing refund
    r"\b(refund\s*(not|never)\s*(received|credited|processed|done|arrived)|"
    r"refund\s*(pending|delayed|overdue|stuck|held|not\s*credited)|"
    r"waiting\s*(for\s*)?(a\s*)?refund|refund\s*(after|since)\s*\d+\s*(days?|weeks?)|"
    r"(still|yet)\s*(no|haven[''t]+\s*(received|got))\s*refund)\b",

    # Suspicious account access
    r"\b(suspicious\s*(activity|login|access|transaction)|"
    r"unknown\s*(device|login|access|transaction|charge)|"
    r"password\s*(changed|reset)\s*without\s*(my|authorization|permission)|"
    r"(someone\s*)?(else\s*)?logged\s*(in|into)\s*my\s*account)\b",

    # Work / business critical impact
    r"\b(affecting\s*(my\s*)?(work|business|office|clients?|customers?)|"
    r"losing\s*(business|clients?|customers?|money)|"
    r"(work|business|office)\s*(is\s*)?(affected|impacted|disrupted|stopped)|"
    r"can[''t]+\s*(work|do\s*my\s*job|run\s*(my\s*)?business))\b",
]

# Compile once at module level for performance
_CRITICAL_COMPILED = [
    (re.compile(p, re.IGNORECASE | re.DOTALL), reason)
    for p, reason in CRITICAL_PATTERNS
]
_HIGH_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in HIGH_PRIORITY_PATTERNS]

_PRIORITY_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


class PriorityEscalator:
    """Deterministic Safety Rule Engine applied after model prediction."""

    def __init__(self):
        self.critical_rules = _CRITICAL_COMPILED
        self.high_rules = _HIGH_COMPILED

    def evaluate_safety(
        self,
        review_text: str,
        predicted_category: str,
        predicted_priority: str,
        predicted_department: str,
        confidence: float,
        confidence_threshold: float = 0.70,
    ) -> Dict:
        """
        Evaluates predictions against safety guardrails.
        Returns final_category, final_priority, final_department, routing_status,
        escalated flag, escalation_reason, and confidence_passed.
        """
        escalated = False
        escalation_reason = None
        final_priority = predicted_priority
        final_category = predicted_category
        final_department = predicted_department

        # ── 1. Check CRITICAL patterns ────────────────────────────────────
        for pattern, reason in self.critical_rules:
            if pattern.search(review_text):
                escalated = True
                escalation_reason = reason
                final_priority = "Critical"
                break  # First critical trigger is sufficient

        # ── 2. Check HIGH-PRIORITY patterns (skip if already Critical) ────
        if not escalated:
            for pattern in self.high_rules:
                if pattern.search(review_text):
                    # Only upgrade; never downgrade
                    if _PRIORITY_RANK.get(final_priority, 0) < _PRIORITY_RANK["High"]:
                        final_priority = "High"
                    break

        # ── 3. Auto-correct category/department mismatches ────────────────
        if final_category == "Refund" and final_department in ("Technical", "General Support"):
            final_department = "Refunds"
        if final_category == "Billing" and final_department == "General Support":
            final_department = "Finance"
        if final_category == "Technical" and final_department == "Finance":
            final_department = "Technical"
        if final_category == "Account" and final_department in ("Finance", "General Support"):
            final_department = "Account"

        # ── 4. Determine routing status ───────────────────────────────────
        confidence_passed = confidence >= confidence_threshold

        if escalated:
            # Safety-escalated tickets ALWAYS go to human oversight
            routing_status = "HUMAN_REVIEW"
        elif not confidence_passed:
            routing_status = "HUMAN_REVIEW"
        elif final_priority == "Critical" and confidence < 0.90:
            routing_status = "HUMAN_REVIEW"
        else:
            routing_status = "AUTO_ROUTED"

        return {
            "final_category": final_category,
            "final_priority": final_priority,
            "final_department": final_department,
            "routing_status": routing_status,
            "escalated": escalated,
            "escalation_reason": escalation_reason,
            "confidence_passed": confidence_passed,
        }
