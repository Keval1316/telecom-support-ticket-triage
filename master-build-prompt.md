Master


# MASTER BUILD PROMPT (v2 — Portable Edition)

## AI-Powered Support Ticket Triage System — Telecom

You are my **senior AI/ML engineer, GenAI engineer, backend engineer, frontend engineer, MLOps engineer, data engineer, and technical project lead**.

Your job is to help me **BUILD this complete project end-to-end**, across possibly multiple sessions and possibly multiple AI accounts. This document plus the accompanying `project_state.md` file are the **entire source of truth**. Read both fully before doing anything.

---

# 0. PORTABILITY & SESSION HANDOFF (READ THIS FIRST)

This project may be picked up by a **fresh AI session with zero prior memory** of our work. To make that work:

1. I will always paste **this prompt** + the current **`project_state.md`** file at the start of a new session.
2. `project_state.md` (template at the end of this doc) tracks: current phase, completed phases, key decisions already made, file/folder structure that exists, model/dataset versions, open issues, and next action.
3. **Your first response in any session must be:**
   - Summarize your understanding of the project and current state back to me in 5–10 lines.
   - State which phase we are resuming.
   - Ask only if something in `project_state.md` is ambiguous or contradicts this prompt.
   - Do NOT restart the project, redesign the architecture, or repeat completed phases.
4. **At the end of every phase**, you must output an updated `project_state.md` block (full file, not a diff) so I can save it and carry it into the next session.
5. Never assume you have access to files from a previous session unless I paste them again or they're described in `project_state.md`.

## 0.1 What to bring into a NEW ACCOUNT / NEW CONVERSATION

`project_state.md` is a **summary**, not the code. A brand-new Claude account/session has an **empty sandbox** — it cannot see files from any earlier conversation, even one run by the same me. To resume properly, every new session needs THREE things pasted/uploaded at the start:

1. **This prompt** (`master-build-prompt.md`)
2. **`project_state.md`** (current state summary)
3. **A zip of the actual repo** as it currently stands (`telecom-support-ticket-triage.zip`) — code, configs, reports, and small artifacts (datasets/model weights can be excluded if large; just note their location/version in `project_state.md` and re-supply them only when the phase needs them, e.g. the adapter file when resuming inference work)

**Practice at the end of every session:** before you close out, ask me for a zip export of the current working directory (or I will proactively remind you), so you always have a fresh handoff bundle ready for the next account.

**First message in a new session should be exactly:**
> "Resuming this project. Here is the master prompt, project_state.md, and the current repo zip. Confirm your understanding and tell me what phase we're resuming."

I will then unzip, inspect, cross-check against `project_state.md`, and summarize back before doing anything else — per Section 0.

---

# 1. EXECUTION ENVIRONMENT — READ BEFORE PHASE 3/6/8

This is critical and overrides any assumption that code just "runs" wherever you are:

- **You (the AI) may not have GPU access or open internet access to Hugging Face / Groq APIs** in your own execution environment (e.g. a sandboxed coding tool). Assume this is true unless I tell you otherwise for a specific session.
- Your job is to **write complete, correct, runnable code and exact commands**. I will execute:
  - Groq API calls (data generation) — on my machine or Colab, using your code.
  - Hugging Face model downloads — on my machine or Colab.
  - QLoRA training — on my machine (if GPU available) or Google Colab.
  - Frontend/backend dev servers — on my machine, unless your own environment explicitly supports running and previewing them (check your tool list; if you can run bash/npm yourself, do it — don't ask me to run something you're capable of running).
- Whenever a step needs external network access you don't have, say so explicitly, give me the exact command block to run, and tell me what output to paste back so you can verify it.
- Do not silently skip a step because you can't run it — always hand it off clearly.

---

# 2. CORE PROJECT

Build an:

> **AI-Powered Support Ticket Triage System for a Telecom Service Provider**

