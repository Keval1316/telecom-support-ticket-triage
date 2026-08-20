# Project State - Telecom Ticket Triage

## Meta
- Last updated: 2026-08-20
- Current phase: Phase 6 to Phase 8 — Model Download, Preparation & QLoRA Fine-Tuning Execution
- Completed phases: [0, 1, 2, 3, 4, 5]
- Frontend stack: React + Vite + Tailwind + Framer Motion + Recharts
- Base model: Qwen2.5-3B (Qwen/Qwen2.5-3B)
- Fine-tuning method: QLoRA (4-bit NF4)

## Phases Status Summary
- Phase 0: COMPLETE — Requirements & Architecture established
- Phase 1: COMPLETE — Project initialized & folder structure created
- Phase 2: COMPLETE — Environment checked & dependencies verified
- Phase 3: COMPLETE — 2,045 raw records generated via Groq Data Factory
- Phase 4: COMPLETE — Data deduplication, schema validation, and class balancing completed
- Phase 5: COMPLETE — Splits created: Train=1,288, Val=276, Test=276, Future-Test=205, Evaluation & Demo datasets created
- Phase 6: CODE READY (Colab Run Pending) — `training/download_base_model.py` and `notebooks/phase6_download_cells.py` created
- Phase 7: CODE READY (Colab Run Pending) — `training/prepare_dataset.py` and `notebooks/phase7_prepare_dataset_cells.py` created (masks prompt with -100)
- Phase 8: CODE READY (Colab Run Pending) — `training/train.py` and `notebooks/phase8_train_cells.py` created (SFTTrainer + 4-bit NF4 LoRA)
- Phase 9: CODE READY — `training/evaluate.py` created (Accuracy, Recall, Macro-F1, Critical Safety analysis)
- Phase 10: CODE READY — `training/confidence.py` & `training/threshold_analysis.py` created
- Phase 11: CODE READY — `backend/app/ml/priority_escalator.py` created (Deterministic safety escalation engine)
- Phase 12: CODE READY — `backend/app/ml/inference.py` created (Local 4-bit inference engine, zero runtime Groq cost)

## Key decisions locked in
- Training environment: Google Colab T4 GPU (16 GB VRAM)
- Model: Qwen/Qwen2.5-3B quantized to 4-bit NF4 with double quantization
- LoRA config: r=16, alpha=32, target_modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- SFTTrainer config: 3 epochs, cosine LR scheduler (lr=2e-4), warmup_ratio=0.03, paged_adamw_8bit, batch_size=2, grad_accum=8 (effective batch size=16), max_length=512
- Prompt & Label masking: System prompt & user ticket masked with -100; loss calculated exclusively on assistant JSON tokens
- Safety & routing: Calibrated token confidence threshold (~0.85) + deterministic priority escalator for emergency/security/outage keywords
- Runtime cost: ₹0 runtime cost (local quantized Qwen2.5-3B + LoRA adapter, no paid APIs for inference)

## Repo state
- `training/download_base_model.py`: Phase 6 snapshot downloader & verification
- `training/prepare_dataset.py`: Phase 7 prompt formatter & label masker
- `training/train.py`: Phase 8 QLoRA fine-tuning script
- `training/evaluate.py`: Phase 9 comprehensive model evaluation on test split
- `training/confidence.py`: Phase 10 confidence estimation & calibration
- `training/threshold_analysis.py`: Phase 10 confidence threshold sweep (0.70 - 0.90)
- `backend/app/ml/priority_escalator.py`: Phase 11 deterministic safety escalation engine
- `backend/app/ml/inference.py`: Phase 12 local inference service
- `notebooks/phase6_download_cells.py`: Colab cells for Phase 6
- `notebooks/phase7_prepare_dataset_cells.py`: Colab cells for Phase 7
- `notebooks/phase8_train_cells.py`: Colab cells for Phase 8
- `notebooks/phase9_eval_cells.py`: Colab cells for Phase 9 & 10
- `data/splits/train.csv`: 1,288 rows (Final)
- `data/splits/validation.csv`: 276 rows (Final)
- `data/splits/test.csv`: 276 rows (Final)
- `data/future_testing/future_test.csv`: 205 rows (Locked)

## Environment notes
- Local GPU: RTX 2050 4GB — used for lightweight local test/dev; training executes on Google Colab T4.
- Colab GPU: T4 (16 GB) — verified for 4-bit QLoRA fine-tuning.

## Next action
1. Open Google Colab with **T4 GPU** runtime.
2. Mount Google Drive and set working directory to repo root.
3. Install dependencies:
   ```bash
   pip install -q -r training/requirements-colab.txt
   pip install -q triton==2.3.0
   ```
4. Execute Phase 6 (Base Model Download):
   ```bash
   python training/download_base_model.py --model-id Qwen/Qwen2.5-3B --target-dir models/base/Qwen2.5-3B
   ```
5. Execute Phase 7 (Tokenization & Dataset Preparation):
   ```bash
   python training/prepare_dataset.py --model-path models/base/Qwen2.5-3B --max-length 512
   ```
6. Execute Phase 8 (QLoRA Fine-Tuning):
   ```bash
   python training/train.py --model-path models/base/Qwen2.5-3B --max-length 512
   ```
7. Execute Phase 9 & 10 (Evaluation & Threshold Analysis):
   ```bash
   python training/evaluate.py --base-model models/base/Qwen2.5-3B --adapter-path models/adapters/telecom-ticket-triage
   python training/threshold_analysis.py
   ```
8. Review `reports/evaluation_report.md` and `reports/threshold_analysis.md`.
