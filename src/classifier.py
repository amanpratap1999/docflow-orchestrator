import re
from typing import Tuple

INVOICE_KEYWORDS = [
    r"\binvoice\b",
    r"\bbill to\b",
    r"\bremit to\b",
    r"\bsubtotal\b",
    r"\btax\b",
    r"\btotal amount\b",
    r"\btotal due\b",
    r"\bdue date\b",
    r"\bvendor\b",
    r"\bpayment terms\b",
    r"\bpo number\b",
    r"\bunit price\b",
    r"\bline item\b",
    r"\binvoice number\b",
    r"\binv-\d+\b",
]

ACCESS_REQUEST_KEYWORDS = [
    r"\baccess request\b",
    r"\bit request\b",
    r"\bsystem access\b",
    r"\bemployee id\b",
    r"\bdepartment\b",
    r"\baccess level\b",
    r"\badmin access\b",
    r"\bread access\b",
    r"\bwrite access\b",
    r"\bjustification\b",
    r"\bprovisioning\b",
    r"\brequest id\b",
    r"\breq-\d+\b",
    r"\bsecurity clearance\b",
    r"\bmanager sign-off\b",
]

def classify_document(text: str) -> Tuple[str, float]:
    """
    Classifies raw document text into 'invoice', 'access_request', or 'unknown'
    with an associated confidence score in [0.0, 1.0].
    """
    lower = text.lower()

    invoice_matches = sum(1 for kw in INVOICE_KEYWORDS if re.search(kw, lower))
    access_matches = sum(1 for kw in ACCESS_REQUEST_KEYWORDS if re.search(kw, lower))

    total_words = len(lower.split())
    if total_words < 5:
        return "unknown", 0.0

    # Strong discriminatory signals
    if re.search(r"\binvoice\b", lower) and invoice_matches >= 3 and invoice_matches > access_matches:
        confidence = min(0.98, 0.70 + (invoice_matches * 0.05))
        return "invoice", round(confidence, 2)

    if (re.search(r"\baccess request\b", lower) or re.search(r"\bsystem access\b", lower)) and access_matches >= 3 and access_matches > invoice_matches:
        confidence = min(0.98, 0.70 + (access_matches * 0.05))
        return "access_request", round(confidence, 2)

    # Moderate signals
    if invoice_matches >= 2 and invoice_matches > access_matches * 2:
        confidence = min(0.85, 0.60 + (invoice_matches * 0.05))
        return "invoice", round(confidence, 2)

    if access_matches >= 2 and access_matches > invoice_matches * 2:
        confidence = min(0.85, 0.60 + (access_matches * 0.05))
        return "access_request", round(confidence, 2)

    return "unknown", 0.30
