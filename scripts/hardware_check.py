"""
Phase 6 — Hardware & environment check for QLoRA fine-tuning (Colab).
Run this INSIDE Colab after installing training/requirements-colab.txt.
Checks Python, PyTorch, CUDA, GPU/VRAM, and required library versions.
Exits non-zero if anything critical is missing.
"""
import sys
import platform

REQUIRED = {
    "torch": "2.3.1",
    "transformers": "4.44.2",
    "peft": "0.12.0",
    "bitsandbytes": "0.43.3",
    "trl": "0.9.6",
    "datasets": "2.20.0",
    "accelerate": "0.33.0",
}

def check_versions():
    import importlib
    print("=" * 60)
    print("LIBRARY VERSION CHECK")
    print("=" * 60)
    ok = True
    for pkg, expected in REQUIRED.items():
        try:
            mod = importlib.import_module(pkg)
            actual = getattr(mod, "__version__", "unknown")
            status = "OK" if actual == expected else "MISMATCH"
            if status == "MISMATCH":
                ok = False
            print(f"  {pkg:15s} expected={expected:10s} actual={actual:10s} [{status}]")
        except ImportError:
            print(f"  {pkg:15s} NOT INSTALLED [FAIL]")
            ok = False
    return ok

def check_gpu():
    print("=" * 60)
    print("GPU / CUDA CHECK")
    print("=" * 60)
    import torch
    print(f"  torch.__version__       = {torch.__version__}")
    print(f"  torch.cuda.is_available = {torch.cuda.is_available()}")
    if not torch.cuda.is_available():
        print("  [FAIL] No CUDA GPU visible. In Colab: Runtime > Change runtime type > GPU (T4).")
        return False
    idx = torch.cuda.current_device()
    name = torch.cuda.get_device_name(idx)
    vram_gb = torch.cuda.get_device_properties(idx).total_memory / (1024 ** 3)
    print(f"  GPU name                = {name}")
    print(f"  VRAM                    = {vram_gb:.1f} GB")
    print(f"  CUDA version (torch)    = {torch.version.cuda}")
    if vram_gb < 12:
        print(f"  [WARN] VRAM under 12GB — QLoRA 4-bit on Qwen2.5-3B should still fit; reduce batch size if OOM.")
    else:
        print(f"  [OK] VRAM sufficient for QLoRA 4-bit fine-tuning of Qwen2.5-3B.")
    return True

def check_bnb():
    print("=" * 60)
    print("BITSANDBYTES / 4-BIT QUANT CHECK")
    print("=" * 60)
    try:
        import bitsandbytes as bnb
        import torch
        from transformers import BitsAndBytesConfig
        _ = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
        print(f"  bitsandbytes version    = {bnb.__version__}")
        print(f"  4-bit config build      = OK")
        return True
    except Exception as e:
        print(f"  [FAIL] bitsandbytes / 4-bit config error: {e}")
        return False

def main():
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    v_ok = check_versions()
    g_ok = check_gpu()
    b_ok = check_bnb()
    print("=" * 60)
    if v_ok and g_ok and b_ok:
        print("RESULT: ALL CHECKS PASSED — ready for Phase 8 (QLoRA training).")
        sys.exit(0)
    else:
        print("RESULT: ONE OR MORE CHECKS FAILED — fix before Phase 8.")
        sys.exit(1)

if __name__ == "__main__":
    main()
