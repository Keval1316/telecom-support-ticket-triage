# ==============================================================================
# Phase 6 Colab Cells: Base Model Download & Verification
# Copy and execute these cells in Google Colab (with T4 GPU or Standard CPU runtime)
# ==============================================================================

# --- CELL 1: Clone / Pull Repo & Install Requirements ---
"""
!git pull origin main
!pip install -q -r training/requirements-colab.txt
!pip install -q triton==2.3.0
"""

# --- CELL 2: Run Hardware & Environment Pre-flight Check ---
"""
!python scripts/hardware_check.py
"""

# --- CELL 3: Download Qwen2.5-3B Base Model ---
"""
!python training/download_base_model.py --model-id Qwen/Qwen2.5-3B --target-dir models/base/Qwen2.5-3B
"""

# --- CELL 4: Verify Base Model Files & Tokenizer ---
"""
!python training/download_base_model.py --target-dir models/base/Qwen2.5-3B --verify-only
"""
