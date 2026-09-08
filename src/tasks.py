import uuid
from datetime import datetime
from typing import Dict, Any
from src.models import TaskModel

def create_downstream_task(document_id: str, doc_type: str, extracted_data: Dict[str, Any], approval_mode: str) -> TaskModel:
    """
    Constructs and records a downstream integration task (e.g. ERP payment or IAM provisioning)
    for an approved document.
    """
    task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"

    if doc_type == "invoice":
        task_type = "erp_invoice_payment"
        target_system = "SAP_ERP"
        payload = {
            "vendor_name": extracted_data.get("vendor_name", "Unknown"),
            "invoice_number": extracted_data.get("invoice_number", "INV-UNKNOWN"),
            "total_amount": extracted_data.get("total_amount", 0.0),
            "currency": extracted_data.get("currency", "USD"),
            "due_date": extracted_data.get("due_date", "Immediate"),
            "payment_status": "SCHEDULED_FOR_DISBURSEMENT",
            "approval_mode": approval_mode
        }
    elif doc_type == "access_request":
        task_type = "iam_access_grant"
        target_system = "Okta_IAM"
        payload = {
            "employee_id": extracted_data.get("employee_id", "EMP-UNKNOWN"),
            "employee_name": extracted_data.get("employee_name", "Unknown"),
            "system": extracted_data.get("requested_system", "GENERAL"),
            "access_level": extracted_data.get("access_level", "read"),
            "provisioning_status": "PROVISIONED",
            "approval_mode": approval_mode
        }
    else:
        task_type = "generic_document_sync"
        target_system = "Enterprise_Archive"
        payload = {
            "doc_type": doc_type,
            "status": "ARCHIVED",
            "approval_mode": approval_mode
        }

    task = TaskModel(
        id=task_id,
        document_id=document_id,
        task_type=task_type,
        target_system=target_system,
        status="DISPATCHED",
        dispatched_at=datetime.utcnow()
    )
    task.payload = payload
    return task
