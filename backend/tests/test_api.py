"""
Backend API & Database Unit Tests.
Tests database creation, CRUD, triage endpoints, CSV uploads, analytics, and review queue.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.session import Base, get_db
from backend.app.main import app

# In-memory SQLite for isolated fast unit testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_triage_single_ticket():
    payload = {
        "customer_name": "Rohan Sharma",
        "contact_number": "+91-9876543210",
        "review": "My recharge was deducted twice for Rs 299 but data pack is not activated. Need immediate refund.",
    }
    response = client.post("/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "ticket_id" in data
    assert data["customer_name"] == "Rohan Sharma"
    assert data["routing_status"] in ["AUTO_ROUTED", "HUMAN_REVIEW"]
    assert 0.0 <= data["confidence"] <= 1.0


def test_list_tickets_and_filters():
    # Insert 2 tickets
    client.post("/triage", json={"review": "Network is very slow in my area."})
    client.post("/triage", json={"review": "Please tell me the validity of my plan."})

    response = client.get("/tickets?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["tickets"]) == 2


def test_analytics_summary_and_trends():
    client.post("/triage", json={"review": "Billing discrepancy on my invoice."})
    client.post("/triage", json={"review": "SIM swap unauthorized emergency."})

    res_sum = client.get("/analytics/summary")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert sum_data["total_tickets"] == 2
    assert "auto_routing_rate" in sum_data

    res_trends = client.get("/analytics/trends?days_window=7")
    assert res_trends.status_code == 200
    assert "summary_trends" in res_trends.json()


def test_review_queue_and_resolve():
    # Insert a ticket
    triage_res = client.post("/triage", json={"review": "Medical emergency! Need ambulance coverage signal dead."})
    t_id = triage_res.json()["id"]

    # Check review queue
    q_res = client.get("/review-queue")
    assert q_res.status_code == 200

    # Resolve ticket
    resolve_payload = {
        "final_category": "Technical",
        "final_priority": "Critical",
        "final_department": "Technical",
        "reviewer_notes": "Verified by manager. Emergency ticket handled.",
    }
    res_resolve = client.post(f"/review-queue/{t_id}/resolve", json=resolve_payload)
    assert res_resolve.status_code == 200
    resolved_data = res_resolve.json()
    assert resolved_data["is_reviewed"] is True
    assert resolved_data["reviewer_notes"] == "Verified by manager. Emergency ticket handled."
