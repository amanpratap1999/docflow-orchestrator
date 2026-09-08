import hashlib
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from src.models import DocumentModel, ApprovalModel, TaskModel
from src.classifier import classify_document
from src.extractors import extract_invoice_data, extract_access_request_data
from src.tasks import create_downstream_task
from src.config import settings

def calculate_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def process_document_pipeline(filename: str, raw_text: str, db: Session) -> DocumentModel:
    """
    Executes the Document-to-Workflow pipeline through the Finite State Machine:
    RECEIVED -> CLASSIFIED -> EXTRACTED -> (AUTO_APPROVED -> TASK_CREATED -> COMPLETED)
                                        OR (PENDING_APPROVAL)
    """
    sha = calculate_sha256(raw_text)
    doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"

    # 1. State: RECEIVED
    doc = DocumentModel(
        id=doc_id,
        filename=filename,
        sha256=sha,
        raw_text=raw_text,
        status="RECEIVED",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 2. State: CLASSIFIED
    doc_type, class_conf = classify_document(raw_text)
    doc.doc_type = doc_type
    doc.classification_confidence = class_conf
    doc.status = "CLASSIFIED"
    db.commit()

    # 3. State: EXTRACTED
    extracted_data: Dict[str, Any] = {}
    extract_conf = 0.0

    if doc_type == "invoice":
        extracted_data, extract_conf = extract_invoice_data(raw_text)
    elif doc_type == "access_request":
        extracted_data, extract_conf = extract_access_request_data(raw_text)
    else:
        extracted_data = {"raw_excerpt": raw_text[:200]}
        extract_conf = 0.30

    doc.extracted_data = extracted_data
    doc.extraction_confidence = extract_conf
    doc.status = "EXTRACTED"

    # 4. Evaluate Human Approval Checkpoint Boundary
    requires_approval = False
    approval_reason = None

    if doc_type == "invoice":
        total_amt = extracted_data.get("total_amount", 0.0)
        vendor_verified = extracted_data.get("vendor_verified", False)

        if total_amt >= settings.INVOICE_AUTO_APPROVE_MAX_AMOUNT:
            requires_approval = True
            approval_reason = f"Invoice total (${total_amt:,.2f}) meets or exceeds auto-approval threshold (${settings.INVOICE_AUTO_APPROVE_MAX_AMOUNT:,.2f})."
        elif not vendor_verified:
            requires_approval = True
            approval_reason = f"Vendor '{extracted_data.get('vendor_name')}' is unverified in vendor master catalog."
        elif extract_conf < settings.AUTO_APPROVE_CONFIDENCE_THRESHOLD:
            requires_approval = True
            approval_reason = f"Extraction confidence ({extract_conf:.2f}) is below automated processing threshold ({settings.AUTO_APPROVE_CONFIDENCE_THRESHOLD:.2f})."

    elif doc_type == "access_request":
        access_lvl = extracted_data.get("access_level", "read").lower()
        if access_lvl == "admin":
            requires_approval = True
            approval_reason = "Elevated 'admin' privilege requested. Requires IT Security Officer manual authorization."
        elif extract_conf < settings.AUTO_APPROVE_CONFIDENCE_THRESHOLD:
            requires_approval = True
            approval_reason = f"Extraction confidence ({extract_conf:.2f}) is below automated processing threshold ({settings.AUTO_APPROVE_CONFIDENCE_THRESHOLD:.2f})."

    else:
        requires_approval = True
        approval_reason = "Unrecognized document structure requires human operator triage."

    doc.requires_human_approval = requires_approval
    doc.approval_reason = approval_reason

    if requires_approval:
        doc.status = "PENDING_APPROVAL"
        db.commit()
    else:
        # Auto-Approve and trigger Downstream Task
        doc.status = "AUTO_APPROVED"
        db.commit()

        # Generate Downstream Integration Task
        task = create_downstream_task(
            document_id=doc.id,
            doc_type=doc.doc_type,
            extracted_data=extracted_data,
            approval_mode="AUTOMATED_POLICY_MATCH"
        )
        db.add(task)
        doc.status = "TASK_CREATED"
        db.commit()

        doc.status = "COMPLETED"
        db.commit()

    db.refresh(doc)
    return doc


def approve_document_in_workflow(doc_id: str, reviewer: str, notes: Optional[str], db: Session) -> DocumentModel:
    """
    Executes human approval transition:
    PENDING_APPROVAL -> APPROVED -> TASK_CREATED -> COMPLETED
    """
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise ValueError(f"Document {doc_id} not found.")

    if doc.status != "PENDING_APPROVAL":
        raise ValueError(f"Cannot approve document in status '{doc.status}'. Must be 'PENDING_APPROVAL'.")

    # Record Approval Action
    approval = ApprovalModel(
        document_id=doc.id,
        decision="APPROVED",
        reviewer=reviewer or "ops_supervisor",
        notes=notes or "Approved via operations console.",
        decided_at=datetime.utcnow()
    )
    db.add(approval)
    doc.status = "APPROVED"
    db.commit()

    # Generate Downstream Integration Task
    task = create_downstream_task(
        document_id=doc.id,
        doc_type=doc.doc_type,
        extracted_data=doc.extracted_data,
        approval_mode=f"HUMAN_SUPERVISOR ({approval.reviewer})"
    )
    db.add(task)
    doc.status = "TASK_CREATED"
    db.commit()

    doc.status = "COMPLETED"
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc


def reject_document_in_workflow(doc_id: str, reviewer: str, reason: str, db: Session) -> DocumentModel:
    """
    Executes human rejection transition:
    PENDING_APPROVAL -> REJECTED -> COMPLETED
    """
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise ValueError(f"Document {doc_id} not found.")

    if doc.status != "PENDING_APPROVAL":
        raise ValueError(f"Cannot reject document in status '{doc.status}'. Must be 'PENDING_APPROVAL'.")

    # Record Rejection Action
    approval = ApprovalModel(
        document_id=doc.id,
        decision="REJECTED",
        reviewer=reviewer or "ops_supervisor",
        notes=reason,
        decided_at=datetime.utcnow()
    )
    db.add(approval)
    doc.status = "REJECTED"
    db.commit()

    doc.status = "COMPLETED"
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc
