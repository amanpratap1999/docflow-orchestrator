import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "project-3-workflow-platform"
    assert data["confidence_threshold"] == 0.90
    assert data["invoice_limit"] == 1000.00


def test_invoice_auto_approval_flow(client):
    text = """INVOICE #INV-2024-101
Vendor: Apex Cloud Services
Invoice Date: 2024-05-10
Due Date: 2024-06-10
Bill To: Enterprise Corp

Line Items:
- Web Hosting Qty: 1 Unit Price: $350.00 Total: $350.00

Subtotal: $350.00
Tax: $28.00
Total Amount: $378.00
Payment Terms: Net 30"""

    res = client.post("/documents/text", json={"filename": "invoice_101.txt", "text": text})
    assert res.status_code == 200
    data = res.json()
    assert data["doc_type"] == "invoice"
    assert data["requires_human_approval"] is False
    assert data["status"] == "COMPLETED"
    assert data["extracted_data"]["total_amount"] == 378.00
    assert data["extracted_data"]["vendor_verified"] is True

    # Check that downstream ERP task was created
    tasks_res = client.get("/tasks")
    assert tasks_res.status_code == 200
    tasks = tasks_res.json()
    assert len(tasks) == 1
    assert tasks[0]["target_system"] == "SAP_ERP"
    assert tasks[0]["payload"]["total_amount"] == 378.00


def test_invoice_high_value_human_approval_flow(client):
    text = """INVOICE #INV-2024-999
Vendor: Dell Technologies
Invoice Date: 2024-05-11
Due Date: 2024-06-11
Bill To: Enterprise Corp

Line Items:
- Rack Server Cluster Qty: 1 Unit Price: $8,500.00 Total: $8,500.00

Subtotal: $8,500.00
Tax: $0.00
Total Amount: $8,500.00
Payment Terms: Net 30"""

    res = client.post("/documents/text", json={"filename": "invoice_high.txt", "text": text})
    assert res.status_code == 200
    data = res.json()
    assert data["doc_type"] == "invoice"
    assert data["requires_human_approval"] is True
    assert data["status"] == "PENDING_APPROVAL"
    assert "exceeds auto-approval threshold" in data["approval_reason"]

    doc_id = data["id"]

    # Approve ticket via human supervisor action
    app_res = client.post(f"/documents/{doc_id}/approve", json={"reviewer": "finance_director", "notes": "Approved for Q2 budget."})
    assert app_res.status_code == 200
    app_data = app_res.json()
    assert app_data["status"] == "COMPLETED"
    assert len(app_data["approvals"]) == 1
    assert app_data["approvals"][0]["decision"] == "APPROVED"
    assert app_data["approvals"][0]["reviewer"] == "finance_director"

    # Verify task dispatch
    tasks_res = client.get("/tasks")
    tasks = tasks_res.json()
    assert len(tasks) == 1
    assert tasks[0]["target_system"] == "SAP_ERP"
    assert tasks[0]["payload"]["total_amount"] == 8500.00


def test_invoice_unverified_vendor_rejection_flow(client):
    text = """INVOICE #INV-SUSPECT-01
Vendor: Unknown Random offshore LLC
Invoice Date: 2024-05-12
Total Amount: $450.00
Payment Terms: Net 15"""

    res = client.post("/documents/text", json={"filename": "invoice_unverified.txt", "text": text})
    assert res.status_code == 200
    data = res.json()
    assert data["requires_human_approval"] is True
    assert data["status"] == "PENDING_APPROVAL"
    assert "unverified in vendor master catalog" in data["approval_reason"]

    doc_id = data["id"]

    # Reject via supervisor action
    rej_res = client.post(f"/documents/{doc_id}/reject", json={"reviewer": "compliance_officer", "reason": "Vendor not in authorized list."})
    assert rej_res.status_code == 200
    rej_data = rej_res.json()
    assert rej_data["status"] == "COMPLETED"
    assert len(rej_data["approvals"]) == 1
    assert rej_data["approvals"][0]["decision"] == "REJECTED"

    # Confirm NO ERP task was created
    tasks_res = client.get("/tasks")
    assert len(tasks_res.json()) == 0


def test_access_request_standard_auto_approval(client):
    text = """IT SYSTEM ACCESS REQUEST
Request ID: REQ-2024-55
Employee Name: David Miller
Employee ID: EMP-4019
Department: Analytics
Requested System: Salesforce
Access Level: read
Justification: Weekly sales cohort analysis and pipeline visibility."""

    res = client.post("/documents/text", json={"filename": "access_read.txt", "text": text})
    assert res.status_code == 200
    data = res.json()
    assert data["doc_type"] == "access_request"
    assert data["requires_human_approval"] is False
    assert data["status"] == "COMPLETED"

    # Verify IAM task
    tasks_res = client.get("/tasks")
    tasks = tasks_res.json()
    assert len(tasks) == 1
    assert tasks[0]["target_system"] == "Okta_IAM"
    assert tasks[0]["payload"]["access_level"] == "read"


def test_access_request_admin_human_checkpoint(client):
    text = """IT SYSTEM ACCESS REQUEST
Request ID: REQ-2024-99
Employee Name: Alice Taylor
Employee ID: EMP-1102
Department: Infrastructure
Requested System: AWS Production
Access Level: admin
Justification: Urgent production database migration and failover drill."""

    res = client.post("/documents/text", json={"filename": "access_admin.txt", "text": text})
    assert res.status_code == 200
    data = res.json()
    assert data["doc_type"] == "access_request"
    assert data["requires_human_approval"] is True
    assert data["status"] == "PENDING_APPROVAL"
    assert "admin" in data["approval_reason"]

    doc_id = data["id"]
    app_res = client.post(f"/documents/{doc_id}/approve", json={"reviewer": "ciso_delegate", "notes": "Approved for 24h drill window."})
    assert app_res.status_code == 200
    app_data = app_res.json()
    assert app_data["status"] == "COMPLETED"

    tasks_res = client.get("/tasks")
    tasks = tasks_res.json()
    assert len(tasks) == 1
    assert tasks[0]["target_system"] == "Okta_IAM"
    assert tasks[0]["payload"]["access_level"] == "admin"


def test_unknown_document_handling(client):
    text = """Weekly Cafeteria Lunch Menu
Monday: Grilled Chicken Caesar Salad
Tuesday: Taco Tuesday with fresh salsa
Wednesday: Pasta Primavera
Thursday: Thai Green Curry
Friday: Wood-fired Pizza and Gelato"""

    res = client.post("/documents/text", json={"filename": "lunch_menu.txt", "text": text})
    assert res.status_code == 200
    data = res.json()
    assert data["doc_type"] == "unknown"
    assert data["requires_human_approval"] is True
    assert data["status"] == "PENDING_APPROVAL"
