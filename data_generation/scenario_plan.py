"""
Defines the scenario space (category x priority x department x scenario x difficulty)
and builds a controlled generation plan instead of one giant prompt (Section 20-31).
"""
import random
from dataclasses import dataclass
from typing import List

CATEGORIES = ["Billing", "Technical", "Account", "Refund", "General"]
PRIORITIES = ["Critical", "High", "Medium", "Low"]
DEPARTMENTS = ["Finance", "Technical", "Account", "Refunds", "General Support"]
DIFFICULTIES = ["easy", "medium", "hard", "ambiguous"]

DEFAULT_DEPARTMENT = {
    "Billing": "Finance",
    "Technical": "Technical",
    "Account": "Account",
    "Refund": "Refunds",
    "General": "General Support",
}

LEGITIMATE_CROSS_DEPARTMENT = {
    "Billing": ["Refunds"],
    "Refund": ["Finance"],
    "Account": ["Technical"],
    "General": ["Finance", "Technical", "Account", "Refunds"],
}

SCENARIOS = {
    "Billing": [
        "incorrect charges on bill", "unexpected bill amount", "duplicate billing",
        "payment deducted but not reflected", "recharge payment issue",
        "incorrect plan charge", "billing mismatch between plan and invoice",
    ],
    "Technical": [
        "network unavailable in area", "poor signal strength", "mobile data not working",
        "slow internet speed", "calls dropping repeatedly", "SMS not sending or receiving",
        "SIM card or network registration issue", "repeated service failures",
    ],
    "Account": [
        "unable to log into account", "account locked after failed attempts",
        "cannot access account portal", "profile information incorrect",
        "SIM ownership or transfer issue", "need to update registered info",
    ],
    "Refund": [
        "refund requested but still pending", "refund not received after cancellation",
        "failed transaction needs refund", "recharge refund request",
        "payment reversal not processed",
    ],
    "General": [
        "asking about plan details", "asking about recharge options",
        "general service question", "non-urgent query about offers",
    ],
}

PRIORITY_WEIGHTS = {
    "Billing":   {"Critical": 0.05, "High": 0.25, "Medium": 0.45, "Low": 0.25},
    "Technical": {"Critical": 0.15, "High": 0.35, "Medium": 0.35, "Low": 0.15},
    "Account":   {"Critical": 0.10, "High": 0.30, "Medium": 0.40, "Low": 0.20},
    "Refund":    {"Critical": 0.05, "High": 0.30, "Medium": 0.45, "Low": 0.20},
    "General":   {"Critical": 0.00, "High": 0.05, "Medium": 0.30, "Low": 0.65},
}

CATEGORY_WEIGHTS = {
    "Billing": 0.25, "Technical": 0.30, "Account": 0.18, "Refund": 0.15, "General": 0.12,
}

DIFFICULTY_WEIGHTS = {"easy": 0.35, "medium": 0.35, "hard": 0.20, "ambiguous": 0.10}

CROSS_DEPARTMENT_RATE = 0.08


@dataclass
class ScenarioItem:
    category: str
    priority: str
    department: str
    scenario: str
    difficulty: str


def _weighted_choice(rng: random.Random, weights: dict):
    items = list(weights.keys())
    probs = list(weights.values())
    return rng.choices(items, weights=probs, k=1)[0]


def build_scenario_plan(target_size: int, seed: int) -> List[ScenarioItem]:
    rng = random.Random(seed)
    plan: List[ScenarioItem] = []
    for _ in range(target_size):
        category = _weighted_choice(rng, CATEGORY_WEIGHTS)
        priority = _weighted_choice(rng, PRIORITY_WEIGHTS[category])
        scenario = rng.choice(SCENARIOS[category])
        difficulty = _weighted_choice(rng, DIFFICULTY_WEIGHTS)

        if rng.random() < CROSS_DEPARTMENT_RATE and category in LEGITIMATE_CROSS_DEPARTMENT:
            department = rng.choice(LEGITIMATE_CROSS_DEPARTMENT[category])
        else:
            department = DEFAULT_DEPARTMENT[category]

        plan.append(ScenarioItem(category, priority, department, scenario, difficulty))
    rng.shuffle(plan)
    return plan


def plan_summary(plan: List[ScenarioItem]) -> dict:
    from collections import Counter
    return {
        "total": len(plan),
        "by_category": dict(Counter(p.category for p in plan)),
        "by_priority": dict(Counter(p.priority for p in plan)),
        "by_department": dict(Counter(p.department for p in plan)),
        "by_difficulty": dict(Counter(p.difficulty for p in plan)),
    }


if __name__ == "__main__":
    plan = build_scenario_plan(2000, 42)
    import json
    print(json.dumps(plan_summary(plan), indent=2))
