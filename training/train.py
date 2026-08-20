"""
Phase 8 - QLoRA Fine-Tuning of Qwen2.5-3B for Telecom Ticket Triage.

Design choices:
  - 4-bit NF4 quantization (BitsAndBytesConfig) to fit on a 16 GB T4.
  - LoRA rank 16 / alpha 32 on all attention + MLP projection layers.
    For ~1,288 training examples, a small-to-medium rank avoids overfitting
    while still adapting the model meaningfully.
  - 3 epochs with cosine LR schedule and warm-up. On T4 with bs=2 + grad_acc=8
    this is ~480 steps per epoch (~1,440 total), manageable in <2 hours.
  - paged_adamw_8bit: lower VRAM footprint for optimizer states.
  - eval every epoch; save best checkpoint by eval loss.
  - Adapter saved separately from the base model (never overwritten).

Usage (Colab):
  python training/train.py
  python training/train.py --max-length 768   # if Cell 10 showed >5% truncation

IMPORTANT: Run AFTER prepare_dataset.py (Phase 7) has produced
  training/prepared/{train,validation,test}/.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import torch
from datasets import load_from_disk
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, DataCollatorForSeq2Seq
from trl import SFTConfig, SFTTrainer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT    = Path(__file__).resolve().parent.parent
PREPARED_DIR = REPO_ROOT / "training" / "prepared"
BASE_MODEL   = REPO_ROOT / "models" / "base" / "Qwen2.5-3B"
ADAPTER_DIR  = REPO_ROOT / "models" / "adapters" / "telecom-ticket-triage"
TRAINING_LOG = REPO_ROOT / "training" / "training_log.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 8 - QLoRA fine-tuning")
    parser.add_argument(
        "--model-path", default=str(BASE_MODEL),
        help="Path to the downloaded Qwen2.5-3B base model"
    )
    parser.add_argument(
        "--max-length", type=int, default=512,
        help="Max sequence length. Must match what prepare_dataset.py used."
    )
    parser.add_argument(
        "--epochs", type=int, default=3,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size", type=int, default=2,
        help="Per-device train batch size (keep low for T4 16 GB)"
    )
    parser.add_argument(
        "--grad-accum", type=int, default=8,
        help="Gradient accumulation steps. Effective batch = batch_size * grad_accum"
    )
    parser.add_argument(
        "--learning-rate", type=float, default=2e-4,
        help="Peak learning rate for cosine schedule"
    )
    parser.add_argument(
        "--lora-rank", type=int, default=16,
        help="LoRA rank r. 16 is a solid default for ~1,300 examples."
    )
    parser.add_argument(
        "--lora-alpha", type=int, default=32,
        help="LoRA alpha. Typically 2x the rank."
    )
    parser.add_argument(
        "--output-dir", default=str(ADAPTER_DIR),
        help="Where to save the LoRA adapter and training state"
    )
    return parser.parse_args()


def verify_prepared_datasets(prepared_dir: Path, max_length: int):
    """Verify training/prepared/{train,validation,test} exist and look sane."""
    for split in ["train", "validation", "test"]:
        path = prepared_dir / split
        if not path.exists():
            print(
                f"ERROR: {path} not found.\n"
                f"Run training/prepare_dataset.py first (Phase 7).",
                file=sys.stderr
            )
            sys.exit(1)
        ds = load_from_disk(str(path))
        if len(ds) == 0:
            print(f"ERROR: {split} dataset is empty.", file=sys.stderr)
            sys.exit(1)
        ex = ds[0]
        if "input_ids" not in ex or "labels" not in ex:
            print(
                f"ERROR: {split} dataset missing 'input_ids'/'labels' columns.\n"
                f"Re-run prepare_dataset.py.",
                file=sys.stderr
            )
            sys.exit(1)
        n_loss = sum(1 for l in ex["labels"] if l != -100)
        if n_loss == 0:
            print(
                f"ERROR: {split}[0] has all labels=-100 (label masking broken).\n"
                f"Re-run prepare_dataset.py.",
                file=sys.stderr
            )
            sys.exit(1)
        print(f"  {split}: {len(ds)} examples  OK (loss_tokens_ex0={n_loss})")


def load_model_and_tokenizer(model_path: str):
    """Load Qwen2.5-3B in 4-bit NF4 quantization mode."""
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,  # double quantization reduces memory ~0.4 bits/param
    )

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        # Qwen2 uses <|endoftext|> as eos; set pad = eos so the model doesn't error
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,  # Qwen2 needs this
    )
    model = prepare_model_for_kbit_training(model)
    return model, tokenizer


def apply_lora(model, lora_rank: int, lora_alpha: int):
    """
    Apply LoRA to all attention projection layers and MLP gate/up/down projections.
    Qwen2 uses: q_proj, k_proj, v_proj, o_proj (attention)
                gate_proj, up_proj, down_proj (MLP / SwiGLU)
    Targeting all 7 keeps the adapter expressive without blowing up parameter count.
    """
    lora_config = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_alpha,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def build_sft_config(args, output_dir: str) -> SFTConfig:
    """
    Build the SFTConfig (replaces TrainingArguments for SFTTrainer in TRL >=0.9).

    Key decisions:
    - bf16=True: BFloat16 on T4 is faster and more stable than fp16 for LLMs.
    - paged_adamw_8bit: offloads optimizer states to CPU pages, saving ~6 GB VRAM
      which is critical on the 16 GB T4 with a 3B-parameter model.
    - save_strategy="epoch" + load_best_model_at_end=True + metric_for_best_model=
      "eval_loss": saves every epoch and keeps the best checkpoint.
    - dataset_text_field is NOT set here because we pass pre-tokenized datasets
      (input_ids + labels already present); SFTTrainer handles this path correctly.
    - max_seq_length must be passed in SFTConfig (not just to the tokenizer) when
      using pre-tokenized datasets so the trainer's data collator doesn't truncate.
    """
    return SFTConfig(
        output_dir=output_dir,

        # --- Batch & accumulation ---
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,

        # --- Training loop ---
        num_train_epochs=args.epochs,
        max_steps=-1,  # -1 means use num_train_epochs

        # --- LR schedule ---
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,  # 3% of steps as warm-up

        # --- Precision ---
        bf16=True,
        fp16=False,

        # --- Optimizer ---
        optim="paged_adamw_8bit",

        # --- Sequence length ---
        max_seq_length=args.max_length,

        # --- Logging ---
        logging_steps=10,
        report_to="none",

        # --- Checkpointing ---
        save_strategy="epoch",
        eval_strategy="epoch",          # evaluate at the end of each epoch
        load_best_model_at_end=True,    # reload best checkpoint after training
        metric_for_best_model="eval_loss",
        greater_is_better=False,

        # --- Dataset text field ---
        # Leave unset: we pass pre-tokenized datasets with input_ids + labels columns.
        # Setting dataset_text_field would cause SFTTrainer to try to re-tokenize.
        dataset_kwargs={"skip_prepare_dataset": True},
    )


def save_adapter(model, tokenizer, output_dir: str):
    """Save the LoRA adapter weights. Does NOT save base model weights."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(out))
    tokenizer.save_pretrained(str(out))
    print(f"LoRA adapter saved to: {out}")
    # Save a small config so inference code knows what base model to use
    adapter_meta = {
        "base_model": "Qwen2.5-3B",
        "task": "telecom-ticket-triage",
        "label_schema": {
            "category": ["Billing", "Technical", "Account", "Refund", "General"],
            "priority": ["Critical", "High", "Medium", "Low"],
            "department": ["Finance", "Technical", "Account", "Refunds", "General Support"],
        },
    }
    (out / "triage_adapter_meta.json").write_text(
        json.dumps(adapter_meta, indent=2), encoding="utf-8"
    )


