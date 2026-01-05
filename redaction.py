import re
from typing import List, Tuple

PATTERNS = {
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "PHONE": r"\b(?:\+?91[-\s]?)?[6-9]\d{9}\b",
    "PAN": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "AADHAAR": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "BANK_ACCT": r"\b\d{9,18}\b",
}

def redact_pii(text :str) -> Tuple[str, List[str]]:
    redacted_text = text
    notes : List[str] = []

    for label, pattern in PATTERNS.items():
        if re.search(pattern, text):
            redacted_text = re.sub(pattern, f"<{label}>", redacted_text)
            notes.append(f"Redacted {label}")
    
    return redacted_text, notes