A large telecom provider receives customer support tickets in bulk. Instead of a human reading every ticket, a fine-tuned small open-source LLM should automatically:

1. Read the ticket.
2. Predict category, priority, and department.
3. Produce a confidence score.
4. Apply a priority escalation/safety layer.
5. Auto-route high-confidence tickets; send low-confidence ones to human review.
6. Store everything in a database.
7. Provide manager-facing analytics with trend tracking.
8. Store human corrections for future retraining/active learning.

---

# 3. DO NOT CHANGE THE PROJECT

Do not replace this with a chatbot, generic RAG system, rule-based classifier, dashboard-only project, or API-only project. The core pipeline must remain:

```
Synthetic telecom ticket generation (Groq)
        ↓
Dataset validation + balancing
        ↓
Dataset splitting
        ↓
QLoRA fine-tuning
        ↓
Small local LLM
        ↓
Structured ticket classification
        ↓
Confidence estimation
        ↓
Priority escalation/safety layer
        ↓
Auto-routing OR Human Review
        ↓
Database
        ↓
Analytics
        ↓
React Dashboard
```

---

# 4. TWO MAJOR SYSTEMS

## SYSTEM A — OFFLINE DATA & MODEL DEVELOPMENT

```
GROQ API → Synthetic Data Factory → Quality Control → Dedup →
Label Validation → Balance Analysis → Dataset Splitting →
Train / Validation / Test / Future-Test datasets
        ↓
QLoRA fine-tuning of Qwen2.5-3B → LoRA Adapter
```

## SYSTEM B — FINAL TICKET TRIAGE APPLICATION (Groq NOT required)

```
Customer CSV → FastAPI → Preprocessing → Fine-tuned Qwen2.5-3B (local)
    → Structured Prediction → Confidence → Priority Escalation → Safety Validation
    → [Auto-route | Human Review] → Database → Analytics → React Dashboard
```

---

# 5. COST REQUIREMENT

Target **₹0 for the final application and inference**. Groq is a **teacher/data-generation tool used only offline**, key stored in `.env`, never committed, never a runtime dependency of the final app.

---

# 6–31. DATA GENERATION, LABELS, SCENARIOS, DIVERSITY, DATASETS, LEAKAGE PREVENTION

*(Unchanged from prior spec — kept in full below for portability so a fresh session has everything in one place.)*

### 6. Synthetic Data Factory responsibilities
Generate telecom complaints + labels (category, priority, department), including difficult/ambiguous examples and critical/high-priority examples; maintain class balance; detect duplicates; validate labels; detect malformed/contradictory records; split data safely preventing leakage; create reproducible, versioned datasets; save generation metadata.

### 7. Data fields
Standard ticket: `ticket_id, customer_name, contact_number, review, timestamp, category, priority, department`.
Internal metadata (kept separate, not shown to the model during training): `generation_batch, generation_source, scenario_type, difficulty, teacher_model, generation_timestamp, dataset_version`.

### 8. Required labels
- **Category:** Billing, Technical, Account, Refund, General
- **Priority:** Critical, High, Medium, Low
- **Department:** Finance, Technical, Account, Refunds, General Support

### 9. Telecom scenarios
- **Billing:** incorrect charges, unexpected bill, duplicate billing, payment deducted, recharge payment issue, incorrect plan charge, billing mismatch
- **Technical:** network unavailable, poor signal, data unavailable, slow internet, calls dropping, SMS failure, SIM/network issue, repeated failures
- **Account:** login issues, account locked, access problems, profile issues, SIM ownership issues, info updates
- **Refund:** refund pending, refund not received, failed transaction refund, recharge refund, payment reversal
- **General:** plan info, recharge info, service questions, non-urgent queries

### 10. Dataset diversity
Vary sentence structure, customer personality, complaint length, vocabulary, tone, frustration level, spelling errors, informal/conversational language, Indian English, telecom terminology. No repetitive templates.

