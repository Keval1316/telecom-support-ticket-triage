"""
Phase 15 - Triage Service & CSV Batch Processor.
Handles single ticket triage requests and batch CSV uploads with column validation,
parallel/batched inference, database persistence, and summary calculation.
"""
import io
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.database.crud import bulk_create_tickets, create_ticket
from backend.app.ml.inference import TriageInferenceEngine


class TriageService:
    def __init__(self, inference_engine: Optional[TriageInferenceEngine] = None):
        self.engine = inference_engine or TriageInferenceEngine()

    def triage_single_ticket(self, db: Session, ticket_data: dict) -> dict:
        """Processes and saves a single customer support ticket."""
        review_text = ticket_data.get("review", "").strip()
        if not review_text:
            raise ValueError("Review complaint text cannot be empty.")

        triage_result = self.engine.predict(review_text)

        ticket_id = ticket_data.get("ticket_id") or f"TCK-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        db_payload = {
            "ticket_id": ticket_id,
            "customer_name": ticket_data.get("customer_name") or "Anonymous Customer",
            "contact_number": ticket_data.get("contact_number") or "+91-XXXXXXXXXX",
            "review": review_text,
            "timestamp": ticket_data.get("timestamp") or datetime.utcnow().isoformat(),
            "predicted_category": triage_result["predicted_category"],
            "predicted_priority": triage_result["predicted_priority"],
            "predicted_department": triage_result["predicted_department"],
            "confidence": triage_result["confidence"],
            "routing_status": triage_result["routing_status"],
            "escalated": triage_result["escalated"],
            "escalation_reason": triage_result["escalation_reason"],
            "final_category": triage_result["final_category"],
            "final_priority": triage_result["final_priority"],
            "final_department": triage_result["final_department"],
            "is_reviewed": False,
            "model_version": triage_result["model_version"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        created = create_ticket(db, db_payload)
        return created.to_dict()

    def process_csv_upload(self, db: Session, file_contents: bytes) -> Dict:
        """
        Parses uploaded CSV, validates required columns, executes batch triage,
        and saves all tickets to the database.
        """
        try:
            df = pd.read_csv(io.BytesIO(file_contents))
        except Exception as e:
            raise ValueError(f"Invalid CSV file format: {str(e)}")

        if df.empty:
            raise ValueError("Uploaded CSV file is empty.")

        # Normalize column names
        col_map = {str(c).lower().strip(): c for c in df.columns}
        review_col = col_map.get("review") or col_map.get("complaint") or col_map.get("text") or col_map.get("ticket_text")
        if not review_col:
            raise ValueError("CSV must contain a 'review' (or 'complaint' / 'text') column.")

        name_col = col_map.get("name") or col_map.get("customer_name") or col_map.get("customer")
        contact_col = col_map.get("contact_number") or col_map.get("contact") or col_map.get("phone") or col_map.get("mobile")
        time_col = col_map.get("timestamp") or col_map.get("date") or col_map.get("time")

        db_records = []
        auto_routed_count = 0
        human_review_count = 0
        batch_id = datetime.utcnow().strftime("%Y%m%d%H%M")

        for idx, row in df.iterrows():
            review_text = str(row[review_col]).strip() if pd.notna(row[review_col]) else ""
            if not review_text or review_text.lower() == "nan":
                continue

            customer_name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else f"Customer #{idx+1}"
            contact_number = str(row[contact_col]).strip() if contact_col and pd.notna(row[contact_col]) else "+91-XXXXXXXXXX"
            timestamp_val = str(row[time_col]).strip() if time_col and pd.notna(row[time_col]) else datetime.utcnow().isoformat()

            triage = self.engine.predict(review_text)

            if triage["routing_status"] == "AUTO_ROUTED":
                auto_routed_count += 1
            else:
                human_review_count += 1

            ticket_id = f"TCK-CSV-{batch_id}-{idx+1:04d}"
            db_records.append({
                "ticket_id": ticket_id,
                "customer_name": customer_name,
                "contact_number": contact_number,
                "review": review_text,
                "timestamp": timestamp_val,
                "predicted_category": triage["predicted_category"],
                "predicted_priority": triage["predicted_priority"],
                "predicted_department": triage["predicted_department"],
                "confidence": triage["confidence"],
                "routing_status": triage["routing_status"],
                "escalated": triage["escalated"],
                "escalation_reason": triage["escalation_reason"],
                "final_category": triage["final_category"],
                "final_priority": triage["final_priority"],
                "final_department": triage["final_department"],
                "is_reviewed": False,
                "model_version": triage["model_version"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })

        if db_records:
            bulk_create_tickets(db, db_records)

        total_processed = len(db_records)
        auto_rate = round((auto_routed_count / total_processed) * 100, 1) if total_processed > 0 else 0.0

        return {
            "total_processed": total_processed,
            "auto_routed_count": auto_routed_count,
            "human_review_count": human_review_count,
            "auto_routing_rate": auto_rate,
            "batch_id": batch_id,
            "sample_results": [r for r in db_records[:5]],
        }
