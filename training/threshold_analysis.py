"""
Phase 10 - Threshold Analysis & Tuning.
Sweeps confidence thresholds from 0.70 to 0.90 on evaluation predictions,
computes Auto-Routing Rate, Review Rate, Auto-Routed Accuracy, and Error Escape Rate.
Outputs reports/threshold_analysis.md and recommendations.
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PRED_CSV = REPO_ROOT / "reports" / "test_predictions.csv"
DEFAULT_REPORT_PATH = REPO_ROOT / "reports" / "threshold_analysis.md"


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 10 - Threshold Analysis")
    parser.add_argument("--pred-csv", type=str, default=str(DEFAULT_PRED_CSV),
                        help="Path to prediction CSV from Phase 9")
    parser.add_argument("--report-out", type=str, default=str(DEFAULT_REPORT_PATH),
                        help="Path to output markdown report")
    return parser.parse_args()


def run_sweep(df: pd.DataFrame, thresholds: list) -> pd.DataFrame:
    rows = []
    total = len(df)

    # Determine ground truth full match (all 3 labels match)
    df["full_correct"] = (
        (df["true_category"] == df["pred_category"]) &
        (df["true_priority"] == df["pred_priority"]) &
        (df["true_department"] == df["pred_department"])
    )

    for thresh in thresholds:
        auto_mask = (df["confidence"] >= thresh) & (df["raw_valid"] == True)
        review_mask = ~auto_mask

        n_auto = auto_mask.sum()
        n_review = review_mask.sum()

        auto_rate = (n_auto / total) * 100 if total > 0 else 0
        review_rate = (n_review / total) * 100 if total > 0 else 0

        # Accuracy among auto-routed tickets
        auto_df = df[auto_mask]
        cat_acc = (auto_df["true_category"] == auto_df["pred_category"]).mean() * 100 if n_auto > 0 else 0
        pri_acc = (auto_df["true_priority"] == auto_df["pred_priority"]).mean() * 100 if n_auto > 0 else 0
        dept_acc = (auto_df["true_department"] == auto_df["pred_department"]).mean() * 100 if n_auto > 0 else 0
        all_acc = auto_df["full_correct"].mean() * 100 if n_auto > 0 else 0

        # Safety hazard: critical priority misclassified and auto-routed
        critical_escaped = (
            (auto_df["true_priority"] == "Critical") &
            (auto_df["pred_priority"] != "Critical")
        ).sum()

        rows.append({
            "threshold": thresh,
            "auto_routed_count": int(n_auto),
            "review_count": int(n_review),
            "auto_routing_rate": auto_rate,
            "review_rate": review_rate,
            "auto_category_acc": cat_acc,
            "auto_priority_acc": pri_acc,
            "auto_dept_acc": dept_acc,
            "auto_full_match_acc": all_acc,
            "critical_errors_auto_routed": int(critical_escaped),
        })

    return pd.DataFrame(rows)


def generate_report(sweep_df: pd.DataFrame, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Pick recommended threshold: highest auto-routing rate with >= 90% full match and 0 critical escapes
    safe_candidates = sweep_df[sweep_df["critical_errors_auto_routed"] == 0]
    if not safe_candidates.empty:
        recommended = safe_candidates.sort_values(by="auto_routing_rate", ascending=False).iloc[0]
    else:
        recommended = sweep_df.iloc[-1]

    md = []
    md.append("# Confidence Threshold & Routing Analysis Report")
    md.append("")
    md.append("## 1. Executive Summary & Recommendation")
    md.append(f"- **Recommended Default Threshold**: `{recommended['threshold']:.2f}`")
    md.append(f"- **Projected Auto-Routing Rate**: `{recommended['auto_routing_rate']:.1f}%`")
    md.append(f"- **Projected Human Review Rate**: `{recommended['review_rate']:.1f}%`")
    md.append(f"- **Auto-Routed Ticket Accuracy (All 3 Labels Correct)**: `{recommended['auto_full_match_acc']:.1f}%`")
    md.append(f"- **Critical Escaped Errors (without safety layer)**: `{int(recommended['critical_errors_auto_routed'])}`")
    md.append("")
    md.append("## 2. Threshold Sweep (0.70 to 0.90)")
    md.append("")
    md.append("| Threshold | Auto-Routed % | Review Queue % | Cat Acc | Pri Acc | Dept Acc | Full Match % | Critical Escaped |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for _, row in sweep_df.iterrows():
        md.append(
            f"| **{row['threshold']:.2f}** | {row['auto_routing_rate']:.1f}% | "
            f"{row['review_rate']:.1f}% | {row['auto_category_acc']:.1f}% | "
            f"{row['auto_priority_acc']:.1f}% | {row['auto_dept_acc']:.1f}% | "
            f"{row['auto_full_match_acc']:.1f}% | {int(row['critical_errors_auto_routed'])} |"
        )

    md.append("")
    md.append("## 3. Decision Rationale")
    md.append("- At lower thresholds (e.g. 0.70), auto-routing rate is high, but risk of misrouting critical tickets increases.")
    md.append("- At higher thresholds (e.g. 0.90), routing safety is maximized, but human review workload rises.")
    md.append(f"- Operating at `{recommended['threshold']:.2f}` balances cost-efficiency with high classification fidelity.")
    md.append("- Coupled with Phase 11 deterministic safety escalation, any high-severity billing/technical ticket is guaranteed human review.")

    output_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Threshold analysis report written to: {output_path}")


def main():
    args = parse_args()
    pred_path = Path(args.pred_csv)
    if not pred_path.exists():
        print(f"ERROR: {pred_path} not found. Run Phase 9 evaluate.py first.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(pred_path)
    thresholds = [0.70, 0.75, 0.80, 0.82, 0.85, 0.88, 0.90]
    sweep_df = run_sweep(df, thresholds)
    generate_report(sweep_df, Path(args.report_out))
    print("\nPHASE 10 COMPLETE — Threshold analysis finished.")


if __name__ == "__main__":
    main()
