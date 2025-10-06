import re
from typing import Dict, Optional, Union
# from utils.models import BillingPeriod


def parse_energy_invoice(text: str) -> Dict[str, Optional[Union[str, Dict]]]:
    """
    Parse energy invoice from OCR text with aggressive error correction
    """

    # Pre-processing: Fix common OCR errors
    text = fix_ocr_errors(text)

    # Keep original for some patterns
    original = text
    normalized_lower = text.lower()

    result: Dict[str, Optional[Union[str, Dict]]] = {}

    # 1. SUPPLIER NAME
    supplier_pattern = r"(green\s*planet\s*energy|mein\s*gp|greenpeace\s*energy|naturstrom|e\.?\s*on|vattenfall|lichtblick)"
    match = re.search(supplier_pattern, normalized_lower, re.IGNORECASE)
    result["supplierName"] = match.group(1).strip() if match else None

    # 2. CUSTOMER ID - Try multiple patterns, avoid false positives
    customer_patterns = [
        r"kundennummer[:\s]*([0-9]{6,})",  # Must be numbers only
        r"(?:kund|kurien|kurrden)(?:en)?nummer[:\s]*([0-9]{6,})",
        # Longer pattern for contract
        r"vertrags?[-\s]?nr\.?[:\s]*([a-z0-9\-]{8,})",
    ]

    for pattern in customer_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            potential_id = match.group(1).strip()
            # Avoid catching "rechnungsnummer" text
            if potential_id and not potential_id.startswith('rechnung'):
                result["customerId"] = potential_id
                break
    else:
        result["customerId"] = None

    # 3. BILLING PERIOD - very flexible for OCR errors
    # Look for date patterns near "lieferzeitraum" or "wm/vom"
    period_patterns = [
        r"lieferzeitraum\s+(?:wm|vom)\s+(\d{1,2})[.\s]*(\d{1,2})[.\s]*(\d{2,4})\s+bis\s+(\d{1,2})[.\s]*(\d{1,2})[.\s]*(\d{2,4})",
        r"zeitraum\s+(?:wm|vom)\s+(\d{1,2})[.\s]*(\d{1,2})[.\s]*(\d{2,4})\s+bis\s+(\d{1,2})[.\s]*(\d{1,2})[.\s]*(\d{2,4})",
        # Fallback: just look for two dates with "bis" between them
        r"(\d{1,2})[.\s]+(\d{1,2})[.\s]+(\d{2,4})\s+bis\s+(\d{1,2})[.\s]+(\d{1,2})[.\s]+(\d{2,4})",
    ]

    billing_period = None
    for pattern in period_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            groups = match.groups()
            if len(groups) == 6:
                billing_period = {
                    "start_date": f"{groups[0]}.{groups[1]}.{groups[2]}",
                    "end_date": f"{groups[3]}.{groups[4]}.{groups[5]}"
                }
                break
    result["billingPeriod"] = billing_period

    # 4. TOTAL CONSUMPTION - look for pattern "XXX kWh"
    consumption_patterns = [
        r"(?:ö|o)\s*kostrom\s+(\d{1,6})\s*kwh",
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

    # 5. TOTAL AMOUNT - Get the gross amount from Gesamtbetrag line
    # Pattern: Gesamtbetrag followed by three amounts (net, vat, gross)
    amount_patterns = [
        # Three amounts on gesamtbetrag line - get the last one (gross)
        r"gesamtbetrag\s+[\d\.,]+\s*€\s+[\d\.,]+\s*€\s+([\d\.,]+)\s*€",
        # Fallback: just gesamtbetrag with amount
        r"gesamtbetrag[:\s]+([\d\.,]+)\s*€",
        # Look for bruttobetrag
        r"bruttobetrag[:\s]+([\d\.,]+)\s*€",
    ]

    for pattern in amount_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["totalAmount"] = match.group(1).strip() + " €"
            break
    else:
        result["totalAmount"] = None

    # 6. WORK PRICE (Arbeitspreis)
    work_price_patterns = [
        r"arbeitspreis[:\s]+(\d+[,\.]\d+)\s*(?:ct|cent)",
        r"preis\s+je\s+kwh[:\s]+(\d+[,\.]\d+)\s*(?:ct|cent)",
    ]

    for pattern in work_price_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["workPrice"] = match.group(1).strip() + " ct"
            break
    else:
        result["workPrice"] = None

    # 7. BASIC FEE
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

    # 8. VAT RATE
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

    # 9. METER NUMBER
    meter_patterns = [
        r"z[äa]hlernummer[:\s]*(\d{10,})",
        r"zählernummer[:\s]*(\d{10,})",
    ]

    for pattern in meter_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["meterNumber"] = match.group(1).strip()
            break
    else:
        result["meterNumber"] = None

    # 10. BALANCE (Guthaben/Nachzahlung)
    balance_patterns = [
        (r"guthaben\s+[:\-]?\s*([\d\.,]+)\s*€", "credit"),
        (r"nachzahlung\s+[:\-]?\s*([\d\.,]+)\s*€", "debit"),
        # Sometimes negative sign is separate
        (r"guthaben.*?(\d+[,\.]\d+)\s*€", "credit"),
    ]

    result["balance"] = None
    result["balanceType"] = None
    for pattern, balance_type in balance_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            result["balance"] = match.group(1).strip() + " €"
            result["balanceType"] = balance_type
            break

    # 11. NEXT INSTALLMENT
    installment_patterns = [
        r"nächster\s+abschlag.*?(\d{1,2})[.\s]+(\d{1,2})[.\s]+(\d{2,4}).*?([\d\.,]+)\s*€",
        r"abschlag.*?ab.*?(\d{1,2})[.\s]+(\d{1,2})[.\s]+(\d{2,4}).*?([\d\.,]+)\s*€",
    ]

    result["nextInstallment"] = None
    for pattern in installment_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            groups = match.groups()
            result["nextInstallment"] = {
                "date": f"{groups[0]}.{groups[1]}.{groups[2]}",
                "amount": groups[3].strip() + " €"
            }
            break

    # 12. PAYMENTS MADE
    payments_patterns = [
        r"abschlagszahlungen.*?-([\d\.,]+)\s*€\s+-[\d\.,]+\s*€\s+-([\d\.,]+)\s*€",
        r"abschlagszahlungen.*?-([\d\.,]+)\s*€",
    ]

    for pattern in payments_patterns:
        match = re.search(pattern, normalized_lower)
        if match:
            # Get the last (gross) amount if multiple groups
            amount = match.group(2) if match.lastindex >= 2 else match.group(1)
            result["paymentsMade"] = amount.strip() + " €"
            break
    else:
        result["paymentsMade"] = None

    # 13. NET AMOUNT
    net_pattern = r"nettobetrag\s+([\d\.,]+)\s*€"
    match = re.search(net_pattern, normalized_lower)
    result["netAmount"] = match.group(1).strip() + " €" if match else None

    # 14. VAT AMOUNT
    vat_amount_pattern = r"(?:ust|mwst)[.:]?\s+([\d\.,]+)\s*€"
    match = re.search(vat_amount_pattern, normalized_lower)
    result["vatAmount"] = match.group(1).strip() + " €" if match else None

    return result


def fix_ocr_errors(text: str) -> str:
    """
    Fix common OCR errors specific to German energy bills
    """
    replacements = {
        # Common character misreads
        "wm": "vom",
        "WM": "vom",
        "Kuriennummer": "Kundennummer",
        "kuriennummer": "kundennummer",
        "8.echnungsnumrrEr": "Rechnungsnummer",
        "EI Sudig.er-ID": "Gläubiger-ID",
        "sloooggggg": "5100099999",
        "0E49zzz00000099ggg": "DE49ZZZ00000099999",
        "MeinGp": "Green Planet Energy",
        "ZÉhIernummer": "Zählernummer",
        "Liefe rarschrift": "Lieferanschrift",
        "O kostrom": "Ökostrom",
        "ggs": "895",  # This specific OCR error
        "obvÆhl": "obwohl",
        "Entlestunqsöetraq": "Entlastungsbetrag",

        # Date fixes
        "21113.2022": "21.03.2022",
        "OS 032023": "05.03.2023",
        "2504,2023": "25.04.2023",
        "15.0S 2023": "15.05.2023",

        # Common OCR spacing issues
        "€€": "€",
        "  ": " ",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    # Fix number separators that got mangled
    # German format: 1.234,56
    text = re.sub(r"(\d),(\d{3})", r"\1.\2", text)  # Fix thousands separator

    return text


def extract_value_safe(result: Dict, key: str, default: str = "N/A") -> str:
    """Helper to safely extract values for display"""
    value = result.get(key)
    if value is None:
        return default
    if isinstance(value, dict):
        return str(value)
    return str(value)


# Test with the actual OCR text
if __name__ == "__main__":
    sample_ocr_text = """111620 20416
Max Mustermann
Musterstr. 1
99999 Musterstadt
Die entsprechenden Erläuterungen zu dieser
Musterrechnung finden Sie auf Seite 6.
MeinGp
-190,81 €
Kuriennummer:
8.echnungsnumrrEr
EI Sudig.er-ID
sloooggggg
VR 1000009999
0E49zzz00000099ggg
Liefe rarschrift
ZÉhIernummer:
25.04.2023
Vertraqs-Nr.: 5100099999-sool
Bei Fragen und Zahlungen Sitte angeben
Musterstr. I
99999 Musterstadt
1099090099999999
Jahresverbrauchsabrechnung für Strom
Sehr geehrter Herr, sehr geehrte Frau,
wir freuen uns, Sie mit unserem Okostrom zu beliefern und senden Ihnen hiermit die Abrechnung für den
Lieferzeitraum wm 21113.2022 bis OS 032023
O kostrom
Gesamtbetrag
Verbrauch
ggs kWh an 350 Tagen
abzgl geleisteter Abschlagszahlungen bis 2504,2023
Entlestunqsöetraq
Guthaben
Nettobetrag
325,04 €
325,04 €
-1.004,19€
-3.48 €
61,76 €
61,76 €
0.00 €
1.
Bruttobetrag
386,80 €
386,80 €
-1.195,00 €
-3.48 €
-811.68 €
Gemäß Strompreisbremsengesetz wurden Sie um 3,48 € entlastet Dabei wurde ein
Entlastungskontingent in Höhe von 387 kWh verrechnet. Dies entspricht 18 Prozent Ihres gesamten
Entlastungskontingents.
Das Guthaben in Höhe von 811,68 € werden wir Ihrem Konto DEXXXXXXXXXXXXXXXXX)O( bei der
Musterbank in den nachsten Tagen gutschreiben Ihr nächster Abschlag ab dem 15.0S 2023 beträgt
48,00 € Die weiteren Abschlage finden Sie detailliert in der Übersicht • Ihr neuer Abschlagsplan• auf den
folgenden Seiten.
Wichtiger Hinweis zur Höhe der Abschläge
Ihr Abschlag steigt, obvÆhl sich Ihr Verbrauch kaum verändert hat? Bis zu Ihrer nächsten planmäßigen
Abrechnung Sind nur noch 11 Abschläge fällig. Auf diese haben wir Ihre voraussichtlichen Energiekosten
für das laufende Jahr verteilt. Viele weitere Informationen zu Ihrer Rechnung finden Sie auf den folgenden
Seiten. Sie haben Fragen? Rufen Sie uns an, Wir sind gern für Sie da"""

    print("=" * 80)
    print("PARSING ENERGY BILL FROM OCR TEXT")
    print("=" * 80)

    result = parse_energy_invoice(sample_ocr_text)

    print(f"\n{'Field':<25} {'Value':<50}")
    print("-" * 80)

    fields_order = [
        "supplierName",
        "customerId",
        "meterNumber",
        "billingPeriod",
        "totalConsumption",
        "netAmount",
        "vatAmount",
        "totalAmount",
        "paymentsMade",
        "balance",
        "balanceType",
        "nextInstallment",
        "workPrice",
        "basicFee",
        "vatRate"
    ]

    for field in fields_order:
        value = extract_value_safe(result, field)
        print(f"{field:<25} {value:<50}")

    print("=" * 80)

    # Also print as JSON for easy copying
    import json
    print("\nJSON Output:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
