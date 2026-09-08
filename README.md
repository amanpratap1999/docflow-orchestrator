# Project 3: Document-to-Workflow Platform

An enterprise document automation and workflow platform that turns unstructured business documents (PDFs, scans, text requests) into structured data, enforces policy-driven human approval checkpoints, and dispatches automated downstream integration tasks.

---

## Key Features

- **Multi-Document Generalization:**
  - **Type 1: Invoices (`invoice`):** Extracts invoice ID, vendor, dates, line items, and total amount. Auto-approves purchases under $1,000 from verified vendors; triggers human finance review for high-value or unverified vendors.
  - **Type 2: IT Access Requests (`access_request`):** Extracts employee details, target system, and requested privilege. Auto-approves standard `read`/`write` requests; flags elevated `admin` privileges for mandatory security review.
- **Finite State Machine Pipeline:**
  - Strict status transitions: `RECEIVED` $\rightarrow$ `CLASSIFIED` $\rightarrow$ `EXTRACTED` $\rightarrow$ `PENDING_APPROVAL` / `AUTO_APPROVED` $\rightarrow$ `APPROVED` / `REJECTED` $\rightarrow$ `TASK_CREATED` $\rightarrow$ `COMPLETED`.
  - Zero-guesswork safety: high-risk documents are intercepted before any downstream action can be taken.
- **Human-in-the-Loop Operations Console:**
  - Interactive Streamlit dashboard on port `8501`.
  - Supervisors review extracted JSON, audit reason flags, and execute 1-click approvals or rejections with custom notes.
- **Automated Downstream Task Dispatching:**
  - Integrations simulated for SAP ERP (vendor disbursements) and Okta IAM (access provisioning).
- **Zero-Docker Native Windows Architecture:**
  - Runs natively on Python 3.11 with SQLite ACID persistence and local in-process queue.

---

## Quickstart (Local Windows)

### 1. Setup Virtual Environment
```powershell
cd "project-3-workflow-platform"
py -3.11 -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

### 2. Launch Services
Run the automated PowerShell runner:
```powershell
.\run_local.ps1
```
Or start each service independently:
```powershell
# Terminal 1: FastAPI Service (Port 8003)
.\venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8003 --reload

# Terminal 2: Streamlit Dashboard (Port 8501)
.\venv\Scripts\streamlit run dashboard.py --server.port 8501
```

- **Interactive Ops Console:** [http://localhost:8501](http://localhost:8501)
- **FastAPI Swagger API Docs:** [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs)
- **Health Check:** [http://127.0.0.1:8003/health](http://127.0.0.1:8003/health)

---

## Docker Quickstart

```bash
docker-compose up --build
```
The FastAPI API will be available at port `8003` and the Streamlit dashboard at port `8501`.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health, thresholds, and configuration |
| `POST` | `/documents/upload` | Upload PDF, image, or text file |
| `POST` | `/documents/text` | Submit raw text document payload |
| `GET` | `/documents` | Query documents (filter by `status`, `doc_type`) |
| `GET` | `/documents/{id}` | Detailed document data, approvals, and tasks |
| `POST` | `/documents/{id}/approve` | Human supervisor approval |
| `POST` | `/documents/{id}/reject` | Human supervisor rejection |
| `GET` | `/tasks` | List downstream ERP and IAM tasks |
| `GET` | `/stats` | Live platform metrics |

---

## Running Tests & Benchmark Evaluation

### Automated Test Suite:
```powershell
.\venv\Scripts\pytest -v tests/
```

### 30-Document Evaluation Benchmark:
```powershell
.\venv\Scripts\python eval/run_eval.py
```
Benchmark results and metrics are recorded in [docs/eval-results.md](docs/eval-results.md).
