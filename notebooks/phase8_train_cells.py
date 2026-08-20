# ==============================================================================
# Phase 8 Colab Cells: QLoRA Fine-Tuning on T4 GPU
# ==============================================================================

# --- CELL 1: Execute QLoRA Training ---
"""
!python training/train.py \
    --model-path models/base/Qwen2.5-3B \
    --max-length 512 \
    --epochs 3 \
    --batch-size 2 \
    --grad-accum 8 \
    --learning-rate 2e-4 \
    --lora-rank 16 \
    --lora-alpha 32 \
    --output-dir models/adapters/telecom-ticket-triage
"""

# --- CELL 2: Review Training Log ---
"""
import json
with open("training/training_log.json", "r") as f:
    log_data = json.load(f)
print(json.dumps(log_data, indent=2))
"""

# --- CELL 3: Smoke Test Inference with Adapter ---
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
base_path = "models/base/Qwen2.5-3B"
adapter_path = "models/adapters/telecom-ticket-triage"

tokenizer = AutoTokenizer.from_pretrained(base_path)
model = AutoModelForCausalLM.from_pretrained(
    base_path,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
model = PeftModel.from_pretrained(model, adapter_path)
model.eval()

test_prompt = [
    {"role": "system", "content": "You are a support-ticket triage classifier for a telecom company. Given a customer support ticket, respond with ONLY a strict JSON object with exactly these keys: \"category\", \"priority\", \"department\". No explanation, no extra text, no markdown fences."},
    {"role": "user", "content": "My fiber broadband connection is completely dead since yesterday. Red light blinking on router. Need urgent fix as I work from home."}
]
input_text = tokenizer.apply_chat_template(test_prompt, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(input_text, return_tensors="pt").to("cuda")

with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=64, do_sample=False)
gen_text = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print("Model Output:\n", gen_text)
"""
