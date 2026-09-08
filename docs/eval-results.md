# Evaluation Report — Project 3: Document-to-Workflow Platform

**Evaluation Date:** 2026-09-08 07:31:25 UTC  
**Dataset:** 30 Held-out Documents (Invoices, IT Access Requests, Out-of-Scope)  
**Confidence Threshold:** 0.9  
**Invoice Auto-Approval Ceiling:** $1,000.00  

---

## Executive Metric Summary

| Metric | Measured Score | Target Threshold | Result |
|---|---|---|---|
| **Document Classification Accuracy** | **100.0%** | ≥ 90.0% | ✅ PASS |
| **Approval Gating Accuracy** | **100.0%** | ≥ 90.0% | ✅ PASS |
| **Field Extraction Accuracy** | **100.0%** | ≥ 85.0% | ✅ PASS |
| **False Auto-Approval Rate (Safety Ceiling)** | **0.0%** | ≤ 2.0% | ✅ PASS |
| **Mean Processing Latency** | **7.98 ms** | < 1500 ms | ✅ PASS |

---

## Per-Document Benchmark Breakdown

| ID | Filename | Expected Type | Actual Type | Expected Gate | Actual Gate | Match | Latency (ms) |
|---|---|---|---|---|---|---|---|
| doc01 | invoice_acme_office.txt | invoice | invoice | Auto-Approve | Auto-Approve | PASS | 43.12 |
| doc02 | invoice_apex_cloud.txt | invoice | invoice | Auto-Approve | Auto-Approve | PASS | 9.92 |
| doc03 | invoice_cloudflare_dns.txt | invoice | invoice | Auto-Approve | Auto-Approve | PASS | 10.29 |
| doc04 | invoice_slack_seats.txt | invoice | invoice | Auto-Approve | Auto-Approve | PASS | 9.67 |
| doc05 | invoice_github_enterprise.txt | invoice | invoice | Auto-Approve | Auto-Approve | PASS | 7.48 |
| doc06 | invoice_datadog_monitoring.txt | invoice | invoice | Auto-Approve | Auto-Approve | PASS | 8.88 |
| doc07 | invoice_dell_high_val.txt | invoice | invoice | Human Review | Human Review | PASS | 4.77 |
| doc08 | invoice_aws_heavy_compute.txt | invoice | invoice | Human Review | Human Review | PASS | 5.43 |
| doc09 | invoice_microsoft_ea.txt | invoice | invoice | Human Review | Human Review | PASS | 4.37 |
| doc10 | invoice_unverified_consulting.txt | invoice | invoice | Human Review | Human Review | PASS | 4.77 |
| doc11 | invoice_unverified_freelancer.txt | invoice | invoice | Human Review | Human Review | PASS | 4.49 |
| doc12 | invoice_atlassian_jira.txt | invoice | invoice | Auto-Approve | Auto-Approve | PASS | 8.41 |
| doc13 | access_salesforce_read.txt | access_request | access_request | Auto-Approve | Auto-Approve | PASS | 10.96 |
| doc14 | access_jira_write.txt | access_request | access_request | Auto-Approve | Auto-Approve | PASS | 10.59 |
| doc15 | access_github_read.txt | access_request | access_request | Auto-Approve | Auto-Approve | PASS | 9.16 |
| doc16 | access_snowflake_read.txt | access_request | access_request | Auto-Approve | Auto-Approve | PASS | 7.41 |
| doc17 | access_aws_admin.txt | access_request | access_request | Human Review | Human Review | PASS | 5.87 |
| doc18 | access_snowflake_admin.txt | access_request | access_request | Human Review | Human Review | PASS | 4.9 |
| doc19 | access_prod_db_admin.txt | access_request | access_request | Human Review | Human Review | PASS | 4.28 |
| doc20 | access_salesforce_write.txt | access_request | access_request | Auto-Approve | Auto-Approve | PASS | 8.16 |
| doc21 | access_kubernetes_admin.txt | access_request | access_request | Human Review | Human Review | PASS | 4.66 |
| doc22 | access_portal_read.txt | access_request | access_request | Auto-Approve | Auto-Approve | PASS | 7.79 |
| doc23 | invoice_zoom_video.txt | invoice | invoice | Auto-Approve | Auto-Approve | PASS | 7.38 |
| doc24 | invoice_dell_laptops.txt | invoice | invoice | Human Review | Human Review | PASS | 4.36 |
| doc25 | access_databricks_admin.txt | access_request | access_request | Human Review | Human Review | PASS | 4.9 |
| doc26 | access_jira_read.txt | access_request | access_request | Auto-Approve | Auto-Approve | PASS | 7.57 |
| doc27 | unknown_lunch_menu.txt | unknown | unknown | Human Review | Human Review | PASS | 5.39 |
| doc28 | unknown_office_party.txt | unknown | unknown | Human Review | Human Review | PASS | 4.68 |
| doc29 | unknown_release_notes.txt | unknown | unknown | Human Review | Human Review | PASS | 5.1 |
| doc30 | unknown_meeting_memo.txt | unknown | unknown | Human Review | Human Review | PASS | 4.64 |

---

## Key Findings & Reliability Analysis
1. **Zero False Auto-Approvals:** High-value invoices (>= $1,000), unverified vendor invoices, and admin-level access requests were 100% intercepted by the human approval checkpoint.
2. **Generalization Across Document Types:** The state machine successfully generalized across completely different data schemas (Invoices and IT Access Requests) without hardcoded format assumptions.
3. **Downstream Execution Integrity:** Downstream integration tasks to SAP ERP and Okta IAM were strictly prevented from dispatching whenever human approval was required until an explicit supervisor approval action was recorded.
