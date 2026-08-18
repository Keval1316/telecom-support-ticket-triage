"""
Main synthetic data generation script (Section 73 - reusable & configurable).
Usage: python data_generation\generate_tickets.py
Safe to re-run: automatically resumes from where it left off if interrupted
or stopped by a daily quota limit.
"""
import sys
import json
import random
import string
import datetime
from pathlib import Path
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generation_config import Config
from scenario_plan import build_scenario_plan, plan_summary
from groq_client import GroqKeyPool, call_groq_structured, GenerationError, DailyQuotaExceeded
from schemas import TicketFields, TicketMetadata, TicketRecord

FIRST_NAMES = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Ananya", "Karan", "Divya",
               "Rahul", "Neha", "Arjun", "Pooja", "Sanjay", "Kavya", "Aditya", "Isha",
               "Manoj", "Ritu", "Suresh", "Meera"]
LAST_NAMES = ["Sharma", "Patel", "Verma", "Gupta", "Nair", "Reddy", "Iyer", "Chauhan",
              "Mehta", "Joshi", "Kapoor", "Desai", "Rao", "Bhat", "Malhotra"]


def synthetic_name(rng):
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def synthetic_phone(rng):
    prefix = rng.choice(["98", "99", "97", "96", "70", "80", "90"])
    rest = "".join(rng.choice(string.digits) for _ in range(8))
    return f"+91{prefix}{rest}"


def build_prompt(item, timestamp):
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
        f"Target department: {item.department}.\n"
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
    rng = random.Random(Config.RANDOM_SEED)

    Config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    Config.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    pool = GroqKeyPool(
        Config.GROQ_API_KEYS,
        rpm_limit=Config.KEY_RPM_LIMIT,
        tpm_limit=Config.KEY_TPM_LIMIT,
        rpd_limit=Config.KEY_RPD_LIMIT,
    )

    plan = build_scenario_plan(Config.TARGET_DATASET_SIZE, Config.RANDOM_SEED)
    print(f"Scenario plan built: {len(plan)} items")

    out_path = Config.RAW_DIR / f"tickets_{Config.DATASET_VERSION}.jsonl"
    progress_path = Config.MANIFEST_DIR / f"progress_{Config.DATASET_VERSION}.json"

    start_index = 0
    accepted, rejected = 0, 0
    batch_id = f"batch_{datetime.datetime.now(datetime.UTC).strftime(chr(37)+chr(89)+chr(37)+chr(109)+chr(37)+chr(100)+chr(84)+chr(37)+chr(72)+chr(37)+chr(77)+chr(37)+chr(83))}"
    file_mode = "w"

    if progress_path.exists() and out_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        start_index = progress["next_index"]
        accepted = progress["accepted"]
        rejected = progress["rejected"]
        batch_id = progress["batch_id"]
        file_mode = "a"
        print(f"RESUMING from index {start_index} (already accepted={accepted}, rejected={rejected})")
    elif out_path.exists() and not progress_path.exists():
        print(f"ERROR: {out_path} exists but no progress file found. Delete both files "
              f"manually to start fresh, or bump DATASET_VERSION in .env.", file=sys.stderr)
        sys.exit(1)

    with open(out_path, file_mode, encoding="utf-8") as f:
        for i, item in enumerate(plan[start_index:], start=start_index):
            ticket_id = f"TCK-{Config.DATASET_VERSION}-{i+1:05d}"
            customer_name = synthetic_name(rng)
            contact_number = synthetic_phone(rng)
            timestamp = (
                datetime.datetime.now(datetime.UTC) - datetime.timedelta(
                    days=rng.randint(0, 180), hours=rng.randint(0, 23))
            ).isoformat()

            system_prompt, user_prompt = build_prompt(item, timestamp)

            try:
                raw, key_idx = call_groq_structured(
                    pool, system_prompt, user_prompt, model=Config.GROQ_MODEL,
                )
            except DailyQuotaExceeded:
                save_progress(progress_path, i, accepted, rejected, batch_id)
                print(f"\nALL KEYS DAILY-EXHAUSTED at item {i+1}/{len(plan)}.")
                print(f"Progress saved. accepted={accepted} rejected={rejected}")
                print("Just re-run this same command later (quota resets ~daily) to resume.")
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

            if (i + 1) % 25 == 0:
                print(f"[{i+1}/{len(plan)}] accepted={accepted} rejected={rejected} | {pool.status_line()}")

    manifest = {
        "dataset_version": Config.DATASET_VERSION,
        "batch_id": batch_id,
        "teacher_model": Config.GROQ_MODEL,
        "seed": Config.RANDOM_SEED,
        "target_size": Config.TARGET_DATASET_SIZE,
        "accepted": accepted,
        "rejected": rejected,
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "output_file": str(out_path.relative_to(Config.REPO_ROOT)),
        "num_keys_used": len(Config.GROQ_API_KEYS),
    }
    manifest_path = Config.MANIFEST_DIR / f"generation_manifest_{Config.DATASET_VERSION}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    progress_path.unlink(missing_ok=True)

    print(f"\nDONE. accepted={accepted} rejected={rejected}")
    print(f"Output: {out_path}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
