"""
Splits the validated ticket dataset into master dataset, train/validation/test,
and a locked-away future-testing set. Implements leakage prevention (near-duplicate
detection across splits) and stratified splitting (Section 17-19).
"""
import json
import sys
import csv
import random
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generation_config import Config
from deduplicate import normalize, shingles, jaccard

try:
    from sklearn.model_selection import train_test_split
except ImportError:
    print("scikit-learn is required. pip install scikit-learn", file=sys.stderr)
    sys.exit(1)

PROCESSED_DIR = Config.REPO_ROOT / "data" / "processed"
SPLITS_DIR = Config.REPO_ROOT / "data" / "splits"
FUTURE_DIR = Config.REPO_ROOT / "data" / "future_testing"

FUTURE_TEST_FRACTION = 0.10
VAL_FRACTION = 0.15
TEST_FRACTION = 0.15

STANDARD_FIELDS = ["ticket_id", "customer_name", "contact_number", "review",
                    "timestamp", "category", "priority", "department"]


def load_validated():
    in_path = Config.RAW_DIR / f"tickets_{Config.DATASET_VERSION}_validated.jsonl"
    if not in_path.exists():
        print(f"ERROR: {in_path} not found. Run validate_generated_data.py first.", file=sys.stderr)
        sys.exit(1)
    return [json.loads(line) for line in open(in_path, encoding="utf-8") if line.strip()]


def write_csv(path: Path, records: list, fields: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in records:
            writer.writerow({k: r["fields"][k] for k in fields})


def remove_cross_split_duplicates(base_records, other_records, threshold=0.85):
    base_shingles = [shingles(normalize(r["fields"]["review"])) for r in base_records]
    kept, dropped = [], 0
    for r in other_records:
        r_sh = shingles(normalize(r["fields"]["review"]))
        if any(jaccard(r_sh, b_sh) >= threshold for b_sh in base_shingles):
            dropped += 1
        else:
            kept.append(r)
    return kept, dropped


def stratified_split(records, test_size, seed, label_fn):
    labels = [label_fn(r) for r in records]
    label_counts = Counter(labels)
    min_class_count = min(label_counts.values())

    if min_class_count < 2:
        print(f"WARNING: some stratification class has <2 members (min={min_class_count}). "
              f"Falling back to category-only stratification.")
        labels = [r["fields"]["category"] for r in records]

    try:
        train_idx, test_idx = train_test_split(
            range(len(records)), test_size=test_size, random_state=seed, stratify=labels
        )
    except ValueError as e:
        print(f"WARNING: stratified split failed ({e}). Falling back to random split.")
        train_idx, test_idx = train_test_split(
            range(len(records)), test_size=test_size, random_state=seed
        )

    return [records[i] for i in train_idx], [records[i] for i in test_idx]


def main():
    records = load_validated()
    print(f"Loaded {len(records)} validated records")

    rng = random.Random(Config.RANDOM_SEED)
    shuffled = records[:]
    rng.shuffle(shuffled)

    combo_label = lambda r: f"{r['fields']['category']}|{r['fields']['priority']}|{r['fields']['department']}"

    pool, future_test = stratified_split(
        shuffled, test_size=FUTURE_TEST_FRACTION, seed=Config.RANDOM_SEED, label_fn=combo_label
    )
    print(f"Future-test carved out: {len(future_test)} records (locked away)")

    pool, dropped_vs_future = remove_cross_split_duplicates(future_test, pool)
    print(f"Dropped {dropped_vs_future} near-duplicates of future-test from remaining pool")

    train, val_test = stratified_split(
        pool, test_size=(VAL_FRACTION + TEST_FRACTION), seed=Config.RANDOM_SEED, label_fn=combo_label
    )
    val, test = stratified_split(
        val_test, test_size=(TEST_FRACTION / (VAL_FRACTION + TEST_FRACTION)),
        seed=Config.RANDOM_SEED, label_fn=combo_label
    )

    val, dropped_val = remove_cross_split_duplicates(train, val)
    test, dropped_test = remove_cross_split_duplicates(train, test)
    print(f"Dropped {dropped_val} near-duplicates of train from validation")
    print(f"Dropped {dropped_test} near-duplicates of train from test")

    print(f"Final sizes -> train: {len(train)}  validation: {len(val)}  test: {len(test)}  future_test: {len(future_test)}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    master_path = PROCESSED_DIR / "master_dataset.csv"
    all_fields = STANDARD_FIELDS + ["generation_batch", "generation_source", "scenario_type", "difficulty",
                                     "teacher_model", "generation_timestamp", "dataset_version", "key_index"]
    with open(master_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()
        for r in records:
            writer.writerow({**r["fields"], **r["metadata"]})
    print(f"Master dataset written: {master_path} ({len(records)} rows)")

    write_csv(SPLITS_DIR / "train.csv", train, STANDARD_FIELDS)
    write_csv(SPLITS_DIR / "validation.csv", val, STANDARD_FIELDS)
    write_csv(SPLITS_DIR / "test.csv", test, STANDARD_FIELDS)
    write_csv(FUTURE_DIR / "future_test.csv", future_test, STANDARD_FIELDS)

    print(f"Written: {SPLITS_DIR / 'train.csv'}")
    print(f"Written: {SPLITS_DIR / 'validation.csv'}")
    print(f"Written: {SPLITS_DIR / 'test.csv'}")
    print(f"Written: {FUTURE_DIR / 'future_test.csv'} (LOCKED - never use for training/tuning/threshold selection)")


if __name__ == "__main__":
    main()
