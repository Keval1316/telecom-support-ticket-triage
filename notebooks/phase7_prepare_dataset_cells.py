# =============================================================================
# PHASE 7 COLAB NOTEBOOK - Copy each block into a separate Colab cell
# =============================================================================

# ------ CELL 1: Mount Drive ------
from google.colab import drive
drive.mount("/content/drive")
print("Drive mounted.")

# ------ CELL 2: Set REPO_DIR ------
import os
# Adjust to where your repo lives on Drive:
REPO_DIR = "/content/drive/MyDrive/telecom-support-ticket-triage"
assert os.path.isdir(REPO_DIR), f"REPO_DIR not found: {REPO_DIR}"
os.chdir(REPO_DIR)
print(f"Working dir: {os.getcwd()}")
print("Contents:", os.listdir("."))

# ------ CELL 3: Git pull ------
# !git pull
# !git log --oneline -5

# ------ CELL 4: Install deps ------
# !pip install -q -r training/requirements-colab.txt
# !pip install -q triton==2.3.0

# ------ CELL 5: Hardware check ------
import torch
import transformers, peft, trl, bitsandbytes, datasets, accelerate
print(f"PyTorch:      {torch.__version__}")
print(f"Transformers: {transformers.__version__}")
print(f"PEFT:         {peft.__version__}")
print(f"TRL:          {trl.__version__}")
print(f"bitsandbytes: {bitsandbytes.__version__}")
print(f"datasets:     {datasets.__version__}")
print(f"accelerate:   {accelerate.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")

# ------ CELL 6: Verify prerequisites ------
from pathlib import Path
import csv
for split in ["train.csv", "validation.csv", "test.csv"]:
    p = Path("data/splits") / split
    if not p.exists():
        print(f"MISSING: {p}")
    else:
        with open(p, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        print(f"{split}: {len(rows)} rows")
model_dir = Path("models/base/Qwen2.5-3B")
print(f"Base model: {len(list(model_dir.iterdir()))} files" if model_dir.exists() else f"MISSING: {model_dir}")

# ------ CELL 7: Run prepare_dataset.py (REAL run) ------
# !python training/prepare_dataset.py --model-path models/base/Qwen2.5-3B --max-length 512

# ------ CELL 8: Verify output ------
from datasets import load_from_disk
all_ok = True
for name in ["train", "validation", "test"]:
    path = Path(f"training/prepared/{name}")
    if not path.exists():
        print(f"ERROR: {path} not found"); all_ok = False; continue
    ds = load_from_disk(str(path))
    ex = ds[0]
    n_masked = sum(1 for l in ex["labels"] if l == -100)
    n_loss   = len(ex["labels"]) - n_masked
    ok = n_loss > 0 and n_masked > 0
    if not ok: all_ok = False
    status = "OK" if ok else "FAIL"
    print(f"{name}: {len(ds)} examples | masked={n_masked} loss_tokens={n_loss} | masking={status}")
print("Phase 7:", "PASSED" if all_ok else "FAILED")

# ------ CELL 9: Decode first example ------
from datasets import load_from_disk
from transformers import AutoTokenizer
import json
tok = AutoTokenizer.from_pretrained("models/base/Qwen2.5-3B")
ds = load_from_disk("training/prepared/train")
ex = ds[0]
full_text  = tok.decode(ex["input_ids"], skip_special_tokens=False)
label_ids  = [t for t in ex["labels"] if t != -100]
label_text = tok.decode(label_ids, skip_special_tokens=True)
print("=== FULL INPUT ===")
print(full_text[:1500])
print("\n=== LABEL ===")
print(label_text)
try:
    parsed = json.loads(label_text.strip())
    assert all(k in parsed for k in ["category","priority","department"])
    print(f"\nLabel JSON valid: {parsed}")
except Exception as e:
    print(f"\nWARNING: {e}")

# ------ CELL 10: Token length distribution ------
from datasets import load_from_disk
import numpy as np
ds = load_from_disk("training/prepared/train")
lengths = [len(ex["input_ids"]) for ex in ds]
print(f"min={min(lengths)} max={max(lengths)} mean={np.mean(lengths):.1f} median={np.median(lengths):.1f}")
print(f"p95={np.percentile(lengths,95):.1f} p99={np.percentile(lengths,99):.1f}")
trunc = sum(1 for l in lengths if l == 512)
pct   = trunc/len(lengths)*100
print(f"Truncated at 512: {trunc} ({pct:.1f}%)")
if pct > 5:
    print("RECOMMENDATION: re-run with --max-length 768, update MAX_SEQUENCE_LENGTH in train.py")
else:
    print("max_length=512 adequate.")

# ------ CELL 11: Save metadata + git commit ------
import json, numpy as np
from datasets import load_from_disk
from pathlib import Path
meta = {}
for name in ["train", "validation", "test"]:
    ds   = load_from_disk(f"training/prepared/{name}")
    lens = [len(ex["input_ids"]) for ex in ds]
    meta[name] = {
        "num_examples": len(ds),
        "columns": ds.column_names,
        "token_length_mean": round(float(np.mean(lens)), 1),
        "token_length_max": int(max(lens)),
        "token_length_p95": round(float(np.percentile(lens, 95)), 1),
        "truncated_at_512": int(sum(1 for l in lens if l == 512)),
    }
p = Path("training/prepared/meta.json")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(meta, indent=2), encoding="utf-8")
print(json.dumps(meta, indent=2))
# !git add training/prepared/meta.json
# !git commit -m "Phase 7 complete: prepared dataset metadata"
# !git push
print("\nPHASE 7 COMPLETE")
