"""
Targeted top-up generation for underrepresented category/priority/department
combos flagged in reports/dataset_report.md (Section 19: "realistic, not forced"
balancing - only topping up the worst singleton/near-singleton combos, not
forcing full parity across all 37 combos).

Appends directly to the existing data/raw/tickets_{version}.jsonl so the
normal QC pipeline (deduplicate -> validate -> balance -> split ->
build_evaluation_datasets) can simply be re-run afterward on the extended file.

Safe to re-run: has its own separate progress file, independent of the
main generation resume state.
"""
import sys
import json
import random
import string
import datetime
from pathlib import Path
from dataclasses import dataclass
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generation_config import Config
from scenario_plan import SCENARIOS, DIFFICULTY_WEIGHTS
from groq_client import GroqKeyPool, call_groq_structured, GenerationError, DailyQuotaExceeded
from schemas import TicketFields, TicketMetadata, TicketRecord

FIRST_NAMES = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Ananya", "Karan", "Divya",
               "Rahul", "Neha", "Arjun", "Pooja", "Sanjay", "Kavya", "Aditya", "Isha",
               "Manoj", "Ritu", "Suresh", "Meera"]
LAST_NAMES = ["Sharma", "Patel", "Verma", "Gupta", "Nair", "Reddy", "Iyer", "Chauhan",
              "Mehta", "Joshi", "Kapoor", "Desai", "Rao", "Bhat", "Malhotra"]

# (category, priority, department, how_many_to_add) - from reports/dataset_report.md review
TOPUP_TARGETS = [
    ("General", "Low", "Account", 9),
    ("Refund", "Critical", "Finance", 9),
    ("Billing", "Critical", "Refunds", 9),
    ("General", "Medium", "Finance", 9),
    ("General", "Medium", "Refunds", 8),
    ("General", "Low", "Finance", 8),
    ("Account", "Low", "Technical", 6),
    ("Refund", "High", "Finance", 6),
    ("Refund", "Low", "Finance", 7),
]


@dataclass
class TopupItem:
    category: str
    priority: str
    department: str
    scenario: str
    difficulty: str


def _weighted_choice(rng, weights: dict):
    items = list(weights.keys())
    probs = list(weights.values())
    return rng.choices(items, weights=probs, k=1)[0]


def build_topup_plan(seed: int):
    rng = random.Random(seed)
    plan = []
    for category, priority, department, count in TOPUP_TARGETS:
        for _ in range(count):
            scenario = rng.choice(SCENARIOS[category])
            difficulty = _weighted_choice(rng, DIFFICULTY_WEIGHTS)
            plan.append(TopupItem(category, priority, department, scenario, difficulty))
    rng.shuffle(plan)
    return plan


def synthetic_name(rng):
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def synthetic_phone(rng):
    prefix = rng.choice(["98", "99", "97", "96", "70", "80", "90"])
    rest = "".join(rng.choice(string.digits) for _ in range(8))
    return f"+91{prefix}{rest}"


def build_prompt(item: TopupItem):
    system_prompt = (
        "You are generating a SINGLE synthetic customer support ticket for a telecom "
        "company, for training-data purposes only. Output STRICT JSON only, matching "
        "exactly this schema and nothing else: "
        "{\"review\": string, \"category\": string, \"priority\": string, \"department\": string}. "
        "The review field must sound like a real Indian telecom customer wrote it, "
        "natural, sometimes informal or with mild spelling issues, varied tone and length. "
        "Do NOT include the customer name or phone number inside the review text. "
        "Do not repeat sentence templates across tickets. Keep review under 80 words. "
        "Valid categories: Billing, Technical, Account, Refund, General. "
        "Valid priorities: Critical, High, Medium, Low. "
        "Valid departments: Finance, Technical, Account, Refunds, General Support."
    )
    difficulty_instructions = {
        "easy": "Write a clear, straightforward complaint with an obvious category and priority.",
        "medium": "Write a realistic complaint with some ambiguity in tone but a clear underlying issue.",
        "hard": "Write a complaint that mixes in a secondary minor issue or missing context, making classification non-trivial.",
        "ambiguous": "Write a complaint that is somewhat vague or could plausibly fit more than one category, but still leans toward the target category on balance.",
    }
    user_prompt = (
        f"Scenario: {item.scenario} (category: {item.category}).\n"
        f"Target priority: {item.priority} - the complaint tone/urgency/impact should "
        f"realistically justify this priority level.\n"
        f"Target department: {item.department} (this ticket legitimately belongs to this "
        f"department even though it may differ from the most obvious default department "
        f"for this category - that is intentional).\n"
        f"Difficulty: {item.difficulty}. {difficulty_instructions[item.difficulty]}\n"
        "Return the JSON object now."
    )
    return system_prompt, user_prompt


