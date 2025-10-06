
from typing import Dict, Optional, Union
import re
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_ocr_errors(text: str) -> str:
    """Fix common OCR errors specific to German energy bills"""

    replacements = {
        # Common OCR misreads
        "wm": "vom",
        "WM": "vom",
        "Wm": "Vom",
        "Kuriennummer": "Kundennummer",
        "kuriennummer": "kundennummer",
        "Kurriennummer": "Kundennummer",
        "MeinGp": "Green Planet Energy",
        "mein gp": "green planet energy",
        "ZÉhIernummer": "Zählernummer",
        "Zahlernummer": "Zählernummer",
        "Liefe rarschrift": "Lieferanschrift",
        "O kostrom": "Ökostrom",
        "0kostrom": "Ökostrom",
        "Okostrom": "Ökostrom",
        "obvÆhl": "obwohl",
        "Entlestunqsöetraq": "Entlastungsbetrag",
        "Entlastunqsbetrag": "Entlastungsbetrag",
        "abzgl": "abzüglich",
        "Guthaben": "Guthaben",
        "Nachzahlung": "Nachzahlung",

        # Date fixes - common OCR date errors
        "OS": "05",
        "0S": "05",
        "O5": "05",
        "ol": "01",
        "Ol": "01",
    }

    # Apply replacements
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    # Fix common patterns with regex
    text = re.sub(r'\b0+kostrom\b', 'Ökostrom', text, flags=re.IGNORECASE)
    text = re.sub(r'\bO+kostrom\b', 'Ökostrom', text, flags=re.IGNORECASE)

    return text


