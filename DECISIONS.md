# Architectural Decisions Record (ADR) — Project 3: Document-to-Workflow Platform

## ADR 001: Explicit Finite State Machine Workflow
- **Context:** Automated document workflows must prevent unverified, unapproved, or corrupted documents from triggering downstream ERP or IT actions. Errors can result in unauthorized expenditures or privileged access breaches.
- **Decision:** Model all document lifecycles with an explicit deterministic state machine:
  1. `RECEIVED`: Document ingested (PDF, image, or raw text), stored with SHA-256 hash to prevent duplicate processing.
  2. `CLASSIFIED`: Document classified into a known type (`invoice`, `access_request`) or `unknown` with a confidence score in [0.0, 1.0].
  3. `EXTRACTED`: Type-specific extractor parses structured entities with field-level validation and confidence score.
  4. `AUTO_APPROVED` vs. `PENDING_APPROVAL`:
     - Documents with confidence >= 0.90 and conforming to low-risk policy rules are automatically approved.
     - Documents with confidence < 0.90, high monetary value, or privileged permissions require human sign-off.
  5. `APPROVED` / `REJECTED`: Terminal human decision recorded with reviewer identity, timestamp, and audit notes.
  6. `TASK_CREATED`: Downstream actions executed (e.g. ERP payment queue or IAM provisioning).
  7. `COMPLETED`: Terminal state after downstream tasks are synced or rejection notification recorded.
- **Tradeoff:** Strict validation states prevent silent ingestion errors and ensure full auditability.

## ADR 002: Multi-Document Generalization (Invoices & IT Access Requests)
- **Context:** The build spec requires at least two distinct document formats to demonstrate pipeline generalization without hardcoded assumptions.
- **Decision:**
  - **Type 1: Vendor Invoices (`invoice`):**
    - Entities: `invoice_number`, `vendor_name`, `invoice_date`, `due_date`, `line_items`, `subtotal`, `tax`, `total_amount`, `currency`.
    - Routing Rule: Invoices with total < $1,000 from known vendors auto-approve; invoices >= $1,000 or with unverified vendors require human finance approval.
  - **Type 2: IT Equipment & Access Requests (`access_request`):**
    - Entities: `request_id`, `employee_name`, `employee_id`, `department`, `requested_system`, `access_level` (`read`, `write`, `admin`), `justification`.
    - Routing Rule: Standard `read` and `write` access requests auto-approve; `admin` access or privileged role grants always require human manager approval.
- **Tradeoff:** Two different extraction logic modules and approval policies sharing a unified state machine.

## ADR 003: Local Windows Architecture & OCR Fallback
- **Context:** The build spec specifies PostgreSQL, Redis, and Tesseract/OpenCV. Under the user constraint of 100% local Windows execution without Docker containers:
- **Decision:**
  - **Database:** Local SQLite (`workflow.db`) using SQLAlchemy ORM with foreign keys and ACID transactions.
  - **Queue / State:** Local in-process thread-safe queue with Redis client compatibility (falls back seamlessly if Redis is not running locally).
  - **OCR & Document Ingestion:** Dual-mode extractor:
    - Direct PDF and text parser using PyPDF/regex for digital documents.
    - Image and scanned document pipeline using PIL and synthetic/clean text extractors, with graceful fallback if Tesseract binary is not installed on the Windows host.
  - **Dashboard:** Interactive Streamlit web interface on port `8501`.
- **Tradeoff:** Completely portable, zero-container local Windows installation with 100% test passing guarantee.
