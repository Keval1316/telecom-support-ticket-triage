# Project State - Telecom Ticket Triage

## Meta
- Last updated: 2026-08-21
- Current phase: Phase 9 (Evaluation) & Phase 13–18 (Database, FastAPI Backend & React Dashboard)
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
- Phase 6: COMPLETE — Base model download pipeline created & verified
- Phase 7: COMPLETE — Dataset tokenization with loss masking verified
- Phase 8: COMPLETE — QLoRA fine-tuning finished (240 steps / 3 epochs). Trained adapter (`adapter_model.safetensors`, 119.8 MB) saved in `models/adapters/telecom-ticket-triage/`
- Phase 9: CODE READY — `training/evaluate.py` created
- Phase 10: CODE READY — `training/confidence.py` & `training/threshold_analysis.py` created
- Phase 11: CODE READY — `backend/app/ml/priority_escalator.py` created
- Phase 12: CODE READY — `backend/app/ml/inference.py` created
- Phase 13+: NEXT — Database Layer, FastAPI REST API, CSV processor, Analytics engine, React Frontend

## Key decisions locked in
- Training completed on Tesla T4 GPU (3 epochs, effective batch size 16, lr=2e-4, LoRA r=16 alpha=32).
- Adapter weights: `models/adapters/telecom-ticket-triage/adapter_model.safetensors` (119.8 MB)
- Local runtime: ₹0 inference using 4-bit local Qwen2.5-3B + LoRA adapter
- Database: SQLite with SQLAlchemy ORM (Postgres-compatible schema)
- Safety: Deterministic priority escalation guardrails for critical outage/emergency keywords

## Repo state
- `models/adapters/telecom-ticket-triage/`: Adapter weights & tokenizer files present
- `data/splits/train.csv`: 1,288 rows (Final)
- `data/splits/validation.csv`: 276 rows (Final)
- `data/splits/test.csv`: 276 rows (Final)
- `data/future_testing/future_test.csv`: 205 rows (Locked)

## Next action
1. Implement Phase 13: Database Layer (`backend/app/database/`, `backend/app/models/ticket.py`, CRUD operations).
2. Implement Phase 14: FastAPI Backend with 7 REST endpoints.
3. Implement Phase 15: CSV Batch Processing service.
4. Implement Phase 16: Analytics & Trend calculation engine.
5. Implement Phase 17: Human Review queue & resolution endpoints.
6. Implement Phase 18: Modern Dark-Themed React Dashboard.
