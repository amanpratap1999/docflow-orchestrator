import streamlit as st
import requests
import json
import os

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8003")

st.set_page_config(
    page_title="Document-to-Workflow Ops Console",
    page_icon="📑",
    layout="wide"
)

st.title("📑 Document-to-Workflow Operations Platform")
st.caption("Autonomous classification, extraction, state machine routing, and human-in-the-loop checkpoints.")

# 1. Pipeline Metrics Banner
try:
    stats_res = requests.get(f"{API_BASE}/stats", timeout=2)
    if stats_res.status_code == 200:
        stats = stats_res.json()
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Documents", stats["total_documents"])
        col2.metric("Pending Approval", stats["pending_human_approval"])
        col3.metric("Auto-Approved", stats["auto_approved"])
        col4.metric("Human Approved", stats["human_approved"])
        col5.metric("Tasks Dispatched", stats["downstream_tasks_created"])
except Exception:
    st.warning("⚠️ FastAPI backend is currently offline. Start the service on port 8003 to connect.")

st.divider()

# Navigation Tabs
tab_upload, tab_queue, tab_docs, tab_tasks = st.tabs([
    "📥 Ingest Document",
    "⏳ Human Approval Queue",
    "📂 Document Explorer",
    "⚡ Downstream Tasks"
])

