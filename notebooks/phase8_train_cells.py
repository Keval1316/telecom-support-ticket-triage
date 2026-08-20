# =============================================================================
# PHASE 8 COLAB NOTEBOOK - Copy each block into a separate Colab cell
# Run cells in order. Assumes Phase 7 notebook was completed successfully.
# =============================================================================

# ====== PRE-FLIGHT: Confirm correct runtime ======
# Runtime -> Change runtime type -> T4 GPU
# Then Runtime -> Run all   (or run cells one by one)

# ------ CELL 1: Mount Drive ------
from google.colab import drive
drive.mount("/content/drive")
print("Drive mounted.")

# ------ CELL 2: Set REPO_DIR ------
import os
REPO_DIR = "/content/drive/MyDrive/telecom-support-ticket-triage"  # ADJUST IF NEEDED
assert os.path.isdir(REPO_DIR), f"REPO_DIR not found: {REPO_DIR}"
os.chdir(REPO_DIR)
print(f"Working dir: {os.getcwd()}")

# ------ CELL 3: Git pull ------
# !git pull
# !git log --oneline -5

# ------ CELL 4: Install deps ------
# !pip install -q -r training/requirements-colab.txt
# !pip install -q triton==2.3.0

# ------ CELL 5: Hardware check ------
import torch
import transformers, peft, trl, bitsandbytes
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU:  {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")
else:
    raise RuntimeError("NO GPU DETECTED. Switch to T4 runtime first.")

# ------ CELL 6: Verify Phase 7 prepared datasets exist ------
from pathlib import Path
import json

prepared_dir = Path("training/prepared")
meta_file = prepared_dir / "meta.json"
if meta_file.exists():
    meta = json.loads(meta_file.read_text())
    print("Phase 7 metadata found:")
    print(json.dumps(meta, indent=2))
else:
    print("WARNING: training/prepared/meta.json not found.")
    print("Phase 7 may not be complete, or was run in a different session.")

all_ok = True
for name in ["train", "validation", "test"]:
    path = prepared_dir / name
    if not path.exists():
        print(f"MISSING: {path}")
        all_ok = False
    else:
        from datasets import load_from_disk
        ds = load_from_disk(str(path))
        print(f"{name}: {len(ds)} examples")

if not all_ok:
    raise RuntimeError("Prepared datasets missing. Run Phase 7 notebook first, then re-run Phase 8.")

# ------ CELL 7: Run train.py ------
# This is the full training run. Expected time on T4:
#   - 3 epochs on 1,288 examples with bs=2, grad_acc=8
#   - ~480 steps/epoch => ~1,440 total steps
#   - Estimated: 45-90 minutes depending on sequence length
#
# Monitor: logging_steps=10 prints loss every 10 steps.
# The best checkpoint (lowest eval_loss) is auto-reloaded at end.
# The LoRA adapter is saved to models/adapters/telecom-ticket-triage/

# !python training/train.py \
#     --model-path models/base/Qwen2.5-3B \
#     --max-length 512 \
#     --epochs 3 \
#     --batch-size 2 \
#     --grad-accum 8 \
#     --learning-rate 2e-4 \
#     --lora-rank 16 \
#     --lora-alpha 32 \
#     --output-dir models/adapters/telecom-ticket-triage

# If Cell 10 in Phase 7 showed >5% truncation, replace --max-length 512 with --max-length 768

# ------ CELL 8: Check training_log.json ------
import json
from pathlib import Path
log_path = Path("training/training_log.json")
if log_path.exists():
    log = json.loads(log_path.read_text())
    print("Training complete. Key metrics:")
    for k, v in log.get("train_metrics", {}).items():
        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
    print("\nFinal eval metrics (best checkpoint):")
    for k, v in log.get("eval_metrics", {}).items():
        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
else:
    print("training_log.json not found - training may not have completed.")

# ------ CELL 9: Verify adapter files ------
adapter_dir = Path("models/adapters/telecom-ticket-triage")
if adapter_dir.exists():
    files = list(adapter_dir.iterdir())
    print(f"Adapter directory: {len(files)} files")
    for f in sorted(files):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name}  ({size_kb:.1f} KB)")
    
    # Check triage_adapter_meta.json
    meta_f = adapter_dir / "triage_adapter_meta.json"
    if meta_f.exists():
        print("\nAdapter meta:")
        print(meta_f.read_text())
else:
    print(f"ERROR: {adapter_dir} not found - check training logs above.")

# ------ CELL 10: Quick inference test with the adapter ------
# Loads base model + adapter and runs one test ticket to confirm the model
# produces valid JSON output. This is a smoke test, not a full evaluation.
import torch, json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_PATH    = "models/base/Qwen2.5-3B"
ADAPTER_PATH = "models/adapters/telecom-ticket-triage"

SYSTEM_PROMPT = (
    "You are a support-ticket triage classifier for a telecom company. "
    "Given a customer support ticket, respond with ONLY a strict JSON object "
    "with exactly these keys: \"category\", \"priority\", \"department\". "
    "No explanation, no extra text, no markdown fences.\n\n"
    "category must be one of: Billing, Technical, Account, Refund, General\n"
    "priority must be one of: Critical, High, Medium, Low\n"
    "department must be one of: Finance, Technical, Account, Refunds, General Support"
)

TEST_TICKET = "My mobile data stopped working completely since yesterday morning. I tried restarting the phone and reinserting the SIM but nothing helped. I need this fixed urgently as I use data for work."

print("Loading tokenizer...")
tok = AutoTokenizer.from_pretrained(BASE_PATH)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

print("Loading base model (4-bit)...")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_PATH,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model.eval()

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user",   "content": TEST_TICKET},
]
prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tok(prompt, return_tensors="pt").to(model.device)

print("\nRunning inference...")
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=64,
        do_sample=False,          # greedy decoding for structured output
        temperature=1.0,
        pad_token_id=tok.eos_token_id,
    )

generated = outputs[0][inputs["input_ids"].shape[1]:]
response  = tok.decode(generated, skip_special_tokens=True).strip()
print(f"\nModel output: {response}")

try:
    parsed = json.loads(response)
    valid_categories   = {"Billing", "Technical", "Account", "Refund", "General"}
    valid_priorities   = {"Critical", "High", "Medium", "Low"}
    valid_departments  = {"Finance", "Technical", "Account", "Refunds", "General Support"}
    
    assert parsed.get("category")   in valid_categories,  f"Bad category: {parsed.get('category')}"
    assert parsed.get("priority")   in valid_priorities,  f"Bad priority: {parsed.get('priority')}"
    assert parsed.get("department") in valid_departments, f"Bad department: {parsed.get('department')}"
    
    print(f"\nInference test PASSED:")
    print(f"  category:   {parsed['category']}")
    print(f"  priority:   {parsed['priority']}")
    print(f"  department: {parsed['department']}")
except (json.JSONDecodeError, AssertionError) as e:
    print(f"\nWARNING: Output validation failed: {e}")
    print("The model may need more epochs or the output format may need adjustment.")

# ------ CELL 11: Git commit adapter meta + training log ------
# !git add models/adapters/telecom-ticket-triage/triage_adapter_meta.json
# !git add training/training_log.json
# !git add training/train.py
# !git add notebooks/phase8_train_cells.py
# !git commit -m "Phase 8 complete: QLoRA adapter trained and saved"
# !git push
# print("\nPHASE 8 COMPLETE")
# print("Next: Phase 9 - run training/evaluate.py against the test split.")
