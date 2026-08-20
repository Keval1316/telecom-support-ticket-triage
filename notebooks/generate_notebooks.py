"""
Script to generate Phase 7 and Phase 8 Colab .ipynb files.
Run: python notebooks/generate_notebooks.py
"""
import json
from pathlib import Path


def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src}


def code(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": src}


def make_nb(name, cells):
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10.0"},
            "accelerator": "GPU",
            "colab": {"provenance": [], "gpuType": "T4", "name": name},
        },
        "cells": cells,
    }


# ===========================================================================
# PHASE 7 NOTEBOOK
# ===========================================================================

P7_CELLS = [
    md(
        "# Phase 7 - Dataset Preparation for QLoRA Fine-Tuning\n"
        "\n"
        "Tokenize real train/val/test CSVs using Qwen2.5-3B tokenizer.\n"
        "Loss computed **ONLY on the assistant JSON** response — prompt is masked with `-100`.\n"
        "\n"
        "## Prerequisites\n"
        "1. **Runtime → Change runtime type → T4 GPU**\n"
        "2. Google Drive mounted with repo present\n"
        "3. `data/splits/{train,validation,test}.csv` exist (Phase 5 done)\n"
        "4. `models/base/Qwen2.5-3B/` downloaded (Phase 6 done)\n"
        "\n"
        "**Run cells in order. Do not skip.**"
    ),
    code(
        "# Cell 1 - Mount Google Drive\n"
        "from google.colab import drive\n"
        "drive.mount('/content/drive')\n"
        "print('Drive mounted.')"
    ),
    code(
        "# Cell 2 - Set REPO_DIR\n"
        "# Adjust to where your repo lives on Drive:\n"
        "#   /content/drive/MyDrive/telecom-support-ticket-triage\n"
        "#   /content/drive/MyDrive/GenAI-Projects/telecom-support-ticket-triage\n"
        "import os\n"
        "REPO_DIR = '/content/drive/MyDrive/telecom-support-ticket-triage'\n"
        "assert os.path.isdir(REPO_DIR), 'REPO_DIR not found: ' + REPO_DIR\n"
        "os.chdir(REPO_DIR)\n"
        "print('Working dir:', os.getcwd())\n"
        "print('Repo contents:', os.listdir('.'))"
    ),
    code(
        "# Cell 3 - Git pull latest changes\n"
        "!git pull\n"
        "!git log --oneline -5"
    ),
    code(
        "# Cell 4 - Install training dependencies\n"
        "# triton==2.3.0 is pinned to fix known Colab T4 incompatibility\n"
        "!pip install -q -r training/requirements-colab.txt\n"
        "!pip install -q triton==2.3.0\n"
        "print('Installation complete.')"
    ),
    code(
        "# Cell 5 - Hardware check\n"
        "import torch\n"
        "import transformers, peft, trl, bitsandbytes, datasets, accelerate\n"
        "print('PyTorch:     ', torch.__version__)\n"
        "print('Transformers:', transformers.__version__)\n"
        "print('PEFT:        ', peft.__version__)\n"
        "print('TRL:         ', trl.__version__)\n"
        "print('bitsandbytes:', bitsandbytes.__version__)\n"
        "print('datasets:    ', datasets.__version__)\n"
        "print('accelerate:  ', accelerate.__version__)\n"
        "print()\n"
        "print('CUDA available:', torch.cuda.is_available())\n"
        "if torch.cuda.is_available():\n"
        "    print('GPU: ', torch.cuda.get_device_name(0))\n"
        "    vram = torch.cuda.get_device_properties(0).total_memory / 1e9\n"
        "    print('VRAM:', round(vram, 1), 'GB')\n"
        "else:\n"
        "    print('WARNING: No GPU. Switch to T4 before Phase 8 training.')"
    ),
    code(
        "# Cell 6 - Verify prerequisite files exist\n"
        "from pathlib import Path\n"
        "import csv\n"
        "missing = []\n"
        "for split in ['train.csv', 'validation.csv', 'test.csv']:\n"
        "    p = Path('data/splits') / split\n"
        "    if not p.exists():\n"
        "        missing.append(str(p))\n"
        "        print('MISSING:', p)\n"
        "    else:\n"
        "        with open(p, encoding='utf-8') as f:\n"
        "            rows = list(csv.DictReader(f))\n"
        "        print(split + ':', len(rows), 'rows')\n"
        "model_dir = Path('models/base/Qwen2.5-3B')\n"
        "if not model_dir.exists():\n"
        "    missing.append(str(model_dir))\n"
        "    print('MISSING: models/base/Qwen2.5-3B - download Phase 6 base model first')\n"
        "else:\n"
        "    print('Base model:', len(list(model_dir.iterdir())), 'files found')\n"
        "if not missing:\n"
        "    print('All prerequisites OK.')"
    ),
    code(
        "# Cell 7 - Run prepare_dataset.py (REAL run - no --self-test flag)\n"
        "# Tokenizes all 3 splits, saves to training/prepared/{train,validation,test}/\n"
        "# Runtime: ~2-5 minutes on CPU\n"
        "!python training/prepare_dataset.py \\\n"
        "    --model-path models/base/Qwen2.5-3B \\\n"
        "    --max-length 512"
    ),
    code(
        "# Cell 8 - Verify output: counts + label masking check\n"
        "from datasets import load_from_disk\n"
        "from pathlib import Path\n"
        "all_ok = True\n"
        "for name in ['train', 'validation', 'test']:\n"
        "    path = Path('training/prepared') / name\n"
        "    if not path.exists():\n"
        "        print('ERROR: not found -', path)\n"
        "        all_ok = False\n"
        "        continue\n"
        "    ds = load_from_disk(str(path))\n"
        "    ex = ds[0]\n"
        "    n_masked = sum(1 for l in ex['labels'] if l == -100)\n"
        "    n_loss   = len(ex['labels']) - n_masked\n"
        "    ok = n_loss > 0 and n_masked > 0\n"
        "    if not ok:\n"
        "        all_ok = False\n"
        "    status = 'OK' if ok else 'FAIL'\n"
        "    print(name + ': ' + str(len(ds)) + ' examples | masked=' + str(n_masked) + ' loss_tokens=' + str(n_loss) + ' | ' + status)\n"
        "print()\n"
        "print('Phase 7 verification:', 'PASSED' if all_ok else 'FAILED - fix errors above')"
    ),
    code(
        "# Cell 9 - Decode first training example for human review\n"
        "from datasets import load_from_disk\n"
        "from transformers import AutoTokenizer\n"
        "import json\n"
        "tok = AutoTokenizer.from_pretrained('models/base/Qwen2.5-3B')\n"
        "ds  = load_from_disk('training/prepared/train')\n"
        "ex  = ds[0]\n"
        "full_text  = tok.decode(ex['input_ids'], skip_special_tokens=False)\n"
        "label_ids  = [t for t in ex['labels'] if t != -100]\n"
        "label_text = tok.decode(label_ids, skip_special_tokens=True)\n"
        "print('=== FULL INPUT (first 1200 chars) ===')\n"
        "print(full_text[:1200])\n"
        "print('\\n=== LABEL (what model learns to predict) ===')\n"
        "print(label_text)\n"
        "try:\n"
        "    parsed = json.loads(label_text.strip())\n"
        "    assert all(k in parsed for k in ['category', 'priority', 'department'])\n"
        "    print('\\nLabel JSON VALID:', parsed)\n"
        "except Exception as e:\n"
        "    print('\\nWARNING: label not valid JSON:', e)"
    ),
    code(
        "# Cell 10 - Token length distribution (validates max_length=512 choice)\n"
        "from datasets import load_from_disk\n"
        "import numpy as np\n"
        "ds = load_from_disk('training/prepared/train')\n"
        "lens = [len(ex['input_ids']) for ex in ds]\n"
        "print('min:', min(lens), ' max:', max(lens), ' mean:', round(float(np.mean(lens)), 1))\n"
        "print('p95:', round(float(np.percentile(lens, 95)), 1), ' p99:', round(float(np.percentile(lens, 99)), 1))\n"
        "trunc = sum(1 for l in lens if l == 512)\n"
        "pct   = trunc / len(lens) * 100\n"
        "print('Truncated at max_length=512:', trunc, '(' + str(round(pct, 1)) + '%)')\n"
        "if pct > 5:\n"
        "    print('RECOMMENDATION: >5% truncated.')\n"
        "    print('Re-run Cell 7 with --max-length 768, then update Phase 8 train command too.')\n"
        "else:\n"
        "    print('max_length=512 is adequate for this dataset.')"
    ),
    code(
        "# Cell 11 - Save metadata JSON + git commit\n"
        "# Binary HF arrow files are NOT committed (too large).\n"
        "# meta.json is small and tracks stats for future sessions.\n"
        "import json\n"
        "import numpy as np\n"
        "from datasets import load_from_disk\n"
        "from pathlib import Path\n"
        "meta = {}\n"
        "for name in ['train', 'validation', 'test']:\n"
        "    ds   = load_from_disk('training/prepared/' + name)\n"
        "    lens = [len(ex['input_ids']) for ex in ds]\n"
        "    meta[name] = {\n"
        "        'num_examples': len(ds),\n"
        "        'columns': ds.column_names,\n"
        "        'token_length_mean': round(float(np.mean(lens)), 1),\n"
        "        'token_length_max': int(max(lens)),\n"
        "        'token_length_p95': round(float(np.percentile(lens, 95)), 1),\n"
        "        'truncated_at_512': int(sum(1 for l in lens if l == 512)),\n"
        "    }\n"
        "p = Path('training/prepared/meta.json')\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        "p.write_text(json.dumps(meta, indent=2), encoding='utf-8')\n"
        "print(json.dumps(meta, indent=2))\n"
        "!git add training/prepared/meta.json\n"
        "!git commit -m 'Phase 7 complete: prepared dataset metadata'\n"
        "!git push\n"
        "print('\\nPHASE 7 COMPLETE')\n"
        "print('Next: open notebooks/phase8_train.ipynb and run training.')"
    ),
]