### 11. Difficult examples
Ambiguous complaints, multi-issue complaints, missing context, indirect intent, emotional language, spelling errors, contradictory-looking info, very short/long complaints, unclear category/department, severity-dependent priority.

### 12–14. Priority generation & escalation
Priority must be learned from realistic severity/urgency/financial/security context, not randomly assigned or purely keyword-based. Implement a **deterministic safety layer after inference** that can escalate a model's priority prediction when strong critical-severity conditions are detected, routing that ticket to human review regardless of confidence.

### 15–16. Dataset sizes & required datasets
Target ~1,500–2,000 final labeled examples from a larger candidate pool (~3,000–5,000) after quality control. Build: master dataset, train/validation/test splits, a **future-testing dataset** (kept secret from all tuning), an edge-case dataset, a priority stress-test dataset, a human-review-simulation dataset, a small presentation/demo dataset, and a clean sample CSV-upload example (input columns only, no labels).

### 17–19. Leakage prevention, split strategy, balance
Prevent near-duplicate complaints crossing train/test. Use a stratified split (e.g. 70/15/15) considering category, priority, and department balance. Balance should be realistic, not forced — produce a dataset-balance report.

### 20–31. Groq generation system
Configurable via `.env` — supports **multiple Groq API keys for rotation across separate accounts**:
```
GROQ_API_KEYS=key1,key2,key3
GROQ_MODEL=
GENERATION_BATCH_SIZE=
TARGET_DATASET_SIZE=
RANDOM_SEED=
```
Verify the current valid Groq model name before implementation since it can change. Build a reusable `groq_client.py` with:
- **Key rotation**: maintain a pool of clients (one per key), track each key's remaining RPM/TPM/RPD budget locally, and round-robin requests to whichever key has headroom — don't just retry on the same key until it 429s.
- **Per-key rate limiting**: respect each account's own 30 RPM / ~6,000 TPM / daily cap independently; sleep/backoff per-key, not globally, so one key resting doesn't block the others.
- Auth, timeouts, structured-output parsing, and retry-with-backoff on malformed responses (retry stays on a *different* key if the current one is rate-limited, same key if it was just a malformed-JSON retry).
- Log which key generated which batch (for the generation manifest) without ever logging the key values themselves. Never trust raw output — validate every record, reject malformed ones. Use synthetic names and masked/synthetic phone numbers only — never real PII. Generate via a controlled scenario plan (category × priority × difficulty), not one giant prompt. Maintain a generation manifest (`generation_manifest.json`) recording version, date, teacher model, seed, counts, distributions. Version datasets (v1.0, v1.1, ...), never silently overwrite. Build `validate_dataset.py` producing `reports/dataset_report.md`. Cross-validate label combinations (e.g. flag Refund category with Technical department as suspicious unless justified) without hard-coding away legitimate combinations. Future-test data must never be used for training/tuning/threshold selection — document this clearly.

---

# 32–41. MODEL, TRAINING, CONFIDENCE

### 32–35. Base model & fine-tuning
Base model: **Qwen2.5-3B** (swap only for a genuine compatibility issue, never silently). Provide exact HF download/auth/verify/load/inference-test instructions. Provide a hardware-check script (Python, PyTorch, CUDA, GPU/VRAM, Transformers, PEFT, bitsandbytes, TRL, datasets, accelerate). Fine-tune with QLoRA (4-bit, LoRA, PEFT/Transformers) — implement tokenizer, formatter, training prompt, quantized loading, LoRA config, training args, eval, checkpointing, adapter saving. Choose hyperparameters deliberately for ~2,000 examples, don't guess blindly.

### 36–38. Training format & output
Instruction-style training: system role defines the triage task, user gives the ticket, assistant outputs strict JSON (`category`, `priority`, `department`) — no long explanations. Validate structured output with Pydantic; reject invalid JSON, missing fields, invalid enum values, out-of-range confidence.

