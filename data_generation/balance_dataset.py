"""
Analyzes class balance across category x priority x department combinations
and appends a balance section to reports/dataset_report.md.
Balance should be realistic, not forced (Section 19).
"""
import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generation_config import Config

REPORTS_DIR = Config.REPO_ROOT / "reports"


def main():
    in_path = Config.RAW_DIR / f"tickets_{Config.DATASET_VERSION}_validated.jsonl"
    if not in_path.exists():
        print(f"ERROR: {in_path} not found. Run validate_generated_data.py first.", file=sys.stderr)
        sys.exit(1)

    records = [json.loads(line) for line in open(in_path, encoding="utf-8") if line.strip()]
    print(f"Loaded {len(records)} validated records")

    combo_counts = Counter(
        (r["fields"]["category"], r["fields"]["priority"], r["fields"]["department"])
        for r in records
    )

    min_count = min(combo_counts.values())
    max_count = max(combo_counts.values())
    imbalance_ratio = max_count / min_count if min_count > 0 else float("inf")

    lines = [
        "",
        "## Balance analysis (category x priority x department)",
        "",
        f"- Unique combinations present: {len(combo_counts)}",
        f"- Smallest combo count: {min_count}",
        f"- Largest combo count: {max_count}",
        f"- Imbalance ratio (max/min): {imbalance_ratio:.1f}x",
        "",
        "| Category | Priority | Department | Count |",
        "|---|---|---|---|",
    ]
    for (cat, pri, dept), count in sorted(combo_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat} | {pri} | {dept} | {count} |")

    report_path = REPORTS_DIR / "dataset_report.md"
    with open(report_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Balance report appended to {report_path}")
    if imbalance_ratio > 10:
        print("WARNING: severe imbalance detected (>10x) - consider regenerating underrepresented combos.")


if __name__ == "__main__":
    main()