# ===========================================================================
# PHASE 8 NOTEBOOK
# ===========================================================================

P8_CELLS = [
    md(
        "# Phase 8 - QLoRA Fine-Tuning of Qwen2.5-3B\n"
        "\n"
        "**This notebook trains the model. Expected time: 45-90 minutes on T4.**\n"
        "\n"
        "What happens:\n"
        "1. Loads Qwen2.5-3B base in 4-bit NF4 quantization\n"
        "2. Applies LoRA (rank=16, alpha=32) on all 7 projection layers\n"
        "3. Trains for 3 epochs with cosine LR + paged_adamw_8bit optimizer\n"
        "4. Saves the LoRA adapter to `models/adapters/telecom-ticket-triage/`\n"
        "\n"
        "**The adapter is ~60 MB (committed to git). The base model (~6 GB) stays on Drive.**\n"
        "\n"
        "## Prerequisites\n"
        "- Phase 7 complete (`training/prepared/{train,validation,test}/` exist on Drive)\n"
        "- **T4 GPU runtime** (required for 4-bit model + LoRA training)\n"
        "\n"
        "**Run cells in order.**"
    ),
    code(
        "# Cell 1 - Mount Drive\n"
        "from google.colab import drive\n"
        "drive.mount('/content/drive')\n"
        "print('Drive mounted.')"
    ),
    code(
        "# Cell 2 - Set REPO_DIR\n"
        "import os\n"
        "REPO_DIR = '/content/drive/MyDrive/telecom-support-ticket-triage'\n"
        "assert os.path.isdir(REPO_DIR), 'REPO_DIR not found: ' + REPO_DIR\n"
        "os.chdir(REPO_DIR)\n"
        "print('Working dir:', os.getcwd())"
    ),
    code(
        "# Cell 3 - Git pull\n"
        "!git pull\n"
        "!git log --oneline -5"
    ),
    code(
        "# Cell 4 - Install dependencies\n"
        "!pip install -q -r training/requirements-colab.txt\n"
        "!pip install -q triton==2.3.0\n"
        "print('Done.')"
    ),
    code(
        "# Cell 5 - GPU check (MUST have GPU for training)\n"
        "import torch\n"
        "if not torch.cuda.is_available():\n"
        "    raise RuntimeError('NO GPU DETECTED. Go to Runtime -> Change runtime type -> T4 GPU, then re-run all cells.')\n"
        "print('GPU: ', torch.cuda.get_device_name(0))\n"
        "print('VRAM:', round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1), 'GB')"
    ),
    code(
        "# Cell 6 - Verify Phase 7 prepared datasets exist\n"
        "from pathlib import Path\n"
        "import json\n"
        "prepared_dir = Path('training/prepared')\n"
        "meta_file = prepared_dir / 'meta.json'\n"
        "if meta_file.exists():\n"
        "    meta = json.loads(meta_file.read_text())\n"
        "    print('Phase 7 metadata:')\n"
        "    print(json.dumps(meta, indent=2))\n"
        "all_ok = True\n"
        "for name in ['train', 'validation', 'test']:\n"
        "    path = prepared_dir / name\n"
        "    if not path.exists():\n"
        "        print('MISSING:', path)\n"
        "        all_ok = False\n"
        "if not all_ok:\n"
        "    raise RuntimeError('Prepared datasets missing. Run Phase 7 notebook first.')\n"
        "print('All prepared datasets found. Ready to train.')"
    ),
    code(
        "# Cell 7 - RUN TRAINING\n"
        "# train.py: loads base model -> applies LoRA -> trains 3 epochs -> saves adapter\n"
        "# Estimated runtime on T4: 45-90 minutes\n"
        "# Watch for: loss decreasing each epoch, eval_loss lower than train_loss\n"
        "# Best checkpoint (lowest eval_loss) is automatically reloaded at the end\n"
        "!python training/train.py \\\n"
        "    --model-path models/base/Qwen2.5-3B \\\n"
        "    --max-length 512 \\\n"
        "    --epochs 3 \\\n"
        "    --batch-size 2 \\\n"
        "    --grad-accum 8 \\\n"
        "    --learning-rate 2e-4 \\\n"
        "    --lora-rank 16 \\\n"
        "    --lora-alpha 32 \\\n"
        "    --output-dir models/adapters/telecom-ticket-triage\n"
        "# NOTE: If Cell 10 in Phase 7 showed >5% truncation, add: --max-length 768"
    ),
    code(
        "# Cell 8 - Review training metrics\n"
        "import json\n"
        "from pathlib import Path\n"
        "log_path = Path('training/training_log.json')\n"
        "if not log_path.exists():\n"
        "    print('training_log.json not found - check if Cell 7 completed successfully.')\n"
        "else:\n"
        "    log = json.loads(log_path.read_text())\n"
        "    print('=== Training metrics ===')\n"
        "    for k, v in log.get('train_metrics', {}).items():\n"
        "        val = round(v, 4) if isinstance(v, float) else v\n"
        "        print(' ', k, ':', val)\n"
        "    print()\n"
        "    print('=== Final eval metrics (best checkpoint) ===')\n"
        "    for k, v in log.get('eval_metrics', {}).items():\n"
        "        val = round(v, 4) if isinstance(v, float) else v\n"
        "        print(' ', k, ':', val)"
    ),
    code(
        "# Cell 9 - Verify adapter files were saved\n"
        "from pathlib import Path\n"
        "adapter_dir = Path('models/adapters/telecom-ticket-triage')\n"
        "if not adapter_dir.exists():\n"
        "    print('ERROR: adapter dir not found. Check Cell 7 output for errors.')\n"
        "else:\n"
        "    files = list(adapter_dir.iterdir())\n"
        "    print('Adapter directory:', len(files), 'files')\n"
        "    for f in sorted(files):\n"
        "        print(' ', f.name, '-', round(f.stat().st_size / 1024, 1), 'KB')\n"
        "    meta_f = adapter_dir / 'triage_adapter_meta.json'\n"
        "    if meta_f.exists():\n"
        "        import json\n"
        "        print('\\nAdapter meta:', json.loads(meta_f.read_text()))"
    ),
    code(
        "# Cell 10 - Inference smoke test\n"
        "# Loads base model + LoRA adapter and runs one test ticket.\n"
        "# MUST produce valid JSON {category, priority, department} before proceeding to Phase 9.\n"
        "import torch, json\n"
        "from pathlib import Path\n"
        "from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig\n"
        "from peft import PeftModel\n"
        "\n"
        "BASE_PATH    = 'models/base/Qwen2.5-3B'\n"
        "ADAPTER_PATH = 'models/adapters/telecom-ticket-triage'\n"
        "\n"
        "SYSTEM = (\n"
        "    'You are a support-ticket triage classifier for a telecom company. '\n"
        "    'Given a customer support ticket, respond with ONLY a strict JSON object '\n"
        "    'with exactly these keys: \"category\", \"priority\", \"department\". '\n"
        "    'No explanation, no extra text, no markdown fences.\\n\\n'\n"
        "    'category must be one of: Billing, Technical, Account, Refund, General\\n'\n"
        "    'priority must be one of: Critical, High, Medium, Low\\n'\n"
        "    'department must be one of: Finance, Technical, Account, Refunds, General Support'\n"
        ")\n"
        "TICKET = 'My mobile data stopped working completely since yesterday morning. Tried restarting and reinserting SIM. Nothing helped. Need this fixed urgently as I use data for work.'\n"
        "\n"
        "print('Loading tokenizer...')\n"
        "tok = AutoTokenizer.from_pretrained(BASE_PATH)\n"
        "if tok.pad_token is None:\n"
        "    tok.pad_token = tok.eos_token\n"
        "\n"
        "bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',\n"
        "    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)\n"
        "\n"
        "print('Loading base model in 4-bit...')\n"
        "base = AutoModelForCausalLM.from_pretrained(BASE_PATH, quantization_config=bnb,\n"
        "    device_map='auto', trust_remote_code=True)\n"
        "\n"
        "print('Loading LoRA adapter...')\n"
        "model = PeftModel.from_pretrained(base, ADAPTER_PATH)\n"
        "model.eval()\n"
        "\n"
        "msgs = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': TICKET}]\n"
        "prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)\n"
        "inputs = tok(prompt, return_tensors='pt').to(model.device)\n"
        "\n"
        "print('Running inference...')\n"
        "with torch.no_grad():\n"
        "    out = model.generate(**inputs, max_new_tokens=64, do_sample=False,\n"
        "        pad_token_id=tok.eos_token_id)\n"
        "\n"
        "generated = out[0][inputs['input_ids'].shape[1]:]\n"
        "response  = tok.decode(generated, skip_special_tokens=True).strip()\n"
        "print('\\nModel output:', response)\n"
        "\n"
        "try:\n"
        "    p = json.loads(response)\n"
        "    cats  = {'Billing','Technical','Account','Refund','General'}\n"
        "    pris  = {'Critical','High','Medium','Low'}\n"
        "    depts = {'Finance','Technical','Account','Refunds','General Support'}\n"
        "    assert p.get('category') in cats, 'Bad category: ' + str(p.get('category'))\n"
        "    assert p.get('priority') in pris, 'Bad priority: ' + str(p.get('priority'))\n"
        "    assert p.get('department') in depts, 'Bad dept: ' + str(p.get('department'))\n"
        "    print('\\nInference test PASSED:')\n"
        "    print('  category:  ', p['category'])\n"
        "    print('  priority:  ', p['priority'])\n"
        "    print('  department:', p['department'])\n"
        "except Exception as e:\n"
        "    print('\\nInference test FAILED:', e)\n"
        "    print('Model may need more training or output format needs review.')"
    ),
    code(
        "# Cell 11 - Git commit adapter metadata + training log\n"
        "# adapter_model.safetensors is excluded from git by .gitignore (*safetensors)\n"
        "# We commit: triage_adapter_meta.json, adapter_config.json, tokenizer files, training_log.json\n"
        "!git add models/adapters/telecom-ticket-triage/triage_adapter_meta.json\n"
        "!git add models/adapters/telecom-ticket-triage/adapter_config.json\n"
        "!git add models/adapters/telecom-ticket-triage/tokenizer.json\n"
        "!git add models/adapters/telecom-ticket-triage/tokenizer_config.json\n"
        "!git add models/adapters/telecom-ticket-triage/special_tokens_map.json\n"
        "!git add training/training_log.json\n"
        "!git status\n"
        "!git commit -m 'Phase 8 complete: QLoRA adapter trained and saved'\n"
        "!git push\n"
        "print('\\nPHASE 8 COMPLETE')\n"
        "print('The LoRA adapter weights (adapter_model.safetensors) stay on Drive only.')\n"
        "print('Next: run Phase 9 (evaluate.py) to measure test set accuracy and F1.')"
    ),
]

# Write files
nb_dir = Path("notebooks")
nb_dir.mkdir(exist_ok=True)

p7_path = nb_dir / "phase7_prepare_dataset.ipynb"
p8_path = nb_dir / "phase8_train.ipynb"

p7_path.write_text(json.dumps(make_nb("Phase7_PrepareDataset.ipynb", P7_CELLS), indent=1), encoding="utf-8")
p8_path.write_text(json.dumps(make_nb("Phase8_Train.ipynb", P8_CELLS), indent=1), encoding="utf-8")

print(f"Written: {p7_path}")
print(f"Written: {p8_path}")
