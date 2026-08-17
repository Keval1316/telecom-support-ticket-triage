# Telecom Support Ticket Triage

AI-powered support ticket triage system for a telecom service provider.
Fine-tuned Qwen2.5-3B (QLoRA) classifies incoming tickets by category,
priority, and department, applies a confidence-based routing + safety
escalation layer, and surfaces results via a FastAPI backend and a
React (Vite + Tailwind + Framer Motion) dashboard.

> **Status:** Scaffolding in progress (Phase 1 of 27). Full README with
> setup, architecture diagram, results, and demo instructions will be
> written in Phase 26.

## Quick pipeline overview

```
Groq (synthetic data, offline) -> QLoRA fine-tune Qwen2.5-3B -> Local adapter
        -> FastAPI + local model inference -> Confidence + safety routing
        -> SQLite -> Analytics -> React dashboard
```

Runtime cost target: **₹0** — Groq is only used offline during data generation.

## Project structure

See `master-build-prompt.md` (Section 59) / `project_state.md` for the
full folder layout and current build phase.

## Setup (placeholder — finalized in later phases)

```bash
cp .env.example .env      # fill in GROQ_API_KEYS, etc.
pip install -r requirements.txt
```

Backend and frontend run instructions will be added as those phases
are completed (`scripts/run_backend.sh`, `scripts/run_frontend.sh`).
