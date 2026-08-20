# ==============================================================================
# Phase 9 & 10 Colab Cells: Model Evaluation & Threshold Analysis
# ==============================================================================

# --- CELL 1: Run Full Evaluation on Test Split (276 samples) ---
"""
!python training/evaluate.py \
    --base-model models/base/Qwen2.5-3B \
    --adapter-path models/adapters/telecom-ticket-triage \
    --test-csv data/splits/test.csv \
    --report-out reports/evaluation_report.md \
    --pred-out reports/test_predictions.csv
"""

# --- CELL 2: Run Confidence Threshold Sweep & Tuning (Phase 10) ---
"""
!python training/threshold_analysis.py \
    --pred-csv reports/test_predictions.csv \
    --report-out reports/threshold_analysis.md
"""

# --- CELL 3: Display Generated Markdown Reports ---
"""
from IPython.display import Markdown, display

with open("reports/evaluation_report.md", "r") as f:
    display(Markdown(f.read()))

with open("reports/threshold_analysis.md", "r") as f:
    display(Markdown(f.read()))
"""
