# central_parser.py
from typing import Dict, Any
from sqlalchemy.orm import Session
from .models import ParsedInvoiceData
from src.entities.ocr import Invoice
from .utils.utility_functions import normalize_field
from .utils.parser_patterns import GREEN_PATTERNS, SUPPLIERS
from .utils.parser_eon_refined import (
    EON_PATTERNS,
    clean_ocr_text,
    normalize_amount_german,
    normalize_kwh,
    parse_german_date,
    score_confidence,
)
import re


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


# Save bill data as invoice


def save_invoice_to_db(data: ParsedInvoiceData, db: Session) -> Invoice:
    billing_start, billing_end = normalize_field(
        data.billingPeriod, "billing_period")

    invoice = Invoice(
        supplier=data.supplier,
        supplier_raw=data.supplierName.raw if data.supplierName else None,
        supplier_confidence=data.supplierName.confidence if data.supplierName else None,

        customer_id=data.customerId.normalized if data.customerId else None,
        customer_raw=data.customerId.raw if data.customerId else None,
        customer_confidence=data.customerId.confidence if data.customerId else None,

        billing_start=billing_start,
        billing_end=billing_end,
        billing_raw=data.billingPeriod.raw if data.billingPeriod else None,
        billing_confidence=data.billingPeriod.confidence if data.billingPeriod else None,

        total_consumption=normalize_field(data.totalConsumption, "float"),
        consumption_raw=data.totalConsumption.raw if data.totalConsumption else None,
        consumption_confidence=data.totalConsumption.confidence if data.totalConsumption else None,

        total_amount=normalize_field(data.totalAmount, "float"),
        amount_raw=data.totalAmount.raw if data.totalAmount else None,
        amount_confidence=data.totalAmount.confidence if data.totalAmount else None,

        issue_date=normalize_field(data.issueDate, "date"),
        issue_raw=data.issueDate.raw if data.issueDate else None,
        issue_confidence=data.issueDate.confidence if data.issueDate else None,

        additional_fields=data.additionalFields or {}
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


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
