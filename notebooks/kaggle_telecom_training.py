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
import os
import base64
from IPython.display import HTML, display

# 1. Package the trained LoRA adapter, reports, and training log into a zip file
!zip -r /kaggle/working/telecom_adapter.zip models/adapters/telecom-ticket-triage reports/ training/training_log.json

# 2. Render direct in-browser download button (bypasses Kaggle 404 URL restrictions)
zip_path = "/kaggle/working/telecom_adapter.zip"
if os.path.exists(zip_path):
    file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"Zip created successfully ({file_size_mb:.2f} MB). Rendering direct download button...")
    with open(zip_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    
    html_btn = f'''
    <div style="margin-top: 15px; padding: 15px; background: #1e293b; border-radius: 10px; text-align: center;">
        <h3 style="color: #38bdf8; margin-bottom: 10px;">Training Artifacts Ready!</h3>
        <a href="data:application/zip;base64,{b64}" download="telecom_adapter.zip" 
           style="display: inline-block; padding: 12px 28px; background: #2563eb; color: white; 
                  font-weight: bold; border-radius: 8px; text-decoration: none; font-size: 16px; 
                  box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
           ⬇️ Click Here to Download telecom_adapter.zip ({file_size_mb:.2f} MB)
        </a>
    </div>
    '''
    display(HTML(html_btn))
else:
    print("ERROR: telecom_adapter.zip was not found. Check training logs.")
"""
