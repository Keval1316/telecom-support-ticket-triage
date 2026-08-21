"""
Phase 14 - FastAPI Application Entry Point.
Sets up CORS, initializes database schema on startup, and mounts REST endpoints.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.endpoints import router as api_router
from backend.app.database.session import init_db

app = FastAPI(
    title="Telecom Support Ticket Triage API",
    description="Fine-tuned Qwen2.5-3B AI Triage System with Confidence Scoring, Priority Escalation & Human-in-the-loop Review.",
    version="1.0.0",
)

# CORS configuration for React frontend (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initializes SQLite database tables upon startup."""
    print("[FastAPI] Initializing database tables...")
    init_db()
    print("[FastAPI] Database ready.")


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "Telecom Support Ticket Triage API",
        "model": "Qwen2.5-3B QLoRA fine-tuned",
        "runtime_cost": "₹0.00",
    }


# Mount all triage endpoints under /api (or root)
app.include_router(api_router, prefix="/api")
app.include_router(api_router)  # Also mount at root for backward compatibility with tests/spec
