"""
Standalone Test Runner for Backend Database and FastAPI Endpoints.
Uses Python's standard unittest + FastAPI TestClient.
"""
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

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=test_engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)

    def test_health(self):
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "online")
        print("  [OK] test_health PASSED")

    def test_triage_single(self):
        payload = {
            "customer_name": "Keval Chudasama",
            "contact_number": "+91-9876543210",
            "review": "My recharge payment of Rs.499 failed but amount deducted from bank.",
        }
        res = client.post("/triage", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("ticket_id", data)
        self.assertEqual(data["customer_name"], "Keval Chudasama")
        self.assertIn(data["routing_status"], ["AUTO_ROUTED", "HUMAN_REVIEW"])
        print(f"  [OK] test_triage_single PASSED (ticket_id={data['ticket_id']})")

    def test_analytics_and_review_queue(self):
        # Create 2 tickets
        client.post("/triage", json={"review": "Emergency outage in entire colony."})
        client.post("/triage", json={"review": "Inquire about 5G plans."})

        # Summary
        res_sum = client.get("/analytics/summary")
        self.assertEqual(res_sum.status_code, 200)
        self.assertEqual(res_sum.json()["total_tickets"], 2)

        # Trends
        res_trends = client.get("/analytics/trends?days_window=7")
        self.assertEqual(res_trends.status_code, 200)
        self.assertIn("summary_trends", res_trends.json())

        # Review Queue
        res_q = client.get("/review-queue")
        self.assertEqual(res_q.status_code, 200)
        queue = res_q.json()
        if queue:
            t_id = queue[0]["id"]
            res_res = client.post(
                f"/review-queue/{t_id}/resolve",
                json={
                    "final_category": "Technical",
                    "final_priority": "Critical",
                    "final_department": "Technical",
                    "reviewer_notes": "Resolved by test manager",
                },
            )
            self.assertEqual(res_res.status_code, 200)
            self.assertTrue(res_res.json()["is_reviewed"])

        print("  [OK] test_analytics_and_review_queue PASSED")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RUNNING BACKEND DATABASE & FASTAPI API TESTS")
    print("=" * 60)
    unittest.main(verbosity=2)