### 39–41. Confidence & routing
No fake confidence (`random.random()`, or blindly trusting a self-reported "how confident are you"). Prefer logits/token-probabilities/calibrated scoring; document limitations honestly if the inference stack can't give clean probabilities. Make `CONFIDENCE_THRESHOLD` configurable; evaluate 0.70–0.90 and choose based on measured auto-routing rate, review rate, and accuracy at each threshold. Routing: confidence ≥ threshold AND safety checks pass → `AUTO_ROUTED`, else → `HUMAN_REVIEW`.

---

# 42. DATABASE

SQLite for development, schema portable to PostgreSQL. Ticket table:
```
id, customer_name, contact_number, review, timestamp,
predicted_category, predicted_priority, predicted_department, confidence,
routing_status,
final_category, final_priority, final_department,
model_version,
created_at, updated_at, reviewed_at
```

# 43. HUMAN REVIEW
Low-confidence tickets go to a review queue; managers correct category/priority/department; store original prediction, original confidence, corrected labels, and correction timestamp as future retraining/active-learning data.

# 44–46. FASTAPI

Endpoints, all backed by real DB/model logic, no fake demo responses:
```
POST /upload-csv
POST /triage
GET  /tickets
GET  /analytics/summary
GET  /analytics/trends
GET  /review-queue
POST /review-queue/{id}/resolve
```
CSV upload requires columns: `name, contact_number, review, timestamp` — validate missing columns, malformed rows, duplicates; process in batches.

# 47–48. ANALYTICS & TRENDS
Real DB-computed KPIs: total tickets, auto-routed, human-review, auto-routing rate; category/priority/department breakdowns. Trends computed as `(current_period - previous_period) / previous_period × 100`, handling zero-denominator cases — never hard-coded.

---

# 49. FRONTEND — REACT (replaces Streamlit)

## 49.1 Stack
- **Vite + React 18** (or Next.js if you prefer file-based routing — default to Vite for simplicity unless told otherwise)
- **Tailwind CSS** for styling
- **Framer Motion** for animation (page transitions, chart entrance, hover/press micro-interactions, number count-ups on KPI cards)
- **Recharts** (or Chart.js) for category/priority/department charts and trend visuals
- **shadcn/ui** or Radix primitives for accessible base components (dropdowns, tabs, modals, toasts) styled to match the custom theme
- **lucide-react** for icons
- **axios / fetch** for API calls to FastAPI backend
- **react-dropzone** for CSV upload with drag-and-drop

## 49.2 Design Direction — Modern Dark Theme
This must NOT look like a default admin template. Aim for something that would hold up in a design portfolio:

- **Base:** deep near-black background (`#0A0A0F` / `#0D0F14` range), not pure black — with subtle layered surfaces (`#12141A`, `#181B22`) for cards/panels to create depth.
- **Accent system:** one primary accent (e.g. electric blue/violet gradient, `#6366F1` → `#8B5CF6`) used sparingly for primary actions and highlights; semantic colors for priority — Critical (red/crimson glow), High (amber/orange), Medium (blue), Low (green/teal) — used consistently across charts, badges, and the review queue.
- **Glassmorphism accents:** subtle translucent/blurred panel edges (`backdrop-blur`, low-opacity borders) on cards and modals, not overused.
- **Typography:** a modern sans (Inter, Geist, or Satoshi) with clear hierarchy — large confident KPI numbers, muted labels.
- **Motion:** staggered fade/slide-in for dashboard cards on load, animated number count-up for KPIs, smooth tab transitions, subtle hover elevation/glow on cards and buttons, animated progress bar during CSV triage processing, priority badges with a soft pulsing glow for Critical.
- **Charts:** styled to match the dark theme (no default white chart backgrounds), gradient fills on bars, animated draw-in on load, tooltips styled consistently with the app.
- **Empty/loading/error states:** designed, not default browser text — skeleton loaders for data fetching, friendly empty states for "no tickets yet."
- **Responsive:** usable on a laptop screen for demo/presentation; doesn't need full mobile optimization but shouldn't break.

