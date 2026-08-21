"""
Phase 13 - Database CRUD operations for Tickets and Review Queue.
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.app.models.ticket import Ticket


def create_ticket(db: Session, ticket_data: dict) -> Ticket:
    """Creates and persists a single ticket record."""
    ticket = Ticket(**ticket_data)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def bulk_create_tickets(db: Session, tickets_data: List[dict]) -> List[Ticket]:
    """Bulk inserts a list of ticket records."""
    tickets = [Ticket(**data) for data in tickets_data]
    db.add_all(tickets)
    db.commit()
    return tickets


def get_ticket_by_id(db: Session, ticket_id: int) -> Optional[Ticket]:
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_ticket_by_business_id(db: Session, business_id: str) -> Optional[Ticket]:
    return db.query(Ticket).filter(Ticket.ticket_id == business_id).first()


def get_filtered_tickets(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    department: Optional[str] = None,
    routing_status: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[Ticket], int]:
    """Retrieves tickets matching filter criteria with pagination."""
    query = db.query(Ticket)

    if category:
        query = query.filter(Ticket.final_category == category)
    if priority:
        query = query.filter(Ticket.final_priority == priority)
    if department:
        query = query.filter(Ticket.final_department == department)
    if routing_status:
        query = query.filter(Ticket.routing_status == routing_status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Ticket.review.ilike(search_pattern))
            | (Ticket.customer_name.ilike(search_pattern))
            | (Ticket.ticket_id.ilike(search_pattern))
        )

    total = query.count()
    tickets = (
        query.order_by(desc(Ticket.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return tickets, total


def get_review_queue(db: Session, limit: int = 50) -> List[Ticket]:
    """Fetches tickets requiring human review (low confidence or safety escalated)."""
    return (
        db.query(Ticket)
        .filter(Ticket.routing_status == "HUMAN_REVIEW", Ticket.is_reviewed == False)
        .order_by(desc(Ticket.escalated), desc(Ticket.created_at))
        .limit(limit)
        .all()
    )


def resolve_review_ticket(
    db: Session,
    ticket_id: int,
    final_category: str,
    final_priority: str,
    final_department: str,
    reviewer_notes: Optional[str] = None,
) -> Optional[Ticket]:
    """Applies human reviewer correction and saves audit timestamp."""
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        return None

    ticket.final_category = final_category
    ticket.final_priority = final_priority
    ticket.final_department = final_department
    ticket.reviewer_notes = reviewer_notes
    ticket.is_reviewed = True
    ticket.routing_status = "RESOLVED"
    ticket.reviewed_at = datetime.utcnow()
    ticket.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)
    return ticket


def resolve_all_review_tickets(db: Session) -> int:
    """Marks all unresolved HUMAN_REVIEW tickets as reviewed (pass all). Returns count."""
    pending = (
        db.query(Ticket)
        .filter(Ticket.routing_status == "HUMAN_REVIEW", Ticket.is_reviewed == False)
        .all()
    )
    now = datetime.utcnow()
    for ticket in pending:
        ticket.is_reviewed = True
        ticket.routing_status = "RESOLVED"
        ticket.reviewed_at = now
        ticket.updated_at = now
        ticket.reviewer_notes = "Bulk approved via Pass All"
    db.commit()
    return len(pending)


def clear_review_queue(db: Session) -> int:
    """Permanently deletes all unresolved HUMAN_REVIEW tickets. Returns deleted count."""
    pending = (
        db.query(Ticket)
        .filter(Ticket.routing_status == "HUMAN_REVIEW", Ticket.is_reviewed == False)
        .all()
    )
    count = len(pending)
    for ticket in pending:
        db.delete(ticket)
    db.commit()
    return count


def clear_all_tickets(db: Session) -> int:
    """Permanently deletes ALL tickets from the database. Returns deleted count."""
    count = db.query(Ticket).count()
    db.query(Ticket).delete()
    db.commit()
    return count


def recalculate_all_confidence(db: Session) -> int:
    """Re-runs heuristic confidence scorer on all tickets to fix old fake 92% values."""
    from backend.app.ml.inference import TriageInferenceEngine
    engine = TriageInferenceEngine()
    engine.load()

    tickets = db.query(Ticket).all()
    for ticket in tickets:
        # Re-predict using the same heuristic to get a properly varied confidence
        _, new_confidence = engine._heuristic_predict(ticket.review)
        ticket.confidence = new_confidence
        ticket.updated_at = datetime.utcnow()
    db.commit()
    return len(tickets)
