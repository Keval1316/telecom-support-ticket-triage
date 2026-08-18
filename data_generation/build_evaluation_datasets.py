"""
Builds the evaluation/demo/sample-upload datasets from master_dataset.csv + test.csv.
Section 16: edge-case dataset, priority stress-test dataset, human-review-simulation
dataset, presentation/demo dataset, and a clean sample CSV-upload example.
"""
import csv
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generation_config import Config

PROCESSED_DIR = Config.REPO_ROOT / "data" / "processed"
SPLITS_DIR = Config.REPO_ROOT / "data" / "splits"
EVAL_DIR = Config.REPO_ROOT / "data" / "evaluation"
DEMO_DIR = Config.REPO_ROOT / "data" / "demo"

STANDARD_FIELDS = ["ticket_id", "customer_name", "contact_number", "review",
                    "timestamp", "category", "priority", "department"]


def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fields})


def main():
    master = load_csv(PROCESSED_DIR / "master_dataset.csv")
    test_rows = load_csv(SPLITS_DIR / "test.csv")
    test_ids = {r["ticket_id"] for r in test_rows}

    test_master = [r for r in master if r["ticket_id"] in test_ids]
    print(f"Test-set rows with full metadata available: {len(test_master)}")

    rng = random.Random(Config.RANDOM_SEED)

    edge_cases = [r for r in test_master if r["difficulty"] in ("hard", "ambiguous")]
    write_csv(EVAL_DIR / "edge_cases.csv", edge_cases, STANDARD_FIELDS)
    print(f"edge_cases.csv: {len(edge_cases)} rows")

    critical = [r for r in test_master if r["priority"] == "Critical"]
    high = [r for r in test_master if r["priority"] == "High"]
    rng.shuffle(high)
    stress_test = critical + high[:max(10, len(critical))]
    write_csv(EVAL_DIR / "priority_stress_test.csv", stress_test, STANDARD_FIELDS)
    print(f"priority_stress_test.csv: {len(stress_test)} rows ({len(critical)} Critical)")

    review_pool = test_master[:]
    rng.shuffle(review_pool)
    review_sim = review_pool[:min(50, len(review_pool))]
    write_csv(EVAL_DIR / "review_queue_examples.csv", review_sim, STANDARD_FIELDS)
    print(f"review_queue_examples.csv: {len(review_sim)} rows")

    demo_pool = [r for r in test_master if r["difficulty"] == "easy"]
    rng.shuffle(demo_pool)
    seen_categories = set()
    demo_rows = []
    for r in demo_pool:
        if r["category"] not in seen_categories or len(demo_rows) < 15:
            demo_rows.append(r)
            seen_categories.add(r["category"])
        if len(demo_rows) >= 15:
            break
    write_csv(DEMO_DIR / "demo_tickets.csv", demo_rows, STANDARD_FIELDS)
    print(f"demo_tickets.csv: {len(demo_rows)} rows")

    upload_pool = demo_rows[:8] if len(demo_rows) >= 8 else demo_pool[:8]
    upload_fields = ["name", "contact_number", "review", "timestamp"]
    upload_rows = [
        {
            "name": r["customer_name"],
            "contact_number": r["contact_number"],
            "review": r["review"],
            "timestamp": r["timestamp"],
        }
        for r in upload_pool
    ]
    write_csv(DEMO_DIR / "sample_upload.csv", upload_rows, upload_fields)
    print(f"sample_upload.csv: {len(upload_rows)} rows (no labels, matches /upload-csv columns)")


if __name__ == "__main__":
    main()