# --- TAB 1: INGEST ---
with tab_upload:
    st.subheader("Upload & Process Document")
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("##### Direct Upload")
        uploaded_file = st.file_uploader("Upload PDF, Image, or Text file", type=["pdf", "txt", "png", "jpg"])

        st.markdown("##### Quick Demo Samples")
        sample_choice = st.selectbox(
            "Or select a pre-built document:",
            [
                "None",
                "1. Verified Low-Value Invoice ($420.00 - Auto-Approve)",
                "2. High-Value Invoice ($14,500.00 - Human Sign-off Required)",
                "3. Standard Read Access Request (Auto-Approve)",
                "4. Privileged Admin Access Request (Security Review Required)"
            ]
        )

        sample_texts = {
            "1. Verified Low-Value Invoice ($420.00 - Auto-Approve)": (
                "invoice_420.txt",
                """INVOICE #INV-2024-8812
Vendor: Apex Cloud Services
Invoice Date: 2024-05-12
Due Date: 2024-06-12
Bill To: Enterprise Corp

Line Items:
- Cloud Compute Tier 2   Qty: 2   Unit Price: $180.00   Total: $360.00
- Bandwidth Overages               Unit Price: $30.00    Total: $30.00

Subtotal: $390.00
Tax: $30.00
Total Amount: $420.00
Payment Terms: Net 30"""
            ),
            "2. High-Value Invoice ($14,500.00 - Human Sign-off Required)": (
                "invoice_enterprise.txt",
                """INVOICE #INV-9042
Vendor: Dell Technologies
Invoice Date: 2024-05-15
Due Date: 2024-06-15
Bill To: Enterprise Corp

Line Items:
- PowerEdge R750 Server    Qty: 2   Unit Price: $6,500.00   Total: $13,000.00
- Enterprise Support Care           Unit Price: $1,500.00   Total: $1,500.00

Subtotal: $14,500.00
Tax: $0.00
Total Amount: $14,500.00
Payment Terms: Net 30"""
            ),
            "3. Standard Read Access Request (Auto-Approve)": (
                "access_req_read.txt",
                """IT SYSTEM ACCESS REQUEST
Request ID: REQ-1049
Employee Name: Marcus Chen
Employee ID: EMP-55102
Department: Marketing & Analytics
Requested System: Salesforce
Access Level: read
Business Justification: Needs view-only reporting access for quarterly campaign analytics and attribution tracking."""
            ),
            "4. Privileged Admin Access Request (Security Review Required)": (
                "access_req_admin.txt",
                """IT SYSTEM ACCESS REQUEST
Request ID: REQ-9901
Employee Name: Sarah Connor
Employee ID: EMP-11204
Department: DevOps Engineering
Requested System: AWS Production
Access Level: admin
Business Justification: Requires root IAM privilege to troubleshoot latency spikes in the production cluster during maintenance window."""
            )
        }

        demo_filename = ""
        demo_content = ""
        if sample_choice in sample_texts:
            demo_filename, demo_content = sample_texts[sample_choice]

        text_input = st.text_area(
            "Document Raw Text",
            value=demo_content,
            height=220,
            placeholder="Paste raw document text here..."
        )

        submit_btn = st.button("🚀 Process Document", type="primary", use_container_width=True)

    with col_right:
        st.markdown("##### Execution State & Extraction Output")
        if submit_btn:
            with st.spinner("Executing finite state machine pipeline..."):
                try:
                    if uploaded_file is not None:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                        res = requests.post(f"{API_BASE}/documents/upload", files=files)
                    elif text_input.strip():
                        fn = demo_filename if demo_filename else "document.txt"
                        res = requests.post(f"{API_BASE}/documents/text", json={"filename": fn, "text": text_input})
                    else:
                        st.error("Please provide a file or text content.")
                        res = None

                    if res and res.status_code == 200:
                        doc = res.json()
                        st.success(f"Document **{doc['id']}** Processed Successfully!")

                        # Visual status indicator
                        status_color = "🟢" if doc["status"] == "COMPLETED" else "🟡"
                        st.markdown(f"**State:** {status_color} `{doc['status']}`")
                        st.markdown(f"**Type:** `{doc['doc_type']}` (Confidence: `{doc['classification_confidence']:.2f}`)")

                        if doc["requires_human_approval"]:
                            st.warning(f"⚠️ **Human Approval Required:** {doc['approval_reason']}")
                        else:
                            st.info("✅ **Auto-Approved:** Met all automated policy checks. Downstream task created.")

                        st.json(doc["extracted_data"])
                    elif res:
                        st.error(f"Error {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"Failed to communicate with API: {str(e)}")

# --- TAB 2: HUMAN APPROVAL QUEUE ---
with tab_queue:
    st.subheader("Human-in-the-Loop Review Queue")
    try:
        q_res = requests.get(f"{API_BASE}/documents?status=PENDING_APPROVAL")
        if q_res.status_code == 200:
            pending_docs = q_res.json()
            if not pending_docs:
                st.success("🎉 Queue is empty! All documents have been resolved or auto-approved.")
            else:
                for p_doc in pending_docs:
                    with st.expander(f"⚠️ [{p_doc['doc_type'].upper()}] {p_doc['filename']} — ID: {p_doc['id']}", expanded=True):
                        col_info, col_act = st.columns([2, 1])
                        with col_info:
                            st.markdown(f"**Trigger Reason:** :red[{p_doc['approval_reason']}]")
                            st.markdown(f"**Classification Confidence:** `{p_doc['classification_confidence']:.2f}` | **Extraction Confidence:** `{p_doc['extraction_confidence']:.2f}`")
                            st.markdown("**Extracted Data Summary:**")
                            st.json(p_doc["extracted_data"])

                        with col_act:
                            st.markdown("##### Supervisor Action")
                            reviewer_name = st.text_input("Reviewer Name", value="ops_manager", key=f"rev_{p_doc['id']}")
                            action_notes = st.text_input("Decision Notes / Justification", value="Approved upon verification.", key=f"notes_{p_doc['id']}")

                            c_app, c_rej = st.columns(2)
                            if c_app.button("✅ Approve", key=f"app_{p_doc['id']}", use_container_width=True):
                                app_res = requests.post(
                                    f"{API_BASE}/documents/{p_doc['id']}/approve",
                                    json={"reviewer": reviewer_name, "notes": action_notes}
                                )
                                if app_res.status_code == 200:
                                    st.success("Approved! Downstream task generated.")
                                    st.rerun()
                                else:
                                    st.error(app_res.text)

                            if c_rej.button("❌ Reject", key=f"rej_{p_doc['id']}", use_container_width=True):
                                rej_res = requests.post(
                                    f"{API_BASE}/documents/{p_doc['id']}/reject",
                                    json={"reviewer": reviewer_name, "reason": action_notes}
                                )
                                if rej_res.status_code == 200:
                                    st.warning("Document rejected and audit record logged.")
                                    st.rerun()
                                else:
                                    st.error(rej_res.text)
    except Exception as e:
        st.error(f"Failed to load approval queue: {str(e)}")

# --- TAB 3: DOCUMENT EXPLORER ---
with tab_docs:
    st.subheader("All Ingested Documents")
    try:
        all_res = requests.get(f"{API_BASE}/documents")
        if all_res.status_code == 200:
            all_docs = all_res.json()
            st.dataframe(
                [
                    {
                        "ID": d["id"],
                        "Filename": d["filename"],
                        "Type": d["doc_type"],
                        "Status": d["status"],
                        "Needs Human": "Yes" if d["requires_human_approval"] else "No",
                        "Created At": d["created_at"]
                    }
                    for d in all_docs
                ],
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Failed to load documents: {str(e)}")

# --- TAB 4: DOWNSTREAM TASKS ---
with tab_tasks:
    st.subheader("Dispatched Integration Tasks (ERP & IAM)")
    try:
        tasks_res = requests.get(f"{API_BASE}/tasks")
        if tasks_res.status_code == 200:
            tasks_list = tasks_res.json()
            if not tasks_list:
                st.info("No downstream tasks dispatched yet.")
            else:
                for t in tasks_list:
                    st.markdown(f"**Task ID:** `{t['id']}` | **Target System:** `{t['target_system']}` | **Type:** `{t['task_type']}` | **Status:** `{t['status']}`")
                    st.json(t["payload"])
                    st.divider()
    except Exception as e:
        st.error(f"Failed to load tasks: {str(e)}")
