"""
Phase 11 - Deterministic Priority Escalation & Safety Layer.
Post-inference safety guardrails:
1. Detects critical severity indicators (total network outages, medical/emergency mentions, repeated billing fraud, unauthorized SIM swap).
2. Overrides model's predicted priority if critical condition is met.
3. Automatically flags ticket for HUMAN_REVIEW if safety escalation triggers.
"""
import re
from typing import Dict, Optional, Tuple

# Patterns indicating critical severity that require immediate human oversight or priority escalation
CRITICAL_PATTERNS = [
    (r"\b(sim\s*swap|unauthorized\s*sim|sim\s*hijack|identity\s*theft)\b", "Security Hazard: Possible unauthorized SIM hijack"),
    (r"\b(medical\s*emergency|hospital|ambulance|emergency\s*call|sos)\b", "Emergency Hazard: Medical or emergency service dependency"),
    (r"\b(complete\s*outage|entire\s*area\s*down|tower\s*collapsed|no\s*signal\s*entire\s*(city|town|colony))\b", "Critical Infrastructure: Major area outage"),
    (r"\b(fraud|fraudulent\s*transaction|unauthorized\s*deduction|hacked)\b", "Financial/Security Hazard: Potential fraudulent activity"),
    (r"\b(police|legal\s*notice|consumer\s*court|fir\s*filed)\b", "Legal/Compliance Hazard: Formal legal or police escalation"),
]


class PriorityEscalator:
    """Deterministic Safety Rule Engine applied after model prediction."""

    def __init__(self):
        self.compiled_rules = [(re.compile(p, re.IGNORECASE), reason) for p, reason in CRITICAL_PATTERNS]

    def evaluate_safety(
        self,
        review_text: str,
        predicted_category: str,
        predicted_priority: str,
        predicted_department: str,
        confidence: float,
        confidence_threshold: float = 0.85,
    ) -> Dict:
        """
        Evaluates predictions against safety guardrails.
        Returns:
            {
                "final_category": str,
                "final_priority": str,
                "final_department": str,
                "routing_status": "AUTO_ROUTED" | "HUMAN_REVIEW",
                "escalated": bool,
                "escalation_reason": Optional[str],
                "confidence_passed": bool
            }
        """
        escalated = False
        escalation_reason = None
        final_priority = predicted_priority

        # 1. Check critical regex patterns
        for pattern, reason in self.compiled_rules:
            if pattern.search(review_text):
                if final_priority != "Critical":
                    final_priority = "Critical"
                    escalated = True
                    escalation_reason = reason
                break

        # 2. Check category/department contradiction or severe mismatches
        if predicted_category == "Refund" and predicted_department == "Technical":
            # Department correction to Refunds or Finance
            predicted_department = "Refunds"

        # 3. Determine routing status
        confidence_passed = (confidence >= confidence_threshold)

        # High severity critical tickets MUST be sent to human review unless confidence is near absolute
        # If safety escalation triggered, ALWAYS route to HUMAN_REVIEW
        if escalated:
            routing_status = "HUMAN_REVIEW"
        elif not confidence_passed:
            routing_status = "HUMAN_REVIEW"
        elif final_priority == "Critical" and confidence < 0.95:
            # Critical tickets require high assurance (0.95+) for auto-route
            routing_status = "HUMAN_REVIEW"
        else:
            routing_status = "AUTO_ROUTED"

        return {
            "final_category": predicted_category,
            "final_priority": final_priority,
            "final_department": predicted_department,
            "routing_status": routing_status,
            "escalated": escalated,
            "escalation_reason": escalation_reason,
            "confidence_passed": confidence_passed,
        }
