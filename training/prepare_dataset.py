"""
Phase 7 - Dataset preparation for QLoRA fine-tuning.
Masks labels so loss is computed ONLY on the assistant's JSON response,
not the system prompt or the customer's ticket text.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPLITS_DIR = REPO_ROOT / "data" / "splits"
PREPARED_DIR = REPO_ROOT / "training" / "prepared"

STANDARD_FIELDS = ["ticket_id", "customer_name", "contact_number", "review",
                    "timestamp", "category", "priority", "department"]

SYSTEM_PROMPT = (
    "You are a support-ticket triage classifier for a telecom company. "
    "Given a customer support ticket, respond with ONLY a strict JSON object "
    "with exactly these keys: \"category\", \"priority\", \"department\". "
    "No explanation, no extra text, no markdown fences.\n\n"
    "category must be one of: Billing, Technical, Account, Refund, General\n"
    "priority must be one of: Critical, High, Medium, Low\n"
    "department must be one of: Finance, Technical, Account, Refunds, General Support"
)

DUMMY_ROWS = [
    {
        "ticket_id": "dummy-0001", "customer_name": "Test User", "contact_number": "XXXXXXXXXX",
        "review": "My recharge payment was deducted twice but only one recharge was applied to my number.",
        "timestamp": "2026-01-01T10:00:00", "category": "Billing", "priority": "High", "department": "Finance",
    },
    {
        "ticket_id": "dummy-0002", "customer_name": "Test User 2", "contact_number": "XXXXXXXXXX",
        "review": "No network in my area since morning, complete outage, urgent please fix.",
        "timestamp": "2026-01-01T11:00:00", "category": "Technical", "priority": "Critical", "department": "Technical",
    },
    {
        "ticket_id": "dummy-0003", "customer_name": "Test User 3", "contact_number": "XXXXXXXXXX",
        "review": "Can you tell me the validity of my current recharge plan?",
        "timestamp": "2026-01-01T12:00:00", "category": "General", "priority": "Low", "department": "General Support",
    },
]


def load_split_csv(path: Path, allow_missing_self_test: bool):
    if not path.exists():
        if allow_missing_self_test:
            print(f"  [self-test] {path} not found - using {len(DUMMY_ROWS)} dummy rows instead")
            return DUMMY_ROWS[:]
        print(f"ERROR: {path} not found. Run the Phase 3-5 pipeline first, "
              f"or pass --self-test to smoke-test with dummy data.", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_example(row: dict) -> dict:
    assistant_json = json.dumps({
        "category": row["category"],
        "priority": row["priority"],
        "department": row["department"],
    }, ensure_ascii=False)
    system_msg = {"role": "system", "content": SYSTEM_PROMPT}
    user_msg = {"role": "user", "content": row["review"]}
    assistant_msg = {"role": "assistant", "content": assistant_json}
    return {
        "prompt_messages": [system_msg, user_msg],
        "full_messages": [system_msg, user_msg, assistant_msg],
        "ticket_id": row["ticket_id"],
    }


def tokenize_examples(examples, tokenizer, max_length):
    from datasets import Dataset

    def _map(batch):
        full_texts = [
            tokenizer.apply_chat_template(m, tokenize=False, add_generation_prompt=False)
            for m in batch["full_messages"]
        ]
        prompt_texts = [
            tokenizer.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
            for m in batch["prompt_messages"]
        ]
        full_enc = tokenizer(full_texts, truncation=True, max_length=max_length, padding=False)
        prompt_enc = tokenizer(prompt_texts, truncation=True, max_length=max_length, padding=False)

        labels = []
        for full_ids, prompt_ids in zip(full_enc["input_ids"], prompt_enc["input_ids"]):
            prompt_len = min(len(prompt_ids), len(full_ids))
            lbl = [-100] * prompt_len + full_ids[prompt_len:]
            labels.append(lbl[:len(full_ids)])

        full_enc["labels"] = labels
        return full_enc

    ds = Dataset.from_list(examples)
    ds = ds.map(_map, batched=True, remove_columns=["prompt_messages", "full_messages"])
    return ds


def run_split(name: str, tokenizer, max_length: int, self_test: bool):
    rows = load_split_csv(SPLITS_DIR / f"{name}.csv", allow_missing_self_test=self_test)
    print(f"  {name}: {len(rows)} raw rows")

    for r in rows:
        missing = [f for f in STANDARD_FIELDS if f not in r or r[f] in (None, "")]
        if missing:
            print(f"    WARNING: {name} ticket_id={r.get('ticket_id')} missing fields {missing}, skipping")
    rows = [r for r in rows if all(r.get(f) for f in STANDARD_FIELDS)]

    examples = [build_example(r) for r in rows]
    ds = tokenize_examples(examples, tokenizer, max_length)

    out_dir = PREPARED_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    ds.save_to_disk(str(out_dir))
    print(f"  {name}: saved {len(ds)} tokenized examples -> {out_dir}")

    if len(ds) > 0:
        sample_text = tokenizer.apply_chat_template(
            examples[0]["full_messages"], tokenize=False, add_generation_prompt=False
        )
        n_masked = sum(1 for l in ds[0]["labels"] if l == -100)
        n_total = len(ds[0]["labels"])
        print(f"  {name}: sample formatted example:\n{'-'*50}\n{sample_text}\n{'-'*50}")
        print(f"  {name}: label check - {n_masked}/{n_total} tokens masked (prompt), "
              f"{n_total - n_masked} tokens counted in loss (assistant response)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", default="./models/base/Qwen2.5-3B",
                         help="Path to downloaded base model (Phase 6 output)")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--self-test", action="store_true",
                         help="Use dummy synthetic rows for any missing split CSV.")
    args = parser.parse_args()

    from transformers import AutoTokenizer

    model_path = Path(args.model_path)
    if not model_path.exists():
        print(f"ERROR: model path {model_path} not found. Run Phase 6 download first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading tokenizer from {model_path} ...")
    tokenizer = AutoTokenizer.from_pretrained(str(model_path))
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    for split_name in ["train", "validation", "test"]:
        print(f"\nProcessing split: {split_name}")
        run_split(split_name, tokenizer, args.max_length, args.self_test)

    print("\nDONE.")
    if args.self_test:
        print("NOTE: ran in --self-test mode with dummy data. "
              "Re-run WITHOUT --self-test once data/splits/*.csv exist for real.")


if __name__ == "__main__":
    main()
