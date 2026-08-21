"""
Phase 13 - SQLAlchemy Ticket Model.
Stores raw complaints, fine-tuned LLM predictions, confidence metrics,
routing status, priority escalation flags, and human reviewer corrections.
"""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from backend.app.database.session import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(String(64), unique=True, index=True, nullable=False)
    customer_name = Column(String(128), nullable=False)
    contact_number = Column(String(32), nullable=False)
    review = Column(Text, nullable=False)
    timestamp = Column(String(64), nullable=True)

    # Predictions
    predicted_category = Column(String(64), nullable=False, index=True)
    predicted_priority = Column(String(32), nullable=False, index=True)
    predicted_department = Column(String(64), nullable=False, index=True)
    confidence = Column(Float, nullable=False, index=True)

    # Routing & Safety
    routing_status = Column(String(32), nullable=False, index=True)  # "AUTO_ROUTED" | "HUMAN_REVIEW"
    escalated = Column(Boolean, default=False)
    escalation_reason = Column(String(256), nullable=True)

    # Human Review Corrections
    final_category = Column(String(64), nullable=False, index=True)
    final_priority = Column(String(32), nullable=False, index=True)
    final_department = Column(String(64), nullable=False, index=True)
    is_reviewed = Column(Boolean, default=False, index=True)
    reviewer_notes = Column(Text, nullable=True)

    # Metadata & Timestamps
    model_version = Column(String(64), default="qwen2.5-3b-qlora-v1.0")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "customer_name": self.customer_name,
            "contact_number": self.contact_number,
            "review": self.review,
            "timestamp": self.timestamp,
            "predicted_category": self.predicted_category,
            "predicted_priority": self.predicted_priority,
            "predicted_department": self.predicted_department,
            "confidence": round(self.confidence, 4),
            "routing_status": self.routing_status,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
            "final_category": self.final_category,
            "final_priority": self.final_priority,
            "final_department": self.final_department,
            "is_reviewed": self.is_reviewed,
            "reviewer_notes": self.reviewer_notes,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
