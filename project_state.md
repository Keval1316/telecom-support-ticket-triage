# Project State - Telecom Ticket Triage

## Meta
- Last updated: 2026-08-20
- Current phase: Phase 8 (QLoRA Training completed / weights saved) -> Ready for Phase 9 (Evaluation) & Phase 13+ (Backend & UI)
- Completed phases: [0, 1, 2, 3, 4, 5, 6, 7, 8]
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
- Phase 6: COMPLETE — `models/base/Qwen2.5-3B` download script verified
- Phase 7: COMPLETE — `training/prepare_dataset.py` prompt tokenization & label masking verified
- Phase 8: COMPLETE / CHECKPOINTED — QLoRA fine-tuning executed, adapter saved to `models/adapters/telecom-ticket-triage`
- Phase 9: CODE READY — `training/evaluate.py` created (Accuracy, Recall, Macro-F1, Critical Safety analysis)
- Phase 10: CODE READY — `training/confidence.py` & `training/threshold_analysis.py` created
- Phase 11: CODE READY — `backend/app/ml/priority_escalator.py` created (Deterministic safety escalation engine)
- Phase 12: CODE READY — `backend/app/ml/inference.py` created (Local 4-bit inference engine, zero runtime Groq cost)
- Phase 13+: NEXT — Database (SQLite), FastAPI backend, CSV processor, Analytics engine, React dashboard

## Key decisions locked in
- Training environment: Kaggle / Google Colab T4 GPU (16 GB VRAM)
- Model: Qwen/Qwen2.5-3B quantized to 4-bit NF4 with double quantization
- LoRA config: r=16, alpha=32, target_modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- Precision: Native FP16 hardware acceleration on Tensor Cores
- Prompt & Label masking: System prompt & user ticket masked with -100; loss calculated exclusively on assistant JSON tokens
- Safety & routing: Calibrated token confidence threshold (~0.85) + deterministic priority escalator for emergency/security/outage keywords
- Runtime cost: ₹0 runtime cost (local quantized Qwen2.5-3B + LoRA adapter, no paid APIs for inference)

## Repo state
- `training/download_base_model.py`: Phase 6 snapshot downloader & verification
- `training/prepare_dataset.py`: Phase 7 prompt formatter & label masker
- `training/train.py`: Phase 8 QLoRA fine-tuning script with auto-resume support
- `training/evaluate.py`: Phase 9 comprehensive model evaluation on test split
- `training/confidence.py`: Phase 10 confidence estimation & calibration
- `training/threshold_analysis.py`: Phase 10 confidence threshold sweep (0.70 - 0.90)
- `backend/app/ml/priority_escalator.py`: Phase 11 deterministic safety escalation engine
- `backend/app/ml/inference.py`: Phase 12 local inference service
- `notebooks/kaggle_telecom_training.py`: Kaggle notebook pipeline script
- `data/splits/train.csv`: 1,288 rows (Final)
- `data/splits/validation.csv`: 276 rows (Final)
- `data/splits/test.csv`: 276 rows (Final)
- `data/future_testing/future_test.csv`: 205 rows (Locked)

## Next action (When Resuming)
1. If you downloaded `telecom_adapter.zip` from Kaggle/Colab, extract it into `models/adapters/telecom-ticket-triage/`.
2. Run Phase 9 Evaluation:
   ```bash
   python training/evaluate.py --test-csv data/splits/test.csv --report-out reports/evaluation_report.md
   ```
3. Run Phase 10 Threshold Tuning:
   ```bash
   python training/threshold_analysis.py --pred-csv reports/test_predictions.csv --report-out reports/threshold_analysis.md
   ```
4. Proceed to Phase 13 (SQLite Database Models & CRUD) and Phase 14 (FastAPI Backend API).
