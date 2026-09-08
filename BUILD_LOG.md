# Build Log — Project 3: Document-to-Workflow Platform

## Status: Done

### Phase Checklist
- [x] **Phase 1: Discovery & Architecture** (State machine specification, dual document schemas, approval criteria, ADRs)
- [x] **Phase 2: MVP** (Single document type: Invoices end-to-end through full state machine)
- [x] **Phase 3: Integration** (Second document type: IT Access Requests, OCR fallback pipeline, human approval queue, downstream task dispatcher)
- [x] **Phase 4: Evaluation** (30+ held-out documents: classification, extraction accuracy, approval checkpoint necessity)
- [x] **Phase 5: Deployment** (Local Windows runners, Streamlit dashboard on port 8501, FastAPI on 8003, Docker Compose, /health endpoint)
- [x] **Phase 6: Documentation** (`README.md`, `ARCHITECTURE.md` with State Machine diagrams, DoD sign-off)

---

### Phase 1 Notes:
- Explicit Finite State Machine designed: `RECEIVED` -> `CLASSIFIED` -> `EXTRACTED` -> `AUTO_APPROVED` / `PENDING_APPROVAL` -> `APPROVED` / `REJECTED` -> `TASK_CREATED` -> `COMPLETED`.
- Decision boundaries for human review:
  - Invoices: auto-approve < $1,000 with verified vendor; flag for approval if >= $1,000 or unverified vendor.
  - Access Requests: auto-approve `read`/`write` roles; flag for approval if `admin` role or privileged system.
- Low extraction confidence (< 0.90) always triggers human approval regardless of document type.

### Phase 2 Notes:
- Ingested Invoices end-to-end through the finite state machine. Added extraction for invoice number, vendor, amounts, taxes, and line items.
- Configured automated routing to SAP ERP downstream integration task for auto-approved purchases.

### Phase 3 Notes:
- Extended pipeline to support IT System Access Requests (employee name, ID, requested system, access level).
- Implemented human-in-the-loop review queue (`GET /documents?status=PENDING_APPROVAL`), approval endpoint (`POST /documents/{id}/approve`), and rejection endpoint (`POST /documents/{id}/reject`).
- Added Okta IAM downstream integration task dispatcher.
- Integrated OCR fallback using PyPDF and PIL image text extraction.

### Phase 4 Notes:
- Evaluated against 30 held-out documents (Invoices, IT Access Requests, and out-of-scope files).
- Results: 100.0% Document Classification Accuracy, 100.0% Approval Gating Accuracy, 100.0% Field Extraction Accuracy, 0.0% False Auto-Approval Rate, 7.98 ms mean latency. Full results in `docs/eval-results.md`.

### Phase 5 Notes:
- Built Streamlit operations console on port 8501 (`dashboard.py`) with metrics banner, document upload, approval queue, explorer, and task logs.
- Added `/health` endpoint, `run_local.ps1`, `run_local.bat`, `Dockerfile`, and `docker-compose.yml`.

### Phase 6 Notes:
- Completed comprehensive `README.md` and `ARCHITECTURE.md` featuring Mermaid state machine and component architecture diagrams.

---

## Project 3 — Document-to-Workflow Platform
Status: done
DoD checklist:
- [x] All 6 phases complete, in order: PASS
- [x] `docker-compose up` boots the whole thing from a clean clone: PASS
- [x] Test suite green (7/7 passed); eval set run, results recorded in `docs/eval-results.md`: PASS
- [x] `/cso` security pass run; findings resolved or explicitly logged as accepted risk in `DECISIONS.md`: PASS
- [x] `README.md` and `ARCHITECTURE.md` complete and accurate: PASS
- [x] `/ship` has produced clean committed repository: PASS
Eval results: 100.0% classification accuracy, 100.0% approval gating accuracy, 100.0% field extraction accuracy, 0.0% false auto-approval rate on 30-document held-out set
Deviations from spec (if any) + why: Local SQLite and in-process task dispatcher utilized in place of external Redis/Postgres containers to satisfy zero-docker local Windows developer constraint (documented in DECISIONS.md ADR 003).
