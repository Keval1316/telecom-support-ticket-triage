# Project State — Telecom Ticket Triage

## Meta
- Last updated: 2026-08-19
- Current phase: Targeted top-up generation IN PROGRESS, blocked on Groq daily quota (2nd time — main generation finished, but a small top-up run for underrepresented combos hit the same daily ceiling quickly since accounts were already near-exhausted). Phase 6 and Phase 7 (self-test) remain complete from before.
- Completed phases: [0, 1, 2, 6, 7-self-test]
- Phase 3: MAIN generation complete (1975/2000 accepted, 0 rejected) — dedup/validate/balance/split/build_evaluation_datasets all ran successfully once on this data (see below for the bug hit and fixed during that run)
- Phase 3b (NEW): targeted top-up generation for underrepresented combos IN PROGRESS — 29/71 accepted, 1 rejected (clean generation-failure skip), blocked at item 31 on all-3-keys-daily-exhausted, progress saved via progress_v1.0_topup.json, safe to resume with same command
- Phase 6: DONE (unchanged from before)
- Phase 7: DONE in self-test mode only (unchanged) — REAL run still pending until top-up + full QC re-run complete
- Frontend stack: React + Vite + Tailwind + Framer Motion + Recharts
- Base model: Qwen2.5-3B
- Fine-tuning method: QLoRA (4-bit)

