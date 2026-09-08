import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db, init_db
from src.models import DocumentModel, TaskModel, ApprovalModel
from src.schemas import (
    DocumentResponse,
    DocumentSubmitTextRequest,
    ApprovalActionRequest,
    RejectionActionRequest,
    TaskResponse
)
from src.ocr import process_document_bytes
from src.workflow import process_document_pipeline, approve_document_in_workflow, reject_document_in_workflow

init_db()

app = FastAPI(
    title="Document-to-Workflow Platform API",
    description="Automated document classification, entity extraction, state machine routing, and human-in-the-loop approvals.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "project-3-workflow-platform",
        "database": "sqlite-local",
        "confidence_threshold": settings.AUTO_APPROVE_CONFIDENCE_THRESHOLD,
        "invoice_limit": settings.INVOICE_AUTO_APPROVE_MAX_AMOUNT
    }

@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    raw_text = process_document_bytes(file.filename, content)
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any readable text from document.")

    doc = process_document_pipeline(file.filename, raw_text, db)
    return doc

@app.post("/documents/text", response_model=DocumentResponse)
def submit_document_text(
    payload: DocumentSubmitTextRequest,
    db: Session = Depends(get_db)
):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    doc = process_document_pipeline(payload.filename, payload.text, db)
    return doc

@app.get("/documents", response_model=List[DocumentResponse])
def list_documents(
    status: Optional[str] = Query(None, description="Filter by status, e.g. PENDING_APPROVAL, COMPLETED"),
    doc_type: Optional[str] = Query(None, description="Filter by doc_type, e.g. invoice, access_request"),
    db: Session = Depends(get_db)
):
    query = db.query(DocumentModel)
    if status:
        query = query.filter(DocumentModel.status == status)
    if doc_type:
        query = query.filter(DocumentModel.doc_type == doc_type)
    return query.order_by(DocumentModel.created_at.desc()).all()

@app.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    return doc

@app.post("/documents/{doc_id}/approve", response_model=DocumentResponse)
def approve_document(
    doc_id: str,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db)
):
    try:
        return approve_document_in_workflow(doc_id, payload.reviewer, payload.notes, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/documents/{doc_id}/reject", response_model=DocumentResponse)
def reject_document(
    doc_id: str,
    payload: RejectionActionRequest,
    db: Session = Depends(get_db)
):
    try:
        return reject_document_in_workflow(doc_id, payload.reviewer, payload.reason, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(TaskModel).order_by(TaskModel.dispatched_at.desc()).all()

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_docs = db.query(DocumentModel).count()
    pending = db.query(DocumentModel).filter(DocumentModel.status == "PENDING_APPROVAL").count()
    tasks_count = db.query(TaskModel).count()
    approvals_count = db.query(ApprovalModel).filter(ApprovalModel.decision == "APPROVED").count()
    rejections_count = db.query(ApprovalModel).filter(ApprovalModel.decision == "REJECTED").count()
    auto_approved = db.query(DocumentModel).filter(
        DocumentModel.requires_human_approval == False,
        DocumentModel.status == "COMPLETED"
    ).count()

    return {
        "total_documents": total_docs,
        "pending_human_approval": pending,
        "auto_approved": auto_approved,
        "human_approved": approvals_count,
        "rejected": rejections_count,
        "downstream_tasks_created": tasks_count
    }
