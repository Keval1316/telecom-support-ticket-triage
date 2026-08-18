"""
Near-duplicate detection on the review text field.
Uses word-shingle Jaccard similarity - catches paraphrase-level duplicates,
not just exact string matches.
"""
import json
import sys
from pathlib import Path
from itertools import combinations

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generation_config import Config

SIMILARITY_THRESHOLD = 0.85
SHINGLE_SIZE = 3


def normalize(text: str) -> list:
    words = "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text).split()
    return words


def shingles(words: list, n: int = SHINGLE_SIZE) -> set:
    if len(words) < n:
        return {" ".join(words)}
    return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def find_duplicates(records: list) -> set:
    """Returns a set of indices (into records) that should be DROPPED as duplicates."""
    shingle_sets = [shingles(normalize(r["fields"]["review"])) for r in records]

    # Bucket by category to avoid an O(n^2) scan across the whole dataset
    buckets = {}
    for i, r in enumerate(records):
        buckets.setdefault(r["fields"]["category"], []).append(i)

    to_drop = set()
    for cat, idxs in buckets.items():
        for i, j in combinations(idxs, 2):
            if i in to_drop or j in to_drop:
                continue
            sim = jaccard(shingle_sets[i], shingle_sets[j])
            if sim >= SIMILARITY_THRESHOLD:
                to_drop.add(j)  # keep the first occurrence, drop the later one
    return to_drop


def main():
    in_path = Config.RAW_DIR / f"tickets_{Config.DATASET_VERSION}.jsonl"
    if not in_path.exists():
        print(f"ERROR: {in_path} not found. Run generate_tickets.py first.", file=sys.stderr)
        sys.exit(1)

    records = [json.loads(line) for line in open(in_path, encoding="utf-8") if line.strip()]
    print(f"Loaded {len(records)} records")

    to_drop = find_duplicates(records)
    print(f"Near-duplicates found: {len(to_drop)} ({len(to_drop)/len(records)*100:.1f}%)")

    kept = [r for i, r in enumerate(records) if i not in to_drop]
    out_path = Config.RAW_DIR / f"tickets_{Config.DATASET_VERSION}_deduped.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r) + "\n")

    print(f"Kept {len(kept)} records -> {out_path}")


if __name__ == "__main__":
    main()
