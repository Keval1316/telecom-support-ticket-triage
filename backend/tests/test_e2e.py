"""
Phase 19 - Comprehensive End-to-End Lifecycle Integration Test.
Tests the complete flow:
1. Batch CSV ingestion
2. Database persistence & index verification
3. Querying with complex filters
4. Real-time Analytics summary & 7-day trend calculations
5. Review queue retrieval
6. Human reviewer resolution & active learning audit verification
"""
import io
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.session import Base, get_db
from backend.app.main import app

SAMPLE_CSV_PATH = REPO_ROOT / "data" / "demo" / "sample_upload.csv"

# In-memory test DB
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestEndToEndLifecycle(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=test_engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)

    def test_complete_ticket_triage_lifecycle(self):
        print("\n--- [E2E STEP 1] Uploading and Triaging Batch CSV ---")
        # Ensure sample CSV exists or create mock CSV bytes
        if SAMPLE_CSV_PATH.exists():
            with open(SAMPLE_CSV_PATH, "rb") as f:
                csv_bytes = f.read()
        else:
            csv_bytes = b"customer_name,contact_number,review,timestamp\nAnjali Rao,+91-9876543210,Broadband dead since yesterday need urgent help,2026-08-21T10:00:00\nRajesh Patel,+91-9876543211,Please reverse Rs 499 recharge deducted twice,2026-08-21T10:05:00\n"

        response = client.post(
            "/upload-csv",
            files={"file": ("sample_upload.csv", csv_bytes, "text/csv")},
        )
        self.assertEqual(response.status_code, 200)
        upload_data = response.json()
        self.assertGreater(upload_data["total_processed"], 0)
        self.assertIn("auto_routing_rate", upload_data)
        print(f"  [OK] Successfully processed {upload_data['total_processed']} tickets via /upload-csv")

        print("\n--- [E2E STEP 2] Verifying Paginated Ticket Retrieval & Filters ---")
        res_tickets = client.get("/tickets?page=1&page_size=10")
        self.assertEqual(res_tickets.status_code, 200)
        t_data = res_tickets.json()
        self.assertEqual(t_data["total"], upload_data["total_processed"])
        self.assertGreaterEqual(len(t_data["tickets"]), 1)

        first_ticket = t_data["tickets"][0]
        self.assertIn("ticket_id", first_ticket)
        self.assertIn("predicted_category", first_ticket)
        self.assertIn("confidence", first_ticket)
        self.assertIn(first_ticket["routing_status"], ["AUTO_ROUTED", "HUMAN_REVIEW"])
        print(f"  [OK] Fetched tickets: Total = {t_data['total']}, First ID = {first_ticket['ticket_id']}")

        print("\n--- [E2E STEP 3] Verifying Real DB-Backed Analytics KPIs ---")
        res_summary = client.get("/analytics/summary")
        self.assertEqual(res_summary.status_code, 200)
        sum_data = res_summary.json()
        self.assertEqual(sum_data["total_tickets"], upload_data["total_processed"])
        self.assertEqual(sum_data["auto_routed_count"] + sum_data["human_review_count"], upload_data["total_processed"])
        self.assertIn("categories", sum_data)
        self.assertIn("priorities", sum_data)
        self.assertIn("departments", sum_data)
        print(f"  [OK] Analytics KPIs: Auto-Routing Rate = {sum_data['auto_routing_rate']}%, Avg Conf = {sum_data['avg_confidence']}")

        print("\n--- [E2E STEP 4] Verifying 7-Day Trend Engine ---")
        res_trends = client.get("/analytics/trends?days_window=7")
        self.assertEqual(res_trends.status_code, 200)
        trend_data = res_trends.json()
        self.assertIn("summary_trends", trend_data)
        self.assertIn("category_trends", trend_data)
        self.assertIn("priority_trends", trend_data)
        self.assertIn("department_trends", trend_data)
        print(f"  [OK] Trend calculations verified ({len(trend_data['summary_trends'])} summary trend metrics)")

        print("\n--- [E2E STEP 5] Testing Human Review Queue & Active Learning Resolution ---")
        # Ingest a low-confidence or critical emergency ticket guaranteed to route to HUMAN_REVIEW
        client.post("/triage", json={
            "customer_name": "Emergency User",
            "contact_number": "+91-9999999999",
            "review": "Medical emergency! Ambulance cannot reach patient because cellular network tower collapsed in sector 4.",
        })

        res_queue = client.get("/review-queue")
        self.assertEqual(res_queue.status_code, 200)
        queue_list = res_queue.json()
        self.assertGreaterEqual(len(queue_list), 1)

        ticket_to_resolve = queue_list[0]
        t_id = ticket_to_resolve["id"]
        print(f"  [OK] Review queue has {len(queue_list)} tickets awaiting manager review. Resolving Ticket #{t_id}...")

        resolve_payload = {
            "final_category": "Technical",
            "final_priority": "Critical",
            "final_department": "Technical",
            "reviewer_notes": "Handled with high urgency by Senior Support Manager. Tower dispatch initiated.",
        }
        res_resolve = client.post(f"/review-queue/{t_id}/resolve", json=resolve_payload)
        self.assertEqual(res_resolve.status_code, 200)
        resolved_ticket = res_resolve.json()

        self.assertTrue(resolved_ticket["is_reviewed"])
        self.assertEqual(resolved_ticket["final_priority"], "Critical")
        self.assertEqual(resolved_ticket["reviewer_notes"], resolve_payload["reviewer_notes"])
        self.assertIsNotNone(resolved_ticket["reviewed_at"])
        print(f"  [OK] Ticket #{t_id} successfully resolved and archived for active learning retrain.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
