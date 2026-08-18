"""
Validates the deduped dataset: re-checks schema, flags suspicious
category/department combinations, checks for contradictory/malformed
records, and writes reports/dataset_report.md.
"""
import json
import sys
from pathlib import Path
from collections import Counter
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generation_config import Config
from schemas import TicketFields
from scenario_plan import DEFAULT_DEPARTMENT, LEGITIMATE_CROSS_DEPARTMENT

REPORTS_DIR = Config.REPO_ROOT / "reports"


def is_legitimate_department(category: str, department: str) -> bool:
    if department == DEFAULT_DEPARTMENT[category]:
        return True
    return department in LEGITIMATE_CROSS_DEPARTMENT.get(category, [])


def main():
    in_path = Config.RAW_DIR / f"tickets_{Config.DATASET_VERSION}_deduped.jsonl"
    if not in_path.exists():
        print(f"ERROR: {in_path} not found. Run deduplicate.py first.", file=sys.stderr)
        sys.exit(1)

    raw_lines = [line for line in open(in_path, encoding="utf-8") if line.strip()]
    print(f"Loaded {len(raw_lines)} records")

    valid_records = []
    malformed = []
    suspicious_combo = []

    for i, line in enumerate(raw_lines):
        try:
            obj = json.loads(line)
            fields = TicketFields(**obj["fields"])
        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            malformed.append({"line": i, "error": str(e)})
            continue

        if not is_legitimate_department(fields.category, fields.department):
            suspicious_combo.append({
                "ticket_id": fields.ticket_id,
                "category": fields.category,
                "department": fields.department,
            })
            # Flagged, not dropped -- kept in dataset but reported for manual review
        valid_records.append(obj)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    cat_counts = Counter(r["fields"]["category"] for r in valid_records)
    pri_counts = Counter(r["fields"]["priority"] for r in valid_records)
    dept_counts = Counter(r["fields"]["department"] for r in valid_records)
    diff_counts = Counter(r["metadata"]["difficulty"] for r in valid_records)

    report_lines = [
        "# Dataset Quality Report",
        "",
        f"- Dataset version: `{Config.DATASET_VERSION}`",
        f"- Total records loaded: {len(raw_lines)}",
        f"- Valid records: {len(valid_records)}",
        f"- Malformed/rejected records: {len(malformed)}",
        f"- Suspicious category/department combos (flagged, kept): {len(suspicious_combo)}",
        "",
        "## Category distribution",
        "",
    ]
    for k, v in cat_counts.items():
        report_lines.append(f"- {k}: {v} ({v/len(valid_records)*100:.1f}%)")

    report_lines += ["", "## Priority distribution", ""]
    for k, v in pri_counts.items():
        report_lines.append(f"- {k}: {v} ({v/len(valid_records)*100:.1f}%)")

    report_lines += ["", "## Department distribution", ""]
    for k, v in dept_counts.items():
        report_lines.append(f"- {k}: {v} ({v/len(valid_records)*100:.1f}%)")

    report_lines += ["", "## Difficulty distribution", ""]
    for k, v in diff_counts.items():
        report_lines.append(f"- {k}: {v} ({v/len(valid_records)*100:.1f}%)")

    if suspicious_combo:
        report_lines += ["", "## Suspicious category/department combos (first 20)", ""]
        for s in suspicious_combo[:20]:
            report_lines.append(f"- {s['ticket_id']}: {s['category']} -> {s['department']}")

    if malformed:
        report_lines += ["", "## Malformed records (first 20)", ""]
        for m in malformed[:20]:
            report_lines.append(f"- line {m['line']}: {m['error'][:150]}")

    report_path = REPORTS_DIR / "dataset_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    out_path = Config.RAW_DIR / f"tickets_{Config.DATASET_VERSION}_validated.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in valid_records:
            f.write(json.dumps(r) + "\n")

    print(f"Valid: {len(valid_records)}  Malformed: {len(malformed)}  Suspicious: {len(suspicious_combo)}")
    print(f"Report: {report_path}")
    print(f"Validated dataset: {out_path}")


if __name__ == "__main__":
    main()
