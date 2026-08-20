# Project State - Telecom Ticket Triage

## Meta
- Last updated: 2026-08-20
- Current phase: Phase 8 - QLoRA training (script written; Colab run PENDING)
- Completed phases: [0, 1, 2, 3, 4, 5, 6, 7-PENDING-real-run]
- Frontend stack: React + Vite + Tailwind + Framer Motion + Recharts
- Base model: Qwen2.5-3B
- Fine-tuning method: QLoRA (4-bit NF4)

## Phases 3-6 Status (VERIFIED CORRECT as of 2026-08-20)
- Phase 3: COMPLETE - 2045 raw records in tickets_v1.0.jsonl (1975 main + 70 top-up)
- Phase 4: COMPLETE - deduplicate.py, validate_generated_data.py, balance_dataset.py all ran; 0 malformed, 0 suspicious combos, imbalance 44.8x (down from 224x), smallest combo = 5
- Phase 5: COMPLETE - splits: train=1288, val=276, test=276, future_test=205
- Phase 6: COMPLETE - models/base/Qwen2.5-3B/ downloaded on Colab/Drive (not in git)

## Phase 7 Status
- prepare_dataset.py: WRITTEN and CORRECT (label masking on assistant JSON only)
- Self-test run: previously done (dummy data only)
- REAL RUN: PENDING - run in Colab via notebooks/phase7_prepare_dataset_cells.py
- Expected output: training/prepared/{train,validation,test}/ + training/prepared/meta.json

## Phase 8 Status
- training/train.py: WRITTEN and COMMITTED
- notebooks/phase8_train_cells.py: WRITTEN and COMMITTED (includes inference smoke test)
- ACTUAL TRAINING RUN: PENDING - must run in Colab after Phase 7 real run

## Key decisions locked in
- All prior decisions unchanged (Colab T4, 3 Groq accounts, GROQ_MODEL=openai/gpt-oss-120b, json_schema strict, max_retries=0, JSONL-then-CSV, SQLite dev DB, Rs0 runtime cost, single main branch, triton==2.3.0 fix)
- SECURITY: 3 Groq API keys in earlier chat session. .env never committed. Rotate when convenient.
- BUG FIXED (2026-08-19): split_dataset.py missing generation_source field. Fixed and committed.
- Dataset balance: targeted top-up for 9 worst combos; full QC re-run; 44.8x ratio (acceptable).
- Phase 7: loss computed ONLY on assistant JSON tokens (prompt masked with -100).
- Phase 8 hyperparameters: 4-bit NF4 quant + double quant, LoRA rank=16 alpha=32 on 7 Qwen2 projection layers (q/k/v/o_proj + gate/up/down_proj), 3 epochs, cosine LR, warmup_ratio=0.03, paged_adamw_8bit, bs=2 grad_acc=8 (effective=16), eval/save per epoch, load_best_model_at_end (metric=eval_loss), adapter saved separately from base.

## Repo state (as of commit 04dda1d, 2026-08-20)
- training/train.py - Phase 8 QLoRA training script (NEW, committed)
- notebooks/phase7_prepare_dataset_cells.py - Phase 7 Colab cells (NEW, committed)
- notebooks/phase8_train_cells.py - Phase 8 Colab cells with smoke test (NEW, committed)
- .gitignore - added training/prepared/ exclusions for binary HF arrow files
- data/splits/train.csv: 1288 rows - FINAL
- data/splits/validation.csv: 276 rows - FINAL
- data/splits/test.csv: 276 rows - FINAL
- data/future_testing/future_test.csv: 205 rows - LOCKED (never use for training/tuning)
- reports/dataset_report.md: 2045 records, 37 combos, ratio 44.8x
- training/prepared/: NOT in git - regenerate via Phase 7 in Colab
- models/base/Qwen2.5-3B: on Colab Drive, NOT in git
- models/adapters/telecom-ticket-triage: will be populated after Phase 8 training run

## Environment notes
- GPU locally: RTX 2050 4GB - NOT sufficient for QLoRA training; use Colab T4
- Colab T4 (16 GB): confirmed working; re-bootstrap each new session
- Groq accounts: recovered from daily quota exhaustion (2026-08-19)

## Open issues / blockers
- None blocking Phase 7+8. Ready to execute in Colab.
- After Phase 8 training: paste training_log.json back for review before Phase 9.
- Confirm Phase 8 Cell 10 inference smoke test produces valid JSON.

## Next action
1. Open Google Colab. Runtime -> T4 GPU.
2. Mount Drive, set REPO_DIR, git pull.
3. pip install -q -r training/requirements-colab.txt followed by pip install -q triton==2.3.0
4. Run Phase 7 cells (notebooks/phase7_prepare_dataset_cells.py):
   - Cell 7: python training/prepare_dataset.py --model-path models/base/Qwen2.5-3B --max-length 512
   - Cell 8: verify PASSED (label masking OK)
   - Cell 10: if truncation >5%, re-run with --max-length 768 and update train.py arg
   - Cell 11: git add/commit/push meta.json
5. Run Phase 8 cells (notebooks/phase8_train_cells.py):
   - Cell 7: python training/train.py --model-path models/base/Qwen2.5-3B --max-length 512 (45-90 min on T4)
   - Cell 8: review training_log.json metrics
   - Cell 10: inference smoke test MUST produce valid JSON before proceeding
   - Cell 11: git add/commit/push
6. Paste training_log.json contents back for review.
7. Begin Phase 9 (evaluate.py against test split).
