"""
Phase 9 - Model Evaluation Script.
Loads base model + LoRA adapter, runs inference on test split (data/splits/test.csv),
computes comprehensive classification metrics (accuracy, precision, recall, macro-F1,
confusion matrices, Critical priority failure analysis), and outputs reports/evaluation_report.md.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
from peft import PeftModel
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_MODEL = REPO_ROOT / "models" / "base" / "Qwen2.5-3B"
DEFAULT_ADAPTER_DIR = REPO_ROOT / "models" / "adapters" / "telecom-ticket-triage"
DEFAULT_TEST_CSV = REPO_ROOT / "data" / "splits" / "test.csv"
DEFAULT_REPORT_PATH = REPO_ROOT / "reports" / "evaluation_report.md"
DEFAULT_PRED_CSV = REPO_ROOT / "reports" / "test_predictions.csv"

SYSTEM_PROMPT = (
    "You are a support-ticket triage classifier for a telecom company. "
    "Given a customer support ticket, respond with ONLY a strict JSON object "
    "with exactly these keys: \"category\", \"priority\", \"department\". "
    "No explanation, no extra text, no markdown fences.\n\n"
    "category must be one of: Billing, Technical, Account, Refund, General\n"
    "priority must be one of: Critical, High, Medium, Low\n"
    "department must be one of: Finance, Technical, Account, Refunds, General Support"
)

CATEGORIES = ["Billing", "Technical", "Account", "Refund", "General"]
PRIORITIES = ["Critical", "High", "Medium", "Low"]
DEPARTMENTS = ["Finance", "Technical", "Account", "Refunds", "General Support"]


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 9 - Model Evaluation")
    parser.add_argument("--base-model", type=str, default=str(DEFAULT_BASE_MODEL),
                        help="Path to base model directory")
    parser.add_argument("--adapter-path", type=str, default=str(DEFAULT_ADAPTER_DIR),
                        help="Path to LoRA adapter directory")
    parser.add_argument("--test-csv", type=str, default=str(DEFAULT_TEST_CSV),
                        help="Path to test CSV dataset")
    parser.add_argument("--report-out", type=str, default=str(DEFAULT_REPORT_PATH),
                        help="Path to output markdown report")
    parser.add_argument("--pred-out", type=str, default=str(DEFAULT_PRED_CSV),
                        help="Path to output prediction CSV")
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Limit samples for quick test run")
    return parser.parse_args()


def load_model(base_model_path: str, adapter_path: str):
    print(f"Loading base model from {base_model_path} in 4-bit...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    if Path(adapter_path).exists() and (Path(adapter_path) / "adapter_config.json").exists():
        print(f"Loading LoRA adapter from {adapter_path}...")
        model = PeftModel.from_pretrained(base_model, adapter_path)
        model.eval()
    else:
        print(f"WARNING: Adapter at {adapter_path} not found. Evaluating BASE model zero-shot.")
        model = base_model.eval()

    return model, tokenizer


def extract_json(text: str) -> dict:
    """Extract and parse structured JSON response from generated output."""
    clean_text = text.strip()
    clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
    clean_text = re.sub(r"\s*```$", "", clean_text)

    match = re.search(r"\{[\s\S]*\}", clean_text)
    if match:
        clean_text = match.group(0)

    try:
        data = json.loads(clean_text)
        return {
            "category": data.get("category", "General"),
            "priority": data.get("priority", "Medium"),
            "department": data.get("department", "General Support"),
            "raw_valid": True,
        }
    except Exception:
        return {
            "category": "General",
            "priority": "Medium",
            "department": "General Support",
            "raw_valid": False,
        }


def predict_single(model, tokenizer, review: str) -> Tuple[dict, float, str]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": review},
    ]
    prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=64,
            do_sample=False,  # Greedy for reproducible evaluation
            pad_token_id=tokenizer.pad_token_id,
            return_dict_in_generate=True,
            output_scores=True,
        )

    gen_tokens = outputs.sequences[0][inputs["input_ids"].shape[1] :]
    gen_text = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

    # Calculate average transition probability confidence over generated tokens
    confidence = 1.0
    if outputs.scores:
        token_probs = []
        for i, score_tensor in enumerate(outputs.scores):
            probs = torch.softmax(score_tensor[0], dim=-1)
            token_id = gen_tokens[i].item()
            token_prob = probs[token_id].item()
            token_probs.append(token_prob)
        if token_probs:
            confidence = float(np.mean(token_probs))

    parsed = extract_json(gen_text)
    return parsed, confidence, gen_text


def compute_metrics(y_true, y_pred, labels):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    rec = recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return {
        "accuracy": float(acc),
        "macro_precision": float(prec),
        "macro_recall": float(rec),
        "macro_f1": float(f1),
        "per_class": report,
        "confusion_matrix": cm.tolist(),
    }


def generate_report(metrics_cat, metrics_pri, metrics_dept, results_df, critical_failures, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_tickets = len(results_df)
    valid_json_count = int(results_df["raw_valid"].sum())
    valid_json_rate = (valid_json_count / total_tickets) * 100 if total_tickets > 0 else 0

    critical_total = sum(1 for _, row in results_df.iterrows() if row["true_priority"] == "Critical")
    critical_underestimated = critical_failures

    md = []
    md.append("# Model Evaluation Report — Fine-Tuned Qwen2.5-3B")
    md.append("")
    md.append("## 1. Executive Summary")
    md.append(f"- **Test Set Size**: {total_tickets} tickets")
    md.append(f"- **Valid JSON Output Rate**: {valid_json_rate:.1f}% ({valid_json_count}/{total_tickets})")
    md.append(f"- **Average Model Confidence**: {results_df['confidence'].mean():.3f}")
    md.append("")
    md.append("| Task | Accuracy | Macro Precision | Macro Recall | Macro F1 |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    md.append(f"| **Category** | {metrics_cat['accuracy']*100:.2f}% | {metrics_cat['macro_precision']*100:.2f}% | {metrics_cat['macro_recall']*100:.2f}% | {metrics_cat['macro_f1']*100:.2f}% |")
    md.append(f"| **Priority** | {metrics_pri['accuracy']*100:.2f}% | {metrics_pri['macro_precision']*100:.2f}% | {metrics_pri['macro_recall']*100:.2f}% | {metrics_pri['macro_f1']*100:.2f}% |")
    md.append(f"| **Department** | {metrics_dept['accuracy']*100:.2f}% | {metrics_dept['macro_precision']*100:.2f}% | {metrics_dept['macro_recall']*100:.2f}% | {metrics_dept['macro_f1']*100:.2f}% |")
    md.append("")
    md.append("## 2. Priority & Safety Critical Analysis")
    md.append(f"- **Total True Critical Tickets**: {critical_total}")
    crit_rec = metrics_pri["per_class"].get("Critical", {}).get("recall", 0.0) * 100
    md.append(f"- **Critical Priority Recall**: {crit_rec:.2f}%")
    md.append(f"- **Critical Tickets Underestimated (Predicted as Low/Medium)**: {critical_underestimated}")
    if critical_underestimated > 0:
        md.append(f"  > [!WARNING]\n  > {critical_underestimated} critical ticket(s) were predicted as Low/Medium. These MUST be caught by the Phase 11 deterministic safety escalation layer.")
    else:
        md.append("  > [!NOTE]\n  > 0 critical tickets misclassified into Low/Medium.")
    md.append("")
    md.append("## 3. Per-Class Performance Breakdown")
    md.append("")
    md.append("### Category Breakdown")
    md.append("| Class | Precision | Recall | F1-Score | Support |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    for cls in CATEGORIES:
        stats = metrics_cat["per_class"].get(cls, {})
        p = stats.get("precision", 0) * 100
        r = stats.get("recall", 0) * 100
        f = stats.get("f1-score", 0) * 100
        s = stats.get("support", 0)
        md.append(f"| {cls} | {p:.1f}% | {r:.1f}% | {f:.1f}% | {s} |")
    md.append("")
    md.append("### Priority Breakdown")
    md.append("| Class | Precision | Recall | F1-Score | Support |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    for cls in PRIORITIES:
        stats = metrics_pri["per_class"].get(cls, {})
        p = stats.get("precision", 0) * 100
        r = stats.get("recall", 0) * 100
        f = stats.get("f1-score", 0) * 100
        s = stats.get("support", 0)
        md.append(f"| {cls} | {p:.1f}% | {r:.1f}% | {f:.1f}% | {s} |")
    md.append("")
    md.append("### Department Breakdown")
    md.append("| Class | Precision | Recall | F1-Score | Support |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    for cls in DEPARTMENTS:
        stats = metrics_dept["per_class"].get(cls, {})
        p = stats.get("precision", 0) * 100
        r = stats.get("recall", 0) * 100
        f = stats.get("f1-score", 0) * 100
        s = stats.get("support", 0)
        md.append(f"| {cls} | {p:.1f}% | {r:.1f}% | {f:.1f}% | {s} |")
    md.append("")
    output_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Evaluation report written to: {output_path}")


def main():
    args = parse_args()
    test_csv = Path(args.test_csv)
    if not test_csv.exists():
        print(f"ERROR: {test_csv} not found.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(test_csv)
    if args.max_samples:
        df = df.head(args.max_samples)
    print(f"Loaded {len(df)} test rows from {test_csv}")

    model, tokenizer = load_model(args.base_model, args.adapter_path)

    results = []
    print("\n--- Running Inference on Test Split ---")
    for idx, row in df.iterrows():
        review = str(row["review"])
        parsed, conf, raw_gen = predict_single(model, tokenizer, review)

        res = {
            "ticket_id": row.get("ticket_id", f"ticket-{idx}"),
            "review": review,
            "true_category": row["category"],
            "pred_category": parsed["category"],
            "true_priority": row["priority"],
            "pred_priority": parsed["priority"],
            "true_department": row["department"],
            "pred_department": parsed["department"],
            "confidence": conf,
            "raw_valid": parsed["raw_valid"],
            "raw_output": raw_gen,
        }
        results.append(res)
        if (idx + 1) % 25 == 0 or (idx + 1) == len(df):
            print(f"  Processed {idx + 1}/{len(df)} tickets...")

    results_df = pd.DataFrame(results)
    pred_out_path = Path(args.pred_out)
    pred_out_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(pred_out_path, index=False)
    print(f"Saved test predictions to: {pred_out_path}")

    # Compute metrics
    metrics_cat = compute_metrics(results_df["true_category"], results_df["pred_category"], CATEGORIES)
    metrics_pri = compute_metrics(results_df["true_priority"], results_df["pred_priority"], PRIORITIES)
    metrics_dept = compute_metrics(results_df["true_department"], results_df["pred_department"], DEPARTMENTS)

    critical_failures = sum(
        1 for _, r in results_df.iterrows()
        if r["true_priority"] == "Critical" and r["pred_priority"] in ["Low", "Medium"]
    )

    generate_report(
        metrics_cat, metrics_pri, metrics_dept, results_df, critical_failures, Path(args.report_out)
    )
    print("\nPHASE 9 COMPLETE — Model evaluation finished.")


if __name__ == "__main__":
    main()