def main():
    args = parse_args()

    # --- Pre-flight checks ---
    if not torch.cuda.is_available():
        print("ERROR: CUDA not available. QLoRA training requires a GPU.", file=sys.stderr)
        sys.exit(1)

    model_path = Path(args.model_path)
    if not model_path.exists():
        print(
            f"ERROR: Base model not found at {model_path}.\n"
            f"Run Phase 6 to download Qwen2.5-3B first.",
            file=sys.stderr
        )
        sys.exit(1)

    print("\n--- Verifying prepared datasets ---")
    verify_prepared_datasets(PREPARED_DIR, args.max_length)

    print(f"\n--- GPU info ---")
    print(f"  GPU:  {torch.cuda.get_device_name(0)}")
    print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # --- Load datasets ---
    print("\n--- Loading tokenized datasets ---")
    train_dataset = load_from_disk(str(PREPARED_DIR / "train"))
    eval_dataset  = load_from_disk(str(PREPARED_DIR / "validation"))
    print(f"  train:      {len(train_dataset)} examples")
    print(f"  validation: {len(eval_dataset)} examples")

    # --- Load model ---
    print(f"\n--- Loading Qwen2.5-3B from {args.model_path} in 4-bit NF4 ---")
    model, tokenizer = load_model_and_tokenizer(args.model_path)

    # --- Apply LoRA ---
    print(f"\n--- Applying LoRA (rank={args.lora_rank}, alpha={args.lora_alpha}) ---")
    model = apply_lora(model, args.lora_rank, args.lora_alpha)

    # --- Build training config ---
    print("\n--- Building SFTConfig ---")
    sft_config = build_sft_config(args, args.output_dir)
    effective_bs = args.batch_size * args.grad_accum
    print(f"  effective batch size: {effective_bs}")
    print(f"  epochs: {args.epochs}")
    print(f"  learning rate: {args.learning_rate}")
    print(f"  max_seq_length: {args.max_length}")
    print(f"  output: {args.output_dir}")

    # --- Build data collator for dynamic sequence padding ---
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        pad_to_multiple_of=8,
        return_tensors="pt",
        padding=True,
    )

    # --- Build trainer ---
    trainer_kwargs = {
        "model": model,
        "args": sft_config,
        "train_dataset": train_dataset,
        "eval_dataset": eval_dataset,
        "data_collator": data_collator,
    }
    import inspect
    sig = inspect.signature(SFTTrainer.__init__)
    if "processing_class" in sig.parameters:
        trainer_kwargs["processing_class"] = tokenizer
    else:
        trainer_kwargs["tokenizer"] = tokenizer

    trainer = SFTTrainer(**trainer_kwargs)

    # --- Train ---
    print("\n--- Starting training ---")
    train_result = trainer.train()

    # --- Save adapter ---
    print("\n--- Saving LoRA adapter ---")
    # After load_best_model_at_end=True, trainer.model holds the best checkpoint
    save_adapter(trainer.model, tokenizer, args.output_dir)

    # --- Log final metrics ---
    metrics = train_result.metrics
    print("\n--- Training metrics ---")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Evaluate on validation set one final time with the best model
    eval_metrics = trainer.evaluate()
    print("\n--- Final eval metrics (best checkpoint) ---")
    for k, v in eval_metrics.items():
        print(f"  {k}: {v}")

    # Save a training log so we can reference it without re-running
    log = {
        "base_model": str(args.model_path),
        "adapter_path": str(args.output_dir),
        "epochs": args.epochs,
        "effective_batch_size": effective_bs,
        "learning_rate": args.learning_rate,
        "lora_rank": args.lora_rank,
        "lora_alpha": args.lora_alpha,
        "max_length": args.max_length,
        "train_examples": len(train_dataset),
        "val_examples": len(eval_dataset),
        "train_metrics": {k: float(v) if hasattr(v, '__float__') else v for k, v in metrics.items()},
        "eval_metrics": {k: float(v) if hasattr(v, '__float__') else v for k, v in eval_metrics.items()},
    }
    TRAINING_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"\nTraining log saved to: {TRAINING_LOG}")
    print("\nPHASE 8 COMPLETE — LoRA adapter saved.")
    print(f"Next: run training/evaluate.py (Phase 9) against the test split.")


if __name__ == "__main__":
    main()
