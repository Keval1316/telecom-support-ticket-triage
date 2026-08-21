"""
Phase 13/14 - Pydantic Request & Response Schemas for Triage System.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SingleTriageRequest(BaseModel):
    customer_name: Optional[str] = "Customer"
    contact_number: Optional[str] = "+91-9876543210"
    review: str = Field(..., min_length=3, description="Customer telecom complaint text")
    timestamp: Optional[str] = None


class TicketResponse(BaseModel):
    id: int
    ticket_id: str
    customer_name: str
    contact_number: str
    review: str
    timestamp: Optional[str] = None
    predicted_category: str
    predicted_priority: str
    predicted_department: str
    confidence: float
    routing_status: str
    escalated: bool
    escalation_reason: Optional[str] = None
    final_category: str
    final_priority: str
    final_department: str
    is_reviewed: bool
    reviewer_notes: Optional[str] = None
    model_version: str
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (),
    }


class TicketListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    tickets: List[TicketResponse]


class ResolveTicketRequest(BaseModel):
    final_category: str
    final_priority: str
    final_department: str
    reviewer_notes: Optional[str] = None


class AnalyticsSummaryResponse(BaseModel):
    total_tickets: int
    auto_routed_count: int
    human_review_count: int
    auto_routing_rate: float
    avg_confidence: float
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    categories: dict
    priorities: dict
    departments: dict


class TrendItem(BaseModel):
    name: str
    current: int
    previous: int
    percentage_change: float
    direction: str  # "UP", "DOWN", "FLAT"


class AnalyticsTrendsResponse(BaseModel):
    summary_trends: List[TrendItem]
    category_trends: List[TrendItem]
    priority_trends: List[TrendItem]
    department_trends: List[TrendItem]
