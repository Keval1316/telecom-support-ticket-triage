"""
One-Click Application Launcher.
Starts the FastAPI backend server on port 8000 and the Vite frontend on port 5173.
"""
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

def main():
    print("=" * 60)
    print("STARTING TELECOM SUPPORT TICKET TRIAGE SYSTEM")
    print("=" * 60)

    # 1. Start FastAPI Backend
    print("[1/2] Starting FastAPI Backend on http://localhost:8000 ...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=REPO_ROOT)

    time.sleep(2)

    # 2. Start Vite React Frontend
    print("[2/2] Starting React Vite Frontend on http://localhost:5173 ...")
    frontend_dir = REPO_ROOT / "frontend"
    frontend_cmd = ["npm.cmd" if sys.platform == "win32" else "npm", "run", "dev"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=frontend_dir)

    print("\n" + "=" * 60)
    print("APPLICATION RUNNING:")
    print("   Dashboard UI:      http://localhost:5173")
    print("   API Swagger Docs:  http://localhost:8000/docs")
    print("=" * 60)
    print("Press Ctrl+C to terminate both servers.\n")

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
