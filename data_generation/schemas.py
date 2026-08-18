"""
Shared Pydantic schemas for generated ticket records.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Literal

Category = Literal["Billing", "Technical", "Account", "Refund", "General"]
Priority = Literal["Critical", "High", "Medium", "Low"]
Department = Literal["Finance", "Technical", "Account", "Refunds", "General Support"]


class TicketFields(BaseModel):
    ticket_id: str
    customer_name: str
    contact_number: str
    review: str = Field(min_length=5)
    timestamp: str
    category: Category
    priority: Priority
    department: Department

    @field_validator("review")
    @classmethod
    def review_not_placeholder(cls, v: str) -> str:
        if v.strip().lower() in {"n/a", "none", "test", ""}:
            raise ValueError("review looks like a placeholder, not a real complaint")
        return v


class TicketMetadata(BaseModel):
    generation_batch: str
    generation_source: str = "groq"
    scenario_type: str
    difficulty: str
    teacher_model: str
    generation_timestamp: str
    dataset_version: str
    key_index: int


class TicketRecord(BaseModel):
    fields: TicketFields
    metadata: TicketMetadata