def save_progress(path, next_index, accepted, rejected, batch_id):
    path.write_text(json.dumps({
        "next_index": next_index,
        "accepted": accepted,
        "rejected": rejected,
        "batch_id": batch_id,
    }), encoding="utf-8")


def main():
    Config.validate()
    rng = random.Random(Config.RANDOM_SEED + 999)  # distinct sub-seed from main generation

    plan = build_topup_plan(Config.RANDOM_SEED + 999)
    print(f"Top-up plan built: {len(plan)} items across {len(TOPUP_TARGETS)} target combos")

    pool = GroqKeyPool(
        Config.GROQ_API_KEYS,
        rpm_limit=Config.KEY_RPM_LIMIT,
        tpm_limit=Config.KEY_TPM_LIMIT,
        rpd_limit=Config.KEY_RPD_LIMIT,
    )

    # Append directly to the SAME raw file the main pipeline already produced,
    # so deduplicate.py / validate_generated_data.py just see a slightly larger input.
    out_path = Config.RAW_DIR / f"tickets_{Config.DATASET_VERSION}.jsonl"
    progress_path = Config.MANIFEST_DIR / f"progress_{Config.DATASET_VERSION}_topup.json"

    if not out_path.exists():
        print(f"ERROR: {out_path} not found. Run generate_tickets.py first.", file=sys.stderr)
        sys.exit(1)

    start_index = 0
    accepted, rejected = 0, 0
    batch_id = f"topup_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%S')}"

    if progress_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        start_index = progress["next_index"]
        accepted = progress["accepted"]
        rejected = progress["rejected"]
        batch_id = progress["batch_id"]
        print(f"RESUMING top-up from index {start_index} (already accepted={accepted}, rejected={rejected})")

    with open(out_path, "a", encoding="utf-8") as f:
        for i, item in enumerate(plan[start_index:], start=start_index):
            ticket_id = f"TCK-{Config.DATASET_VERSION}-TOPUP-{i+1:05d}"
            customer_name = synthetic_name(rng)
            contact_number = synthetic_phone(rng)
            timestamp = (
                datetime.datetime.now(datetime.UTC) - datetime.timedelta(
                    days=rng.randint(0, 180), hours=rng.randint(0, 23))
            ).isoformat()

            system_prompt, user_prompt = build_prompt(item)

            try:
                raw, key_idx = call_groq_structured(
                    pool, system_prompt, user_prompt, model=Config.GROQ_MODEL,
                )
            except DailyQuotaExceeded:
                save_progress(progress_path, i, accepted, rejected, batch_id)
                print(f"\nALL KEYS DAILY-EXHAUSTED at item {i+1}/{len(plan)}.")
                print(f"Progress saved. accepted={accepted} rejected={rejected}")
                print("Just re-run this same command later to resume the top-up.")
                sys.exit(0)
            except GenerationError as e:
                print(f"[{i+1}/{len(plan)}] GENERATION FAILED, skipping: {e}")
                rejected += 1
                save_progress(progress_path, i + 1, accepted, rejected, batch_id)
                continue

            try:
                fields = TicketFields(
                    ticket_id=ticket_id,
                    customer_name=customer_name,
                    contact_number=contact_number,
                    review=raw.get("review", ""),
                    timestamp=timestamp,
                    category=raw.get("category", item.category),
                    priority=raw.get("priority", item.priority),
                    department=raw.get("department", item.department),
                )
                metadata = TicketMetadata(
                    generation_batch=batch_id,
                    scenario_type=item.scenario,
                    difficulty=item.difficulty,
                    teacher_model=Config.GROQ_MODEL,
                    generation_timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
                    dataset_version=Config.DATASET_VERSION,
                    key_index=key_idx,
                )
                record = TicketRecord(fields=fields, metadata=metadata)
            except ValidationError as e:
                print(f"[{i+1}/{len(plan)}] VALIDATION FAILED, skipping: {e}")
                rejected += 1
                save_progress(progress_path, i + 1, accepted, rejected, batch_id)
                continue

            f.write(record.model_dump_json() + "\n")
            f.flush()
            accepted += 1
            save_progress(progress_path, i + 1, accepted, rejected, batch_id)
            print(f"[{i+1}/{len(plan)}] {item.category}/{item.priority}/{item.department} "
                  f"accepted={accepted} rejected={rejected}")

    progress_path.unlink(missing_ok=True)
    print(f"\nDONE. accepted={accepted} rejected={rejected}")
    print(f"Appended to: {out_path}")
    print("\nNext: re-run the full QC pipeline in order:")
    print("  python data_generation\\deduplicate.py")
    print("  python data_generation\\validate_generated_data.py")
    print("  python data_generation\\balance_dataset.py")
    print("  python data_generation\\split_dataset.py")
    print("  python data_generation\\build_evaluation_datasets.py")


if __name__ == "__main__":
    main()
