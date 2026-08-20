# ==============================================================================
# Phase 7 Colab Cells: Dataset Tokenization & Label Masking
# ==============================================================================

# --- CELL 1: Tokenize Splits & Mask Prompt Tokens (Loss only on Assistant JSON) ---
"""
!python training/prepare_dataset.py --model-path models/base/Qwen2.5-3B --max-length 512
"""

# --- CELL 2: Verify Prepared Arrow Datasets ---
"""
import os
from datasets import load_from_disk

for split in ["train", "validation", "test"]:
    p = f"training/prepared/{split}"
    ds = load_from_disk(p)
    print(f"{split} count: {len(ds)} samples | features: {ds.column_names}")
    # Verify label masking (-100 on prompt)
    sample_lbl = ds[0]["labels"]
    masked_count = sum(1 for x in sample_lbl if x == -100)
    unmasked_count = len(sample_lbl) - masked_count
    print(f"  {split}[0] -> Total tokens: {len(sample_lbl)}, Masked: {masked_count}, Loss tokens: {unmasked_count}")
    assert unmasked_count > 0, "ERROR: Label masking is broken (all -100)"
print("Phase 7 Verification PASSED!")
"""
