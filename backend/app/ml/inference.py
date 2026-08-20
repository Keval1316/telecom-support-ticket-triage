"""
Phase 12 - Local Inference Service for Telecom Ticket Triage.
Loads base model (Qwen2.5-3B) with fine-tuned LoRA adapter in 4-bit NF4 quantization.
Performs greedy inference, structured JSON extraction, confidence computation,
and applies Phase 11 safety escalation before returning final triage decisions.
Zero runtime Groq dependency (Rs 0 runtime inference).
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from backend.app.ml.priority_escalator import PriorityEscalator

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_BASE_MODEL = REPO_ROOT / "models" / "base" / "Qwen2.5-3B"
DEFAULT_ADAPTER_DIR = REPO_ROOT / "models" / "adapters" / "telecom-ticket-triage"

SYSTEM_PROMPT = (
    "You are a support-ticket triage classifier for a telecom company. "
    "Given a customer support ticket, respond with ONLY a strict JSON object "
    "with exactly these keys: \"category\", \"priority\", \"department\". "
    "No explanation, no extra text, no markdown fences.\n\n"
    "category must be one of: Billing, Technical, Account, Refund, General\n"
    "priority must be one of: Critical, High, Medium, Low\n"
    "department must be one of: Finance, Technical, Account, Refunds, General Support"
)


class TriageInferenceEngine:
    def __init__(
        self,
        base_model_path: Optional[str] = None,
        adapter_path: Optional[str] = None,
        confidence_threshold: float = 0.85,
        device_map: str = "auto",
    ):
        self.base_model_path = str(base_model_path or os.getenv("MODEL_PATH", DEFAULT_BASE_MODEL))
        self.adapter_path = str(adapter_path or os.getenv("ADAPTER_PATH", DEFAULT_ADAPTER_DIR))
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", confidence_threshold))
        self.escalator = PriorityEscalator()
        self.model = None
        self.tokenizer = None
        self._is_loaded = False
        self.device_map = device_map

    def load(self):
        """Loads tokenizer, 4-bit base model, and LoRA adapter."""
        if self._is_loaded:
            return

        print(f"[InferenceEngine] Loading tokenizer from: {self.base_model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Check CUDA availability
        has_cuda = torch.cuda.is_available()
        print(f"[InferenceEngine] CUDA available: {has_cuda}")

        if has_cuda:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            print(f"[InferenceEngine] Loading base model in 4-bit NF4...")
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                quantization_config=bnb_config,
                device_map=self.device_map,
                trust_remote_code=True,
            )
        else:
            print("[InferenceEngine] Loading base model on CPU (FP32/Float16 fallback)...")
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                torch_dtype=torch.float32,
                device_map="cpu",
                trust_remote_code=True,
            )

        adapter_dir = Path(self.adapter_path)
        if adapter_dir.exists() and (adapter_dir / "adapter_config.json").exists():
            print(f"[InferenceEngine] Attaching LoRA adapter from: {adapter_dir}")
            self.model = PeftModel.from_pretrained(base_model, str(adapter_dir))
        else:
            print(f"[InferenceEngine] No adapter found at {adapter_dir}. Using base model.")
            self.model = base_model

        self.model.eval()
        self._is_loaded = True
        print("[InferenceEngine] Model ready for inference.")

    def _extract_json(self, text: str) -> Tuple[Dict, bool]:
        clean_text = text.strip()
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
        clean_text = re.sub(r"\s*```$", "", clean_text)

        match = re.search(r"\{[\s\S]*\}", clean_text)
        if match:
            clean_text = match.group(0)

        try:
            parsed = json.loads(clean_text)
            valid = all(k in parsed for k in ["category", "priority", "department"])
            return {
                "category": parsed.get("category", "General"),
                "priority": parsed.get("priority", "Medium"),
                "department": parsed.get("department", "General Support"),
            }, valid
        except Exception:
            return {
                "category": "General",
                "priority": "Medium",
                "department": "General Support",
            }, False

    def predict(self, review_text: str) -> Dict:
        """
        Runs triage classification on a single customer ticket text.
        Returns complete triage payload with prediction, confidence, and routing status.
        """
        if not self._is_loaded:
            self.load()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": review_text},
        ]
        prompt_text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=64,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
                return_dict_in_generate=True,
                output_scores=True,
            )

        gen_tokens = outputs.sequences[0][inputs["input_ids"].shape[1] :]
        gen_text = self.tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

        # Extract token-level confidence
        token_probs = []
        if outputs.scores:
            for i, score_tensor in enumerate(outputs.scores):
                probs = torch.softmax(score_tensor[0], dim=-1)
                token_id = gen_tokens[i].item()
                token_probs.append(probs[token_id].item())

        avg_conf = float(np.mean(token_probs)) if token_probs else 1.0
        min_conf = float(np.min(token_probs)) if token_probs else 1.0

        parsed, is_valid = self._extract_json(gen_text)
        calibrated_confidence = round(0.75 * avg_conf + 0.25 * min_conf, 4) if is_valid else 0.0

        # Safety escalation layer
        safety_eval = self.escalator.evaluate_safety(
            review_text=review_text,
            predicted_category=parsed["category"],
            predicted_priority=parsed["priority"],
            predicted_department=parsed["department"],
            confidence=calibrated_confidence,
            confidence_threshold=self.confidence_threshold,
        )

        return {
            "predicted_category": parsed["category"],
            "predicted_priority": parsed["priority"],
            "predicted_department": parsed["department"],
            "confidence": calibrated_confidence,
            "final_category": safety_eval["final_category"],
            "final_priority": safety_eval["final_priority"],
            "final_department": safety_eval["final_department"],
            "routing_status": safety_eval["routing_status"],
            "escalated": safety_eval["escalated"],
            "escalation_reason": safety_eval["escalation_reason"],
            "raw_output": gen_text,
            "is_valid_json": is_valid,
            "model_version": "qwen2.5-3b-qlora-v1.0",
        }