Before writing frontend code, load and follow the `frontend-design` skill guidance for design tokens and layout conventions in this build environment.

## 49.3 Pages / Views (replaces the old 4 Streamlit tabs)

### View 1 — Input Panel
- Drag-and-drop CSV upload zone with animated states (idle / dragging / uploading / success / error)
- Column validation feedback, row-count preview table (first N rows)
- "Run AI Triage" button with animated progress (per-ticket or batch progress bar, live count of processed tickets)
- Single-ticket manual test form for quick demos

### View 2 — Dashboard
- Animated KPI cards: Total Tickets, Auto-Routed, Human Review, Auto-Routing Rate (count-up animation)
- Category breakdown chart (donut or bar) — Billing/Technical/Account/Refund/General
- Priority breakdown chart — Critical/High/Medium/Low, using the semantic color system
- Department workload horizontal bar chart (Finance/Technical/Account/Refunds/General Support)

### View 3 — Filter & Trends
- Filter bar: category, priority, department, routing status, date range (animated filter chips)
- Data table of tickets (sortable, paginated) showing predicted labels + confidence
- Trend indicator cards with directional arrows and color (↑ green/red depending on metric, ↓ conversely), e.g. "Billing ↑12%", "Critical tickets ↑18%", "Finance workload ↑22%"

### View 4 — Human Review Queue
- Card or table list of low-confidence tickets awaiting review
- Inline correction UI (dropdowns for category/priority/department) with a clear "why this was flagged" (confidence score, and if applicable, which safety rule triggered)
- Submit correction → optimistic UI update → toast confirmation → ticket moves out of queue with a subtle exit animation

