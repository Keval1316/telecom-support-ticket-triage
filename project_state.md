# Project State — Telecom Ticket Triage

## Meta
- Last updated: 2026-08-17
- Current phase: Phase 2 (complete, awaiting "continue" for Phase 3)
- Completed phases: [0, 1, 2]
- Frontend stack: React + Vite + Tailwind + Framer Motion + Recharts
- Base model: Qwen2.5-3B
- Fine-tuning method: QLoRA (4-bit)

## Key decisions locked in
- GPU: NVIDIA RTX 2050, 4GB VRAM confirmed (driver caps at CUDA 11.7). Too tight for comfortable local QLoRA training.
- Training location: GOOGLE COLAB (free T4, 16GB VRAM) — locked in. Local machine does NOT need torch/CUDA/bitsandbytes at all.
- Split requirements: requirements.txt = local-only (CPU: groq, fastapi, pandas, sklearn, etc). training/requirements-colab.txt = training-only (torch, transformers, peft, bitsandbytes, trl, datasets, accelerate) — installed inside Colab notebook in Phase 8, not locally.
- Groq API key(s): user creating key(s); groq_client.py (Phase 3) built for 1-N key rotation via GROQ_API_KEYS comma-separated env var.
- Frontend framework: Vite + React (not Next.js).
- Confidence threshold: not yet finalized — selected in Phase 10 (range 0.70-0.90).
- Database: SQLite for dev, Postgres-portable schema.
- Runtime cost target: ₹0 — Groq is offline-only, never a runtime dependency.

## Repo state
- Local venv (.venv) created and activated, Python 3.12.5, Windows 11.
- Local requirements.txt installed cleanly and verified via scripts/local_env_check.py: dotenv, pydantic 2.8.2, pandas 2.2.2, numpy 1.26.4, sklearn 1.5.1, groq 0.9.0, fastapi 0.112.0, sqlalchemy 2.0.32, httpx 0.27.0, pytest 8.3.2 — all OK.
- training/requirements-colab.txt created (not installed locally, will be installed inside Colab in Phase 8).
- training/hardware_check.py exists (GPU-focused version, superseded by the Colab-based plan but kept for reference).
- scripts/local_env_check.py created and passing.
- Full Section 59 folder layout + .gitignore, .env.example, docker-compose.yml, Dockerfile, README.md all in place from Phase 1.
- Git: 1 commit so far (Phase 1 scaffold). Phase 2 changes not yet committed.
- Datasets generated: none yet.
- Model artifacts: none yet.

## Environment notes
- GPU available locally: yes, RTX 2050 4GB, but NOT used for training (Colab instead).
- Using Colab for training: YES, confirmed, this is the primary plan (not fallback anymore).
- Groq model in use: not yet selected — verify current valid Groq model name at Phase 3 implementation time.
- User works directly in their own PowerShell terminal (not in Claude's sandbox) — Claude gives copy-pasteable PowerShell command blocks (heredoc-style '@"..."@' for multi-line files) rather than running bash itself for this project.

## Open issues / blockers
- Groq API key not yet confirmed in .env — needed before Phase 3 script can run.
- Colab notebook not yet created — will be built in Phase 8.

## Next action
- Commit Phase 2 changes locally (git add/commit commands given).
- Begin Phase 3 — Groq Synthetic Data Factory (groq_client.py with key rotation, generation_config.py, scenario_plan.py, generate_tickets.py).
