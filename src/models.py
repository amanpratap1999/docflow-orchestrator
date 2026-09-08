import json
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    sha256 = Column(String(64), index=True, nullable=False)
    raw_text = Column(Text, nullable=False)
    status = Column(String(32), default="RECEIVED", index=True, nullable=False)
    doc_type = Column(String(32), default="unknown", index=True)
    classification_confidence = Column(Float, default=0.0)
    extraction_confidence = Column(Float, default=0.0)
    extracted_data_json = Column(Text, default="{}")
    requires_human_approval = Column(Boolean, default=False)
    approval_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    approvals = relationship("ApprovalModel", back_populates="document", cascade="all, delete-orphan")
    tasks = relationship("TaskModel", back_populates="document", cascade="all, delete-orphan")

    @property
    def extracted_data(self):
        try:
            return json.loads(self.extracted_data_json) if self.extracted_data_json else {}
        except Exception:
            return {}

    @extracted_data.setter
    def extracted_data(self, val):
        self.extracted_data_json = json.dumps(val)


class ApprovalModel(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    decision = Column(String(32), nullable=False)  # APPROVED / REJECTED
    reviewer = Column(String(128), default="human_operator")
    notes = Column(Text, nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="approvals")


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True, index=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    task_type = Column(String(64), nullable=False)
    target_system = Column(String(64), nullable=False)
    payload_json = Column(Text, default="{}")
    status = Column(String(32), default="DISPATCHED", index=True)
    dispatched_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="tasks")

    @property
    def payload(self):
        try:
            return json.loads(self.payload_json) if self.payload_json else {}
        except Exception:
            return {}

    @payload.setter
    def payload(self, val):
        self.payload_json = json.dumps(val)
