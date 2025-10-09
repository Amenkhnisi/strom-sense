# central_parser.py
import re
from typing import Dict, Any

from utils.parser_eon_refined import (
    EON_PATTERNS,
    clean_ocr_text,
    normalize_amount_german,
    normalize_kwh,
    parse_german_date,
    score_confidence,
)

# ------------------------
# Green Planet Energy regex (basic version)
# ------------------------
GREEN_PATTERNS = {
    "supplierName": re.compile(r"Green\s*Planet\s*Energy|Greenpeace\s*Energy", re.IGNORECASE),
    "customerId": re.compile(r"(?:Kundennr\.?|Kundennummer)\s*[:\-]?\s*([A-Z0-9\-]+)", re.IGNORECASE),
    "contractNumber": re.compile(r"(?:Vertragsnummer|Vertragskonto)\s*[:\-]?\s*([A-Z0-9\-]+)", re.IGNORECASE),
    "invoiceId": re.compile(r"(?:Rechnungsnummer|Rechn.-Nr\.?)\s*[:\-]?\s*([A-Z0-9\-]+)", re.IGNORECASE),
    "meterNumber": re.compile(r"(?:Z[äa]hler)\s*[:\-]?\s*([0-9\-]{3,40})", re.IGNORECASE),
    "billingPeriod": re.compile(
        r"(?:Zeitraum|Abrechnungszeitraum)\s*(?:vom)?\s*([0-3]?\d\.[01]?\d\.\d{4}).{0,40}?(?:bis)?\s*([0-3]?\d\.[01]?\d\.\d{4})",
        re.IGNORECASE,
    ),
    "totalConsumption": re.compile(r"([\d\.\,]+)\s*kWh", re.IGNORECASE),
    "totalAmount": re.compile(r"Gesamtbetrag.{0,20}?([\-–]?\s?[\d\.\,]+\s*€)", re.IGNORECASE),
    "issueDate": re.compile(r"(\d{1,2}\.\s*[A-Za-zÄÖÜäöüß]+\s*\d{4})", re.IGNORECASE),
}

SUPPLIERS = {
    "EON": EON_PATTERNS,
    "GREEN_PLANET": GREEN_PATTERNS,
}

# ------------------------
# Supplier detection
# ------------------------


def detect_supplier(text: str) -> str:
    if re.search(EON_PATTERNS["supplierName"], text):
        return "EON"
    if re.search(GREEN_PATTERNS["supplierName"], text):
        return "GREEN_PLANET"
    return "UNKNOWN"

# ------------------------
# Generic field parser
# ------------------------


def parse_invoice_text(raw_text: str) -> Dict[str, Any]:
    text = clean_ocr_text(raw_text)
    supplier = detect_supplier(text)
    patterns = SUPPLIERS.get(supplier, {})
    result: Dict[str, Any] = {"supplier": supplier, "fields": {}}

    for field, pattern in patterns.items():
        raw_match = None
        normalized = None
        conf = 0.0

        m = pattern.search(text)
        if m:
            try:
                raw_match = m.group(1).strip()
            except Exception:
                raw_match = m.group(0).strip()

            # normalization rules
            if field in ("totalAmount", "gutschrift"):
                normalized = normalize_amount_german(raw_match)
            elif field == "totalConsumption":
                normalized = normalize_kwh(raw_match)
            elif field == "issueDate":
                normalized = parse_german_date(raw_match)
            elif field == "billingPeriod":
                g = re.findall(
                    r"([0-3]?\d\.[01]?\d\.\d{4}|[0-3]?\d\.\s*[A-Za-zÄÖÜäöüß]+\s*\d{4})",
                    m.group(0),
                )
                if len(g) >= 2:
                    normalized = {
                        "start_date": parse_german_date(g[0]),
                        "end_date": parse_german_date(g[1]),
                    }
            else:
                normalized = raw_match

            conf = score_confidence(
                normalized, supplier_specific=(supplier != "UNKNOWN"))

        result["fields"][field] = {
            "raw": raw_match,
            "normalized": normalized,
            "confidence": round(conf, 3),
        }

    return result


# ------------------------
# Example test
# ------------------------
if __name__ == "__main__":
    # Replace this with the raw E.ON or Green Planet sample
    with open("eon_sample.txt", "r", encoding="utf-8") as f:
        text = f.read()

    parsed = parse_invoice_text(text)
    import pprint
    pprint.pprint(parsed)
