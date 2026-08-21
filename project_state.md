# Project State - Telecom Ticket Triage

## Meta
- Last updated: 2026-08-21
- Current phase: Complete Production System (Phases 0–18 implemented & verified)
- Completed phases: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
- Frontend stack: React + Vite + Tailwind CSS + Framer Motion + Recharts + Lucide Icons
- Backend stack: FastAPI + SQLAlchemy SQLite ORM + Pydantic v2
- Base model: Qwen2.5-3B (4-bit QLoRA)
- Safety: Deterministic priority escalation guardrails

## Key Accomplishments
1. **Model Training & Adapter Weights**:
   - 3 epochs QLoRA completed on cloud GPU.
   - Adapter weights saved in `models/adapters/telecom-ticket-triage/adapter_model.safetensors` (119.8 MB).
2. **Fixed JSON Extraction**:
   - Non-greedy regex and `json.JSONDecoder().raw_decode` implemented in `evaluate.py` and `inference.py` to prevent malformed text parsing errors.
3. **Database Layer (Phase 13)**:
   - SQLite engine with WAL mode and thread safety (`backend/app/database/session.py`).
   - Ticket ORM model (`backend/app/models/ticket.py`).
   - CRUD query operations and human review resolving (`backend/app/database/crud.py`).
4. **FastAPI Backend (Phase 14 & 17)**:
   - 7 REST endpoints: `/triage`, `/upload-csv`, `/tickets`, `/analytics/summary`, `/analytics/trends`, `/review-queue`, `/review-queue/{id}/resolve`.
   - Heuristic fallback inference engine for ₹0 runtime cost and 100% environment resilience.
5. **Analytics & Trend Engine (Phase 16)**:
   - Real DB-backed aggregations and period-over-period percentage delta calculations with zero-division handling (`backend/app/analytics/engine.py`).
6. **React Frontend Dashboard (Phase 18)**:
   - Vite + Tailwind + Framer Motion + Recharts.
   - 4 Complete Views:
     - View 1: Batch CSV Upload Dropzone with progress bar & Single Ticket interactive playground.
     - View 2: Executive KPI stats & Recharts Category Donut, Priority Spectrum, Department Workload charts.
     - View 3: Search, multi-dropdown filter bar, paginated ticket table, and 7-day trend indicator cards.
     - View 4: Human Review Queue with inline corrections, escalation reasons, and active learning feedback.
   - Production bundle verified (`npm run build` passed with zero errors).

## Launch Commands
- Start both Backend & Frontend together:
  ```bash
  python run_app.py
  ```
- Or individually:
  - Backend: `uvicorn backend.app.main:app --reload --port 8000`
  - Frontend: `cd frontend && npm run dev`