def parse_energy_invoice(text: str) -> Dict[str, Optional[Union[str, Dict]]]:
    """
    Parse energy invoice from OCR text

    Args:
        text: Raw OCR text

    Returns:
        Dictionary with parsed invoice data
    """
    logger.info("Starting invoice parsing")

    # Fix OCR errors
    text = fix_ocr_errors(text)
    normalized_lower = text.lower()

    result: Dict[str, Optional[Union[str, Dict]]] = {}

    # 1. SUPPLIER NAME
    logger.debug("Parsing supplier name")
    supplier_pattern = r"(green\s*planet\s*energy|greenpeace\s*energy|naturstrom|e\.?\s*on|vattenfall|lichtblick|stadtwerke)"
    match = re.search(supplier_pattern, normalized_lower, re.IGNORECASE)
    result["supplierName"] = match.group(1).strip() if match else None

    # 2. CUSTOMER ID - numbers only to avoid false positives
    logger.debug("Parsing customer ID")
    customer_patterns = [
        r"kundennummer[:\s]*([0-9]{6,})",
        r"kunden[-\s]?nr\.?[:\s]*([0-9]{6,})",
        r"vertrags?[-\s]?nr\.?[:\s]*([a-z0-9\-]{8,})",
    ]

    for pattern in customer_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            potential_id = match.group(1).strip()
            # Avoid catching other keywords
            if potential_id and not any(x in potential_id for x in ['rechnung', 'zahler', 'glaub']):
                result["customerId"] = potential_id
                break
    else:
        result["customerId"] = None

    # 3. BILLING PERIOD
    logger.debug("Parsing billing period")
    period_patterns = [
        # Format: "Lieferzeitraum vom DD.MM.YYYY bis DD.MM.YYYY"
        r"lieferzeitraum\s+(?:vom|wm)\s+(\d{1,2})[.\s]*(\d{1,2})[.\s]*(\d{2,4})\s+bis\s+(\d{1,2})[.\s]*(\d{1,2})[.\s]*(\d{2,4})",
        # Format: "zeitraum vom DD.MM.YYYY bis DD.MM.YYYY"
        r"zeitraum\s+(?:vom|wm)\s+(\d{1,2})[.\s]*(\d{1,2})[.\s]*(\d{2,4})\s+bis\s+(\d{1,2})[.\s]*(\d{1,2})[.\s]*(\d{2,4})",
        # Fallback: just two dates with "bis"
        r"(\d{1,2})[.\s]+(\d{1,2})[.\s]+(\d{2,4})\s+bis\s+(\d{1,2})[.\s]+(\d{1,2})[.\s]+(\d{2,4})",
    ]

    billing_period = None
    for pattern in period_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            groups = match.groups()
            if len(groups) == 6:
                billing_period = {
                    "start_date": f"{groups[0].zfill(2)}.{groups[1].zfill(2)}.{groups[2]}",
                    "end_date": f"{groups[3].zfill(2)}.{groups[4].zfill(2)}.{groups[5]}"
                }
                break
    result["billingPeriod"] = billing_period

    # 4. TOTAL CONSUMPTION
    logger.debug("Parsing consumption")
    consumption_patterns = [
        r"(?:ö|o|oe)kostrom\s+(\d{1,6})\s*kwh",
        r"verbrauch[:\s]+(\d{1,6})\s*kwh",
        r"(\d{3,6})\s*kwh\s+an\s+\d+\s+tagen",
    ]

    for pattern in consumption_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["totalConsumption"] = match.group(1).strip()
            break
    else:
        result["totalConsumption"] = None

    # 5. TOTAL AMOUNT (Gross)
    logger.debug("Parsing total amount")
    amount_patterns = [
        # Three columns: net, vat, gross - get the last one
        r"gesamtbetrag\s+[\d\.,]+\s*€\s+[\d\.,]+\s*€\s+([\d\.,]+)\s*€",
        # Simple pattern
        r"gesamtbetrag[:\s]+([\d\.,]+)\s*€",
        r"bruttobetrag[:\s]+([\d\.,]+)\s*€",
    ]

    for pattern in amount_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["totalAmount"] = match.group(1).strip() + " €"
            break
    else:
        result["totalAmount"] = None

    # 6. NET AMOUNT
    logger.debug("Parsing net amount")
    net_pattern = r"nettobetrag\s+([\d\.,]+)\s*€"
    match = re.search(net_pattern, normalized_lower)
    result["netAmount"] = match.group(1).strip() + " €" if match else None

    # 7. VAT AMOUNT
    logger.debug("Parsing VAT amount")
    vat_amount_patterns = [
        r"(?:ust|mwst)[.:\s]+([\d\.,]+)\s*€",
        r"umsatzsteuer[:\s]+([\d\.,]+)\s*€",
    ]

    for pattern in vat_amount_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["vatAmount"] = match.group(1).strip() + " €"
            break
    else:
        result["vatAmount"] = None

    # 8. WORK PRICE (Arbeitspreis)
    logger.debug("Parsing work price")
    work_price_patterns = [
        r"arbeitspreis[:\s]+(\d+[,\.]\d+)\s*(?:ct|cent)",
        r"preis\s+je\s+kwh[:\s]+(\d+[,\.]\d+)\s*(?:ct|cent)",
        r"verbrauchspreis[:\s]+(\d+[,\.]\d+)\s*(?:ct|cent)",
    ]

    for pattern in work_price_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["workPrice"] = match.group(1).strip() + " ct"
            break
    else:
        result["workPrice"] = None

    # 9. BASIC FEE (Grundpreis)
    logger.debug("Parsing basic fee")
    basic_fee_patterns = [
        r"grundpreis[:\s]+(\d+[,\.]\d+)\s*€",
        r"grundgebühr[:\s]+(\d+[,\.]\d+)\s*€",
    ]

    for pattern in basic_fee_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["basicFee"] = match.group(1).strip() + " €"
            break
    else:
        result["basicFee"] = None

    # 10. VAT RATE
    logger.debug("Parsing VAT rate")
    vat_patterns = [
        r"(?:mwst|ust|mehrwertsteuer)[:\s]*(\d+[,\.]?\d*)\s*%",
        r"(\d+)\s*%\s*(?:mwst|ust)",
    ]

    for pattern in vat_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["vatRate"] = match.group(1).strip() + "%"
            break
    else:
        result["vatRate"] = None

    # 11. METER NUMBER
    logger.debug("Parsing meter number")
    meter_patterns = [
        r"z[äa]hlernummer[:\s]*(\d{10,})",
        r"zählernummer[:\s]*(\d{10,})",
        r"zahlernummer[:\s]*(\d{10,})",
    ]

    for pattern in meter_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["meterNumber"] = match.group(1).strip()
            break
    else:
        result["meterNumber"] = None

    # 12. BALANCE (Guthaben/Nachzahlung)
    logger.debug("Parsing balance")
    balance_patterns = [
        (r"guthaben\s*[:\-]?\s*([\d\.,]+)\s*€", "credit"),
        (r"nachzahlung\s*[:\-]?\s*([\d\.,]+)\s*€", "debit"),
        (r"zu\s+zahlen\s*[:\-]?\s*([\d\.,]+)\s*€", "debit"),
    ]

    result["balance"] = None
    result["balanceType"] = None
    for pattern, balance_type in balance_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["balance"] = match.group(1).strip() + " €"
            result["balanceType"] = balance_type
            break

    # 13. PAYMENTS MADE
    logger.debug("Parsing payments made")
    payments_patterns = [
        # Three columns, get last (gross)
        r"abschlagszahlungen.*?-[\d\.,]+\s*€\s+-[\d\.,]+\s*€\s+-([\d\.,]+)\s*€",
        # Simple pattern
        r"abschlagszahlungen.*?-([\d\.,]+)\s*€",
        r"gezahlte\s+abschläge.*?-([\d\.,]+)\s*€",
    ]

    for pattern in payments_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            amount = match.group(1).strip()
            result["paymentsMade"] = amount + " €"
            break
    else:
        result["paymentsMade"] = None

    # 14. NEXT INSTALLMENT
    logger.debug("Parsing next installment")
    installment_patterns = [
        r"nächster\s+abschlag.*?(\d{1,2})[.\s]+(\d{1,2})[.\s]+(\d{2,4}).*?([\d\.,]+)\s*€",
        r"abschlag.*?ab.*?(\d{1,2})[.\s]+(\d{1,2})[.\s]+(\d{2,4}).*?([\d\.,]+)\s*€",
        r"neuer\s+abschlag.*?(\d{1,2})[.\s]+(\d{1,2})[.\s]+(\d{2,4}).*?([\d\.,]+)\s*€",
    ]

    result["nextInstallment"] = None
    for pattern in installment_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            groups = match.groups()
            result["nextInstallment"] = {
                "date": f"{groups[0].zfill(2)}.{groups[1].zfill(2)}.{groups[2]}",
                "amount": groups[3].strip() + " €"
            }
            break

    logger.info("Parsing completed")
    return result