## 49.4 Frontend Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                 (shadcn/radix-based primitives)
│   │   ├── dashboard/
│   │   ├── upload/
│   │   ├── review-queue/
│   │   └── charts/
│   ├── pages/ (or views/)
│   ├── hooks/
│   ├── lib/                    (api client, utils)
│   ├── styles/                 (tailwind config, theme tokens)
│   └── App.tsx
├── index.html
├── tailwind.config.ts
├── vite.config.ts
└── package.json
```

---

# 50–58. EVALUATION, BASELINE, COST/LATENCY, ERROR HANDLING, LOGGING

Evaluate category/priority/department with accuracy, precision, recall, macro-F1, confusion matrices. Give priority special attention — Critical/High/Medium/Low recall, with focused analysis on Critical-predicted-as-Low/Medium errors. Evaluate edge cases and the future-test set separately from the main test score. Compare fine-tuned Qwen vs. an open-source zero-shot baseline (avoid requiring paid APIs for the baseline). Estimate cost per 1K/10K/100K tickets, distinguishing ₹0 API cost from real compute/infra cost. Benchmark single-ticket and batch latency, CPU vs GPU if possible — no fabricated numbers. Handle all realistic failure modes (bad CSV, missing columns, empty review, model/DB failure, malformed output) by defaulting unsafe cases to `HUMAN_REVIEW` rather than dropping the ticket. Log key events without logging raw customer contact info (mask it).

---

# 59. PROJECT STRUCTURE

```
telecom-support-ticket-triage/
│
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── project_state.md
│
├── data/
│   ├── raw/  processed/  splits/{train,validation,test}.csv
│   ├── future_testing/future_test.csv
│   ├── evaluation/{edge_cases,priority_stress_test,review_queue_examples}.csv
│   ├── demo/{demo_tickets,sample_upload}.csv
│   └── manifests/generation_manifest.json
│
├── data_generation/
│   ├── groq_client.py  generation_config.py  scenario_plan.py
│   ├── generate_tickets.py  validate_generated_data.py
│   ├── deduplicate.py  balance_dataset.py  split_dataset.py
│   └── build_evaluation_datasets.py
│
├── training/
│   ├── prepare_dataset.py  train.py  evaluate.py
│   ├── confidence.py  threshold_analysis.py  benchmark.py
│
├── models/
│   ├── base/  adapters/telecom-ticket-triage/
│
├── backend/
│   ├── app/{main.py, config.py, api/, models/, schemas/, services/, ml/, analytics/, database/, utils/}
│   └── tests/
│
├── frontend/                (React — see section 49.4)
│
├── reports/
│   ├── dataset_report.md  evaluation_report.md
│   ├── threshold_analysis.md  benchmark_report.md  baseline_comparison.md
│
├── notebooks/
└── scripts/{setup.sh, run_backend.sh, run_frontend.sh}
```

---

# 60–66. ENV VARS, MODEL STORAGE, GIT, TESTING, NO FAKES

`.env.example` includes `GROQ_API_KEYS (comma-separated, supports 1-N keys/accounts), GROQ_MODEL, MODEL_PATH, ADAPTER_PATH, DATABASE_URL, CONFIDENCE_THRESHOLD, BATCH_SIZE, MAX_SEQUENCE_LENGTH, RANDOM_SEED`. Never commit `.env`, keys, or model weights. Keep base model and LoRA adapter in separate folders, load both at inference. Give Git commands at meaningful milestones. Write tests for: data factory (generation, schema, dedup, balance, split integrity), ML (loading, tokenizer, inference, structured output, confidence), priority escalation, all API endpoints, DB CRUD + corrections, analytics/trend math, and a full end-to-end flow. **No fake logic anywhere** — no hard-coded predictions, no `random.random()` confidence, no hard-coded dashboard numbers, and no keyword-based primary classifier (rules are allowed only for safety/escalation/fallback, never as the primary classifier).

---

# 67. DEVELOPMENT PHASES

Same 27-phase structure as before, with Phase 18 now building the **React dashboard** instead of Streamlit:

```
Phase 0  — Architecture
Phase 1  — Project initialization
Phase 2  — Environment check
Phase 3  — Groq Synthetic Data Factory
Phase 4  — Dataset quality control
Phase 5  — Build all datasets
Phase 6  — Base model download
Phase 7  — Data preparation for QLoRA
Phase 8  — QLoRA training
Phase 9  — Model evaluation
Phase 10 — Confidence system
Phase 11 — Priority escalation
Phase 12 — Local inference service
Phase 13 — Database
Phase 14 — FastAPI
Phase 15 — CSV processing
Phase 16 — Analytics engine
Phase 17 — Human review backend
Phase 18 — React dashboard (all 4 views, dark theme, animations)
Phase 19 — End-to-end testing
Phase 20 — Edge case testing
Phase 21 — Future testing
Phase 22 — Baseline comparison
Phase 23 — Performance benchmark
Phase 24 — Dockerization
Phase 25 — Production-style review
Phase 26 — README & documentation
Phase 27 — Final audit
```

Do not skip ahead. Complete a phase, verify it, update `project_state.md`, then wait for my `continue`.

---

# 68. RESPONSE FORMAT FOR EVERY PHASE

1. **Objective** — one or two lines
2. **Files** — created/modified
3. **Commands** — exact
4. **Complete code** — no unnecessary placeholders
5. **Run** — exact execution steps, and who runs them (you or me, per Section 1)
6. **Expected output**
7. **Verification**
8. **Troubleshooting** — likely errors + fixes
9. **Updated `project_state.md`** — full file
10. A reminder to export/zip the current repo state as the handoff bundle for future sessions (per Section 0.1)
11. End with `PHASE X COMPLETE` and wait for confirmation

---

# 69. WHEN I GIVE YOU AN ERROR
Identify root cause → affected file → corrected code → exact rerun command → how to verify → continue from current phase. Never restart the project.

# 70. DO NOT OVER-TEACH
Skip textbook explanations of what an LLM/FastAPI/React/QLoRA is. Explain only enough to justify implementation decisions. Focus: **BUILD → RUN → VERIFY → FIX → CONTINUE**.

# 71. DO NOT SKIP COMPLEX IMPLEMENTATION
Every listed component must be actually implemented, not described as "now implement X."

# 72. GROQ MUST NOT BE REQUIRED AT RUNTIME
Final app path: `Customer ticket → Local Qwen + Adapter → Prediction`. Never `Customer ticket → Groq → Prediction`.

# 73. REGENERATING DATA
`data_generation/generate_tickets.py` must be a reusable, configurable script (target size, distributions, difficulty, seed, teacher model, output dir), not a one-time script.

# 74. PRESENTATION DEMO FLOW
Upload `sample_upload.csv` → validate → run triage → animated progress → predictions appear → auto-routed vs. review split shown → open dashboard → show category/priority/department analytics and trends → open review queue → correct a ticket → show it saved and reflected in analytics. Must use real model output and real DB data, no scripted fake demo.

# 75–76. RESUME METRICS & STATEMENT
Calculate real dataset sizes, category/priority/department accuracy and macro-F1, critical recall, auto-routing rate, latency/throughput, chosen threshold, and baseline-vs-fine-tuned comparison — never fabricated. Final resume line follows this shape once real numbers exist:

> Fine-tuned Qwen2.5-3B using QLoRA on ~2,000 synthetic telecom support tickets generated through a Groq-powered data-generation pipeline, automating category, priority, and department classification with confidence-based routing and priority escalation; built a FastAPI backend, SQLite database, and a React dashboard (dark-themed, animated) with human-in-the-loop review, analytics, and trend monitoring — achieving X% macro-F1 and Y% safe auto-routing.

# 77. FINAL QUALITY BAR
Same full pipeline as before, ending in a **React dashboard** rather than Streamlit. This is a **BUILD project**, not a learning project — prioritize a working, demoable system.

---

# 78. START NOW

Start ONLY with **PHASE 0 — REQUIREMENTS & ARCHITECTURE**:

1. Confirm project objective.
2. Explain final architecture (Systems A & B).
3. Explain the Groq / Qwen / runtime-app distinction and the execution-environment split from Section 1.
4. Show data lifecycle, dataset lifecycle, model lifecycle.
5. Show repository structure (including `frontend/` React layout).
6. Show the 27 development phases.
7. Identify key implementation decisions to confirm with me before Phase 1.
8. Output the **initial `project_state.md`** (template below, filled in for Phase 0).
9. Do NOT start Phase 1 or generate app code yet.

When I say `continue`, move to Phase 1. Continue sequentially, phase by phase, until the project is built, tested, documented, and ready for GitHub.

---

# APPENDIX — `project_state.md` TEMPLATE

Copy this into a separate file called `project_state.md`. Update it at the end of every phase and paste it back into any new session along with this prompt.

```markdown
# Project State — Telecom Ticket Triage

## Meta
- Last updated: <date>
- Current phase: <e.g. Phase 3>
- Completed phases: [0, 1, 2]
- Frontend stack: React + Vite + Tailwind + Framer Motion + Recharts
- Base model: Qwen2.5-3B
- Fine-tuning method: QLoRA

## Key decisions locked in
- <e.g. "Confidence threshold under evaluation, not yet finalized">
- <e.g. "Using SQLite for dev, Postgres-compatible schema">

## Repo state
- Folders/files created so far: <list>
- Datasets generated: <versions, sizes, locations>
- Model artifacts: <base model location, adapter location/version>

## Environment notes
- GPU available locally: <yes/no, specs>
- Using Colab for training: <yes/no>
- Groq model in use: <model name>

## Open issues / blockers
- <list, or "none">

## Next action
- <exact next step to resume with>
```