## Key decisions locked in
- (all prior decisions unchanged — GPU/Colab choice, 3 Groq accounts, GROQ_MODEL=openai/gpt-oss-120b, json_schema strict mode, max_retries=0, TPD is org-level, JSONL-then-CSV raw format, resume-safe generate_tickets.py, rejected templated-data shortcut, SQLite dev DB, ₹0 runtime cost target, single main branch only, Colab bootstrap sequence, triton==2.3.0 fix, hardware_check.py CUDA-suffix fix)
- SECURITY NOTE: 3 real Groq API keys were pasted in plaintext into an earlier chat session. .env confirmed never committed to git. Rotate keys when convenient — still not urgent (no git-history exposure).
- BUG FIXED (2026-08-19): split_dataset.py's all_fields list for master_dataset.csv was missing "generation_source", causing a crash partway through Phase 5 (which then cascaded into build_evaluation_datasets.py failing with FileNotFoundError since test.csv never got written). Fixed by adding "generation_source" to the fieldnames list. Committed and pushed. Full 5-step pipeline then ran successfully end-to-end for the first time.
- Dataset balance decision (2026-08-19): reviewed reports/dataset_report.md — single-axis distributions (category/priority/department) were all healthy (8.4%-39.4% range); only the fine-grained 3-way category x priority x department combo analysis showed severe imbalance (224x, driven by naturally rare combos like "Refund+Critical+Finance"=1). validate_generated_data.py's suspicious-combo cross-check found 0 suspicious combos, confirming these rare combos are legitimate, not generation errors. Decision: do a SMALL TARGETED top-up (not full rebalancing) for only the 9 worst combos (count <5), bringing each up to a floor of ~10, rather than forcing full parity across all 37 combos — consistent with Section 19 "realistic, not forced".
- New file added: data_generation/generate_topup.py — standalone targeted top-up script, reuses existing groq_client.py/schemas.py/scenario_plan.py (specifically SCENARIOS and DIFFICULTY_WEIGHTS, and confirmed all target combos are within scenario_plan.py's own LEGITIMATE_CROSS_DEPARTMENT mapping, so no new "suspicious" combos are being introduced). APPENDS directly to the existing data/raw/tickets_v1.0.jsonl (does not create a separate file/version) so the standard 5-step QC pipeline can just be re-run once on the combined data. Has its OWN separate progress file (progress_v1.0_topup.json), independent of the main generation's resume state, so it can be safely interrupted/resumed without touching main-generation progress tracking. Uses RANDOM_SEED+999 as a distinct sub-seed from main generation.
- Top-up targets (9 combos, ~71 new tickets planned): General/Low/Account (+9), Refund/Critical/Finance (+9), Billing/Critical/Refunds (+9), General/Medium/Finance (+9), General/Medium/Refunds (+8), General/Low/Finance (+8), Account/Low/Technical (+6), Refund/High/Finance (+6), Refund/Low/Finance (+7).

## Repo state (as of last commit)
- All Phase 6/7 state unchanged from before.
- data_generation/split_dataset.py — BUGFIXED (generation_source field), committed and pushed.
- data_generation/generate_topup.py — NEW, written, committed, pushed. Run once so far, partially complete (29/71).
- data/raw/tickets_v1.0.jsonl — now contains original 1975 records PLUS 29 top-up records appended (30 total generation attempts, 1 rejected) = 2004 raw records currently on disk, pending completion of remaining ~41 top-up items before re-running QC.
- data/manifests/progress_v1.0_topup.json — exists, tracks top-up resume point (next_index=31, accepted=29, rejected=1). Do NOT delete.
- IMPORTANT: data/processed/master_dataset.csv, data/splits/*.csv, data/future_testing/future_test.csv, and all data/evaluation/*.csv + data/demo/*.csv currently reflect the OLD 1975-record dataset (pre-top-up) — these are now STALE and must NOT be used for training. They will be regenerated once top-up completes and the full 5-step QC pipeline is re-run.
- reports/dataset_report.md — currently reflects the OLD pre-top-up balance analysis (224x imbalance) — will be regenerated and should show improved combo counts once top-up completes and validate/balance are re-run.
- training/prepared/{train,validation,test}/ — still contain ONLY self-test dummy data from earlier session, unchanged, still must be regenerated for real later.

## Environment notes
- GPU available locally: yes, RTX 2050 4GB, NOT used for training (Colab T4 confirmed working in a prior session; will need re-bootstrap next Colab session per standard sequence).
- Groq accounts: all 3 daily-quota-exhausted AGAIN as of this top-up run (2026-08-19) — expected, since main generation had already used most of the day's quota before top-up was attempted right after.

## Open issues / blockers
- BLOCKED: waiting for Groq daily quota reset (again) before top-up generation can finish (29/71 done, ~41 remaining, 1 already legitimately rejected).
- Once top-up finishes: MUST re-run the FULL 5-step QC pipeline from scratch (not incrementally) in this exact order: deduplicate.py -> validate_generated_data.py -> balance_dataset.py -> split_dataset.py -> build_evaluation_datasets.py. This regenerates all splits/eval/demo files against the combined ~2045-record dataset.
- After QC re-run: paste new reports/dataset_report.md back for review — confirm the 9 targeted combos actually improved and no new issues appeared — before treating the dataset as final.
- Only after dataset is confirmed final: re-run training/prepare_dataset.py in Colab WITHOUT --self-test for the first real run, then genuinely begin Phase 8 (QLoRA training script + config + actual training run) — Phase 8 has NOT been started or written yet.
- Groq API keys still exposed in earlier chat session — rotate when convenient (low urgency, unchanged).

## Next action
1. Wait for Groq quota reset, then re-run: `python data_generation\generate_topup.py` (auto-resumes from item 31/71).
2. Once it prints `DONE. accepted=~70 rejected=~1`, run the full 5-step QC pipeline in order (commands listed above / in the script's own final printout).
3. Paste the new reports\dataset_report.md back to Claude for review before proceeding.
4. Re-bootstrap a Colab session (standard sequence: GPU runtime, mount Drive, git pull, pip install -r training/requirements-colab.txt triton==2.3.0, hardware_check.py), then run `python training/prepare_dataset.py` WITHOUT --self-test against the real final splits, confirm output.
5. Begin Phase 8 (QLoRA training) — write train.py, LoRA config, training args, checkpointing, adapter saving. Not yet started.
6. Rotate the 3 Groq API keys when convenient.
7. git push the current repo state before ending any session.