"""
Central config loader for the synthetic data factory.
Reads .env from the repo root and exposes a typed Config object.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")


def _get_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    return int(val) if val else default


class Config:
    GROQ_API_KEYS = [k.strip() for k in os.environ.get("GROQ_API_KEYS", "").split(",") if k.strip()]
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    GENERATION_BATCH_SIZE = _get_int("GENERATION_BATCH_SIZE", 25)
    TARGET_DATASET_SIZE = _get_int("TARGET_DATASET_SIZE", 2000)
    RANDOM_SEED = _get_int("RANDOM_SEED", 42)

    KEY_RPM_LIMIT = 30
    KEY_TPM_LIMIT = 6000
    KEY_RPD_LIMIT = 14400

    REPO_ROOT = REPO_ROOT
    RAW_DIR = REPO_ROOT / "data" / "raw"
    MANIFEST_DIR = REPO_ROOT / "data" / "manifests"

    DATASET_VERSION = os.environ.get("DATASET_VERSION", "v1.0")

    @classmethod
    def validate(cls):
        problems = []
        if not cls.GROQ_API_KEYS:
            problems.append("GROQ_API_KEYS is empty - add at least one key to .env")
        if not cls.GROQ_MODEL:
            problems.append("GROQ_MODEL is empty - set it in .env")
        if problems:
            for p in problems:
                print(f"CONFIG ERROR: {p}", file=sys.stderr)
            sys.exit(1)
        return cls


if __name__ == "__main__":
    Config.validate()
    print("Config OK")
    print(f"  Keys loaded: {len(Config.GROQ_API_KEYS)}")
    print(f"  Model: {Config.GROQ_MODEL}")
    print(f"  Target size: {Config.TARGET_DATASET_SIZE}")
    print(f"  Batch size: {Config.GENERATION_BATCH_SIZE}")
    print(f"  Seed: {Config.RANDOM_SEED}")
    print(f"  Dataset version: {Config.DATASET_VERSION}")
