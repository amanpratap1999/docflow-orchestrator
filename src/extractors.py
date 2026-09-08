import re
from typing import Dict, Any, Tuple, List

VERIFIED_VENDORS = [
    "acme corp", "acme supplies", "apex cloud services", "aws", "amazon web services",
    "dell technologies", "microsoft", "cloudflare", "slack technologies", "github",
    "datadog", "atlassian", "google cloud", "salesforce", "zoom video"
]

def extract_invoice_data(text: str) -> Tuple[Dict[str, Any], float]:
    """
    Extracts structured entities from an invoice document text.
    Returns (data_dict, confidence).
    """
    data: Dict[str, Any] = {
        "invoice_number": "",
        "vendor_name": "",
        "invoice_date": None,
        "due_date": None,
        "subtotal": None,
        "tax": None,
        "total_amount": 0.0,
        "currency": "USD",
        "line_items": [],
        "vendor_verified": False
    }

    confidence = 0.50

    # 1. Invoice Number
    code_match = re.search(r"\b(INV-[0-9A-Z\-]+)\b", text, re.IGNORECASE)
    if code_match:
        data["invoice_number"] = code_match.group(1).strip()
        confidence += 0.15
    else:
        inv_match = re.search(r"(?:invoice\s*(?:#|no\.?|number|id)\s*[:#]?|invoice\s*[:#])\s*([a-zA-Z0-9\-_]+)", text, re.IGNORECASE)
        if inv_match and inv_match.group(1).lower() not in ["date", "number", "id", "#", "invoice"]:
            data["invoice_number"] = inv_match.group(1).strip()
            confidence += 0.15
        else:
            data["invoice_number"] = "INV-UNKNOWN"

    # 2. Vendor Name
    vendor_match = re.search(r"(?:vendor|from|billed\s+by|remit\s+to|company)[:\s]+([^\n\r,]+)", text, re.IGNORECASE)
    if vendor_match:
        data["vendor_name"] = vendor_match.group(1).strip()
    else:
        # Check against known verified vendors appearing in text
        for v in VERIFIED_VENDORS:
            if re.search(r"\b" + re.escape(v) + r"\b", text, re.IGNORECASE):
                data["vendor_name"] = v.title()
                break
        if not data["vendor_name"]:
            # Pick first non-empty line
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if lines:
                data["vendor_name"] = lines[0][:40]

    if data["vendor_name"]:
        if "amazon web services" in data["vendor_name"].lower():
            data["vendor_name"] = "AWS"
        confidence += 0.10
        # Check if vendor is in verified list
        if any(v in data["vendor_name"].lower() for v in VERIFIED_VENDORS):
            data["vendor_verified"] = True
            confidence += 0.05

    # 3. Dates
    date_match = re.search(r"(?:invoice\s*date|date)[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})", text, re.IGNORECASE)
    if date_match:
        data["invoice_date"] = date_match.group(1).strip()

    due_match = re.search(r"(?:due\s*date)[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|Net\s*\d+)", text, re.IGNORECASE)
    if due_match:
        data["due_date"] = due_match.group(1).strip()

    # 4. Total Amount
    # First look for explicit compound markers: Total Amount, Total Due, Balance Due, Amount Due
    total_match = re.search(r"(?:total\s+amount|total\s+due|balance\s+due|amount\s+due)[:\s]*\$?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
    if not total_match:
        # Second, look for a standalone line starting with Total:
        total_match = re.search(r"(?:^|\n)\s*(?:total)[:\s]*\$?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)

    if total_match:
        try:
            val_str = total_match.group(1).replace(",", "")
            data["total_amount"] = float(val_str)
            confidence += 0.15
        except ValueError:
            data["total_amount"] = 0.0
    else:
        # Search for any standalone currency figure preceded by $
        amounts = re.findall(r"\$\s*([0-9,]+\.[0-9]{2})", text)
        if amounts:
            try:
                floats = [float(a.replace(",", "")) for a in amounts]
                data["total_amount"] = max(floats)
                confidence += 0.10
            except ValueError:
                data["total_amount"] = 0.0

    # 5. Subtotal and Tax
    sub_match = re.search(r"(?:subtotal|sub-total)[:\s]*\$?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
    if sub_match:
        try:
            data["subtotal"] = float(sub_match.group(1).replace(",", ""))
        except ValueError:
            pass

    tax_match = re.search(r"(?:tax|vat|sales\s*tax)[:\s]*\$?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
    if tax_match:
        try:
            data["tax"] = float(tax_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Mathematical consistency verification bonus
    if data["subtotal"] is not None and data["tax"] is not None and data["total_amount"] > 0:
        if abs((data["subtotal"] + data["tax"]) - data["total_amount"]) < 0.05:
            confidence += 0.05

    # 6. Line items heuristic
    # Match patterns like: "1x Server Hosting @ $120.00 = $120.00" or tabular line
    line_item_matches = re.findall(r"(?:^|\n)(?:[-*•]|\d+\.?)?\s*([A-Za-z0-9\s\-]+?)\s+(?:qty:?\s*(\d+)|(\d+)\s*x)?\s*\$?\s*([0-9,]+\.[0-9]{2})\s+\$?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
    for desc, q1, q2, price, tot in line_item_matches:
        try:
            qty = int(q1 or q2 or "1")
            u_price = float(price.replace(",", ""))
            t_price = float(tot.replace(",", ""))
            if len(desc.strip()) > 3:
                data["line_items"].append({
                    "description": desc.strip(),
                    "quantity": qty,
                    "unit_price": u_price,
                    "total": t_price
                })
        except ValueError:
            continue

    final_confidence = min(0.98, max(0.20, confidence))
    return data, round(final_confidence, 2)


def extract_access_request_data(text: str) -> Tuple[Dict[str, Any], float]:
    """
    Extracts structured entities from an IT access request document text.
    Returns (data_dict, confidence).
    """
    data: Dict[str, Any] = {
        "request_id": "",
        "employee_name": "",
        "employee_id": "",
        "department": "Engineering",
        "requested_system": "",
        "access_level": "read",
        "justification": ""
    }

    confidence = 0.50

    # 1. Request ID
    # 1. Request ID
    req_pattern = re.search(r"\b(REQ-[0-9A-Z\-]+)\b", text, re.IGNORECASE)
    if req_pattern:
        data["request_id"] = req_pattern.group(1).strip()
        confidence += 0.15
    else:
        req_match = re.search(r"(?:request\s*(?:#|id|number)\s*[:#]?|request\s*[:#])\s*([a-zA-Z0-9\-_]+)", text, re.IGNORECASE)
        if req_match and req_match.group(1).lower() not in ["access", "id", "number", "#", "system"]:
            data["request_id"] = req_match.group(1).strip()
            confidence += 0.15
        else:
            data["request_id"] = "REQ-UNKNOWN"

    # 2. Employee Name
    name_match = re.search(r"(?:employee(?:\s*name)?|requested\s*by|user|name)[:\s]+([^\n\r,]+)", text, re.IGNORECASE)
    if name_match:
        data["employee_name"] = name_match.group(1).strip()
        confidence += 0.10

    # 3. Employee ID
    emp_id_match = re.search(r"(?:employee\s*id|emp\s*id|badge\s*#?)[:\s]*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
    if emp_id_match:
        data["employee_id"] = emp_id_match.group(1).strip()
        confidence += 0.10
    else:
        data["employee_id"] = "EMP-UNKNOWN"

    # 4. Department
    dept_match = re.search(r"(?:department|dept|division)[:\s]*([^\n\r,]+)", text, re.IGNORECASE)
    if dept_match:
        data["department"] = dept_match.group(1).strip()

    # 5. Requested System
    system_match = re.search(r"(?:requested\s*system|target\s*system|system\s*name)[:\s]+([^\n\r,]+)", text, re.IGNORECASE)
    if system_match:
        data["requested_system"] = system_match.group(1).strip().upper()
        confidence += 0.10
    else:
        # Check known systems
        known_systems = ["aws", "snowflake", "salesforce", "github", "jira", "kubernetes", "databricks", "prod database", "internal portal"]
        for sys in known_systems:
            if re.search(r"\b" + re.escape(sys) + r"\b", text, re.IGNORECASE):
                data["requested_system"] = sys.upper()
                confidence += 0.10
                break

    # 6. Access Level
    if re.search(r"\b(admin|root|superuser|full\s*control|privileged)\b", text, re.IGNORECASE):
        data["access_level"] = "admin"
        confidence += 0.05
    elif re.search(r"\b(write|edit|modify|read-write|read/write)\b", text, re.IGNORECASE):
        data["access_level"] = "write"
        confidence += 0.05
    else:
        data["access_level"] = "read"
        confidence += 0.05

    # 7. Justification
    just_match = re.search(r"(?:justification|business\s*reason|reason)[:\s]*([^\n\r]+(?:\n[^\n\r]+)?)", text, re.IGNORECASE)
    if just_match:
        data["justification"] = just_match.group(1).strip()
    else:
        data["justification"] = "Standard onboarding role assignment."

    final_confidence = min(0.98, max(0.30, confidence))
    return data, round(final_confidence, 2)
