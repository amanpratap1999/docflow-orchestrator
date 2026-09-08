import io
import re
from typing import Tuple
from pypdf import PdfReader

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyPDF."""
    text_parts = []
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    except Exception as e:
        return f"[PDF_EXTRACTION_ERROR: {str(e)}]"
    return "\n".join(text_parts).strip()

def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """Extract text from image bytes, trying pytesseract first, then fallback."""
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        if text.strip():
            return text.strip()
    except Exception:
        pass

    # Fallback: scan for any readable ASCII strings embedded in bytes
    try:
        matches = re.findall(rb'[ -~]{4,}', image_bytes)
        decoded = [m.decode('latin1', errors='ignore') for m in matches]
        return "\n".join(decoded).strip()
    except Exception:
        return ""

def process_document_bytes(filename: str, content: bytes) -> str:
    """Process uploaded file bytes based on filename extension."""
    lower_fn = filename.lower()
    if lower_fn.endswith(".pdf"):
        text = extract_text_from_pdf_bytes(content)
        if not text:
            # Fallback for scanned PDF without text layer
            return extract_text_from_image_bytes(content)
        return text
    elif lower_fn.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
        return extract_text_from_image_bytes(content)
    else:
        # Default to UTF-8 / latin1 text decode
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin1", errors="replace")
