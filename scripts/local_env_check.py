import sys, platform
def line(label, value):
    print(f"{label:<28}: {value}")

print("=" * 60)
print("TELECOM TRIAGE — LOCAL ENVIRONMENT CHECK")
print("=" * 60)
line("Python version", sys.version.split()[0])
line("Platform", platform.platform())
print("-" * 60)

libs = ["dotenv", "pydantic", "pandas", "numpy", "sklearn", "groq", "fastapi", "sqlalchemy", "httpx", "pytest"]
for lib_name in libs:
    try:
        mod = __import__(lib_name)
        v = getattr(mod, "__version__", "unknown")
        line(lib_name, v)
    except Exception as e:
        line(lib_name, f"MISSING/ERROR ({e})")

print("=" * 60)
print("Copy this output and paste it back into the chat.")
print("=" * 60)
