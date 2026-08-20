# ==============================================================================
# Kaggle Notebook: Telecom Support Ticket Triage QLoRA Training Pipeline
# Run on Kaggle with Accelerator: GPU T4 x 1 (Internet: ON)
# ==============================================================================

# --- CELL 1: Clone Repository & Setup Working Directory ---
"""
!git clone https://github.com/Keval1316/telecom-support-ticket-triage.git /kaggle/working/telecom-support-ticket-triage
%cd /kaggle/working/telecom-support-ticket-triage
!pwd
"""

# --- CELL 2: Install Required Packages & Hardware Pre-flight Check ---
"""
!pip install -q -r training/requirements-colab.txt
!python scripts/hardware_check.py
"""

# --- CELL 3: Phase 6 — Download Base Model (Qwen2.5-3B) ---
"""
!python training/download_base_model.py \
    --model-id Qwen/Qwen2.5-3B \
    --target-dir models/base/Qwen2.5-3B
"""

# --- CELL 4: Phase 7 — Tokenize & Prepare Datasets ---
"""
!python training/prepare_dataset.py \
    --model-path models/base/Qwen2.5-3B \
    --max-length 512
"""

# --- CELL 5: Phase 8 — Run 4-Bit QLoRA Fine-Tuning (~15–20 min on T4) ---
"""
!python training/train.py \
    --model-path models/base/Qwen2.5-3B \
    --max-length 512 \
    --epochs 3 \
    --batch-size 2 \
    --grad-accum 8 \
    --learning-rate 2e-4 \
    --lora-rank 16 \
    --lora-alpha 32 \
    --output-dir models/adapters/telecom-ticket-triage
"""

# --- CELL 6: Phase 9 — Run Evaluation on Test Split (276 samples) ---
"""
!python training/evaluate.py \
    --base-model models/base/Qwen2.5-3B \
    --adapter-path models/adapters/telecom-ticket-triage \
    --test-csv data/splits/test.csv \
    --report-out reports/evaluation_report.md \
    --pred-out reports/test_predictions.csv
"""

# --- CELL 7: Phase 10 — Run Confidence Threshold Analysis ---
"""
!python training/threshold_analysis.py \
    --pred-csv reports/test_predictions.csv \
    --report-out reports/threshold_analysis.md
"""

# --- CELL 8: Display Results & Reports ---
"""
from IPython.display import Markdown, display

print("=== EVALUATION REPORT ===")
with open("reports/evaluation_report.md", "r") as f:
    display(Markdown(f.read()))

print("=== THRESHOLD ANALYSIS REPORT ===")
with open("reports/threshold_analysis.md", "r") as f:
    display(Markdown(f.read()))
"""

# --- CELL 9: Zip & Download Trained Adapter Weights to Local PC ---
"""
!zip -r /kaggle/working/telecom_adapter.zip models/adapters/telecom-ticket-triage reports/
print("Adapter zip created at /kaggle/working/telecom_adapter.zip")
"""
