"""
Phase 6 - Base Model Download & Verification.
Downloads Qwen/Qwen2.5-3B from Hugging Face Hub to models/base/Qwen2.5-3B
and verifies that tokenizer and model weights are intact.
"""
import argparse
import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_ID = "Qwen/Qwen2.5-3B"
DEFAULT_TARGET_DIR = REPO_ROOT / "models" / "base" / "Qwen2.5-3B"


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 6 - Download Base Model")
    parser.add_argument(
        "--model-id",
        type=str,
        default=DEFAULT_MODEL_ID,
        help=f"Hugging Face model repository ID (default: {DEFAULT_MODEL_ID})",
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=str(DEFAULT_TARGET_DIR),
        help=f"Local target directory (default: {DEFAULT_TARGET_DIR})",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=os.getenv("HF_TOKEN", None),
        help="Optional Hugging Face access token (or set via HF_TOKEN env var)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing model files without re-downloading",
    )
    return parser.parse_args()


def verify_download(target_path: Path):
    print("\n--- Verifying downloaded model files ---")
    required_files = [
        "config.json",
        "tokenizer_config.json",
        "tokenizer.json",
    ]
    missing = [f for f in required_files if not (target_path / f).exists()]
    if missing:
        print(f"ERROR: Missing essential files in {target_path}: {missing}", file=sys.stderr)
        return False

    safetensors = list(target_path.glob("*.safetensors"))
    bin_files = list(target_path.glob("*.bin"))
    if not safetensors and not bin_files:
        print(f"ERROR: No model weights (.safetensors or .bin) found in {target_path}", file=sys.stderr)
        return False

    total_size_gb = sum(f.stat().st_size for f in target_path.rglob("*") if f.is_file()) / (1024**3)
    print(f"  Target path: {target_path}")
    print(f"  Model files: {len(safetensors)} safetensors weights found")
    print(f"  Total folder size: {total_size_gb:.2f} GB")

    print("\n--- Testing Tokenizer & Chat Template ---")
    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(str(target_path))
        print(f"  Tokenizer class: {tokenizer.__class__.__name__}")
        print(f"  Vocab size: {len(tokenizer)}")

        test_messages = [
            {"role": "system", "content": "You are a triage assistant."},
            {"role": "user", "content": "My SIM is blocked."},
        ]
        rendered = tokenizer.apply_chat_template(test_messages, tokenize=False, add_generation_prompt=True)
        print("  Chat template render test: OK")
        print(f"  Sample prompt preview:\n  {rendered.strip()[:100]}...")
    except Exception as e:
        print(f"ERROR verifying tokenizer: {e}", file=sys.stderr)
        return False

    print("\nRESULT: Phase 6 Base Model verification PASSED.")
    return True


def main():
    args = parse_args()
    target_path = Path(args.target_dir)

    if not args.verify_only:
        print(f"Downloading model '{args.model_id}' to '{target_path}'...")
        target_path.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=args.model_id,
            local_dir=str(target_path),
            token=args.hf_token,
            local_dir_use_symlinks=False,
            ignore_patterns=["*.msgpack", "*.h5", "*.ot"],
        )
        print("Download finished.")

    if not verify_download(target_path):
        sys.exit(1)


if __name__ == "__main__":
    main()
