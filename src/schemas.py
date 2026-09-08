from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

class LineItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price: float
    total: float

class InvoiceData(BaseModel):
    invoice_number: str
    vendor_name: str
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total_amount: float
    currency: str = "USD"
    line_items: List[LineItem] = []
    vendor_verified: bool = True

class AccessRequestData(BaseModel):
    request_id: str
    employee_name: str
    employee_id: str
    department: str
    requested_system: str
    access_level: str = "read"  # read, write, admin
    justification: str

class ApprovalActionRequest(BaseModel):
    reviewer: str = "ops_supervisor"
    notes: Optional[str] = None

class RejectionActionRequest(BaseModel):
    reviewer: str = "ops_supervisor"
    reason: str

class TaskResponse(BaseModel):
    id: str
    document_id: str
    task_type: str
    target_system: str
    payload: Dict[str, Any]
    status: str
    dispatched_at: datetime

class ApprovalRecord(BaseModel):
    id: int
    decision: str
    reviewer: str
    notes: Optional[str]
    decided_at: datetime

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    doc_type: str
    classification_confidence: float
    extraction_confidence: float
    extracted_data: Dict[str, Any]
    requires_human_approval: bool
    approval_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approvals: List[ApprovalRecord] = []
    tasks: List[TaskResponse] = []

class DocumentSubmitTextRequest(BaseModel):
    filename: str
    text: str
