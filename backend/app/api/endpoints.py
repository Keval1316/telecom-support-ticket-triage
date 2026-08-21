"""
Phase 14 & 17 - FastAPI API Router with all 7 Production Endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.app.analytics.engine import get_analytics_summary, get_analytics_trends
from backend.app.database.crud import (
    get_filtered_tickets,
    get_review_queue,
    get_ticket_by_id,
    resolve_review_ticket,
)
from backend.app.database.session import get_db
from backend.app.schemas.ticket import (
    AnalyticsSummaryResponse,
    AnalyticsTrendsResponse,
    ResolveTicketRequest,
    SingleTriageRequest,
    TicketListResponse,
    TicketResponse,
)
from backend.app.services.triage_service import TriageService

router = APIRouter()
triage_service = TriageService()


@router.post("/triage", response_model=TicketResponse, summary="Triage a single ticket")
def triage_ticket(request: SingleTriageRequest, db: Session = Depends(get_db)):
    """Triages a single customer ticket with fine-tuned local Qwen2.5-3B model."""
    try:
        res = triage_service.triage_single_ticket(db, request.model_dump())
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-csv", summary="Upload and triage a batch CSV file")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Processes batch CSV file, parses complaints, executes triage, and saves to DB."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are supported.")

    try:
        contents = await file.read()
        res = triage_service.process_csv_upload(db, contents)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tickets", response_model=TicketListResponse, summary="List tickets with filters and pagination")
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    priority: Optional[str] = None,
    department: Optional[str] = None,
    routing_status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieves paginated tickets with category/priority/department filters."""
    tickets, total = get_filtered_tickets(
        db=db,
        page=page,
        page_size=page_size,
        category=category,
        priority=priority,
        department=department,
        routing_status=routing_status,
        search=search,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "tickets": [t.to_dict() for t in tickets],
    }


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse, summary="Get executive dashboard KPIs")
def analytics_summary(db: Session = Depends(get_db)):
    """Returns total volume, auto-routing rate, average confidence, and label distributions."""
    return get_analytics_summary(db)


@router.get("/analytics/trends", response_model=AnalyticsTrendsResponse, summary="Get period-over-period trend deltas")
def analytics_trends(days_window: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    """Calculates trend percentages and directions comparing current period vs previous period."""
    return get_analytics_trends(db, days_window=days_window)


@router.get("/review-queue", summary="Get tickets awaiting human review")
def get_review_queue_endpoint(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Fetches low-confidence or safety-escalated tickets awaiting manager oversight."""
    tickets = get_review_queue(db, limit=limit)
    return [t.to_dict() for t in tickets]


@router.post("/review-queue/{ticket_id}/resolve", response_model=TicketResponse, summary="Resolve human review ticket")
def resolve_ticket(ticket_id: int, request: ResolveTicketRequest, db: Session = Depends(get_db)):
    """Saves manager label corrections and logs resolution timestamp for active learning."""
    updated = resolve_review_ticket(
        db=db,
        ticket_id=ticket_id,
        final_category=request.final_category,
        final_priority=request.final_priority,
        final_department=request.final_department,
        reviewer_notes=request.reviewer_notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found.")
    return updated.to_dict()
