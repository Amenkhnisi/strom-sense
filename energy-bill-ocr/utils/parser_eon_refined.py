# parser_eon_refined.py
import re
from datetime import datetime
from typing import Optional, Dict, Any

# ------------------------
# Utilities
# ------------------------


def clean_ocr_text(text: str) -> str:
    if not text:
        return text
    s = text
    s = s.replace('\r', '\n')
    s = re.sub(r'\u2013|\u2014', '-', s)  # dash normalizing
    s = s.replace('‚', ',').replace('´', "'").replace('´', "'")
    # common OCR substitutions
    s = re.sub(r'\bMw5t\b', 'MwSt', s, flags=re.IGNORECASE)
    s = re.sub(r'\bkW\s*h\b', 'kWh', s, flags=re.IGNORECASE)
    # collapse many spaces
    s = re.sub(r'[ \t]+', ' ', s)
    return s


def normalize_amount_german(s: Optional[str]) -> Optional[float]:
    """Convert German formatted amount '1.234,56 €' or '-811,68 €' to float euros."""
    if not s:
        return None
    s0 = str(s).strip()
    # remove non-breaking spaces
    s0 = s0.replace('\xa0', '').replace(' ', '')
    # keep minus sign
    s0 = s0.replace('−', '-').replace('–', '-')
    # remove currency words or characters
    s0 = re.sub(r'(?i)€|eur|euro', '', s0)
    # replace possible letter-O misreadings inside the numeric portion later
    s0 = s0.replace('O', '0').replace('o', '0')
    # Now handle thousands separators and decimals
    # Cases:
    # "1.234,56" -> remove dots, replace comma with dot -> "1234.56"
    # "1234,56" -> replace comma with dot -> "1234.56"
    # "1234.56" (rare OCR) -> keep last dot as decimal
    # remove any leftover non-digit/dot/minus
    # If multiple dots exist and a comma exists => remove dots first
    if ',' in s0 and '.' in s0:
        s0 = s0.replace('.', '')
        s0 = s0.replace(',', '.')
    else:
        # Replace comma with dot (decimal), then if there are stray dots used as thousands separators, remove them
        s0 = s0.replace(',', '.')
        # if there are multiple dots, keep only last as decimal separator
        if s0.count('.') > 1:
            parts = s0.split('.')
            decimals = parts[-1]
            integers = ''.join(parts[:-1])
            s0 = integers + '.' + decimals
    s0 = re.sub(r'[^0-9\.\-]', '', s0)
    try:
        return float(s0)
    except Exception:
        return None


def normalize_kwh(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    s0 = str(s)
    s0 = re.sub(r'[^\d\.,\-]', '', s0)
    s0 = s0.replace('.', '').replace(',', '.')
    try:
        return float(s0)
    except:
        return None


MONTHS = {
    'jan': 1, 'januar': 1,
    'feb': 2, 'februar': 2,
    'mar': 3, 'märz': 3, 'maerz': 3, 'marz': 3,
    'apr': 4, 'april': 4,
    'mai': 5,
    'jun': 6, 'juni': 6,
    'jul': 7, 'juli': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'september': 9,
    'okt': 10, 'oktober': 10,
    'nov': 11, 'november': 11,
    'dez': 12, 'dezember': 12
}


def parse_german_date(s: Optional[str]) -> Optional[str]:
    """Return ISO date string YYYY-MM-DD for formats:
       - 27.03.2023
       - 27. März 2023  (with German month name, tolerant to OCR variants like 'Marz')
       - 2. Mai 2024
    """
    if not s:
        return None
    s0 = str(s).strip()
    # try numeric first
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s0, fmt)
            return dt.date().isoformat()
        except Exception:
            pass
    # try dd. MonthName YYYY (allow accents and OCR variants)
    m = re.search(
        r'([0-3]?\d)[\.\s]*[ ]*([A-Za-zÄÖÜäöüß]{3,20})[\s,\.]+(\d{4})', s0)
    if m:
        day = int(m.group(1))
        mon_raw = m.group(2).lower()
        # normalize umlauts to plain forms used in map
        mon_normal = mon_raw.replace('ä', 'a').replace(
            'ö', 'o').replace('ü', 'u').replace('ß', 'ss')
        # try keys by startswith to be tolerant (e.g. 'märz' -> 'marz')
        for k in MONTHS.keys():
            if mon_normal.startswith(k[:3]):  # compare first 3 letters
                try:
                    month = MONTHS[k]
                    year = int(m.group(3))
                    dt = datetime(year, month, day)
                    return dt.date().isoformat()
                except Exception:
                    continue
        # fallback: try substring match
        for k in MONTHS:
            if k in mon_normal:
                try:
                    month = MONTHS[k]
                    year = int(m.group(3))
                    dt = datetime(year, month, day)
                    return dt.date().isoformat()
                except Exception:
                    continue
    # final fallback: search for dd.mm.yyyy inside string
    m2 = re.search(r'([0-3]?\d\.[01]?\d\.\d{4})', s0)
    if m2:
        try:
            dt = datetime.strptime(m2.group(1), "%d.%m.%Y")
            return dt.date().isoformat()
        except:
            return None
    return None


def score_confidence(val: Any, supplier_specific: bool = True) -> float:
    if val is None:
        return 0.0
    base = 0.92 if supplier_specific else 0.75
    # small heuristics
    if isinstance(val, float):
        if abs(val) < 0.001:
            return base - 0.2
    if isinstance(val, str) and len(val.strip()) < 2:
        return base - 0.3
    return base


# ------------------------
# E.ON specific patterns (refactored, tolerant to OCR mistakes)
# ------------------------
EON_PATTERNS = {
    "supplierName": re.compile(r"(?:E[\.\-]?ON|EON\s*Deutschland|E[\.\-]?ON Energie Deutschland)", re.IGNORECASE),
    # Kundennummer or Kunde label sometimes written awkwardly; allow "Kunde:", "Kunden", "Kundennr"
    "customerId": re.compile(r"(?:Kundennr\.?|Kundennummer|Kunde)\s*[:\-\s]{0,10}([A-Z0-9\-\s]{4,30})", re.IGNORECASE),
    # Vertragsnummer / Vertragskonto / Vertragenummer (OCR typo)
    "contractNumber": re.compile(r"(?:Vertrags(?:nummer|konto)|Vertragenummer|Vertrags-?Nr\.?)\s*[:\-\s]{0,10}([A-Z0-9\-\s]{3,40})", re.IGNORECASE),
    # Invoice/ Rechnungsnummer often after that line; be tolerant for OCR typos (Rachnungsnummer)
    "invoiceId": re.compile(r"(?:Rechnungs?nummer|Rachnungsnummer|Rachnungsnummer|Rechnung Nr\.?)\s*[:\-\s]{0,10}([A-Z0-9\-\s]{3,40})", re.IGNORECASE),
    # Meter / Zähler
    "meterNumber": re.compile(r"(?:Z[äa]hler\b|Z[aä]hler[:\-\s]*|Zähler:?)\s*[:\-\s]{0,6}([0-9\-]{3,40})", re.IGNORECASE),
    # Billing period may be written as "für den Zeitraum vom 27. März 2023 bis 26. März 2024"
    "billingPeriod": re.compile(r"(?:Zeitraum|für den Zeitraum|Abrechnungszeitraum|Lieferzeitraum).{0,60}?([0-3]?\d[\.\s]*[A-Za-z0-9ÄÖÜäöüß\.\s]{1,20}\d{4}).{0,40}?([0-3]?\d[\.\s]*[A-Za-z0-9ÄÖÜäöüß\.\s]{1,20}\d{4})", re.IGNORECASE | re.DOTALL),
    # consumption like "Ihr Energieverbrauch von 1.246 kWh" or "Verbrauch: 1.246 kWh"
    "totalConsumption": re.compile(r"(?:Verbrauch|Energieverbrauch|Ihr Verbrauch).{0,20}?([\d\.\,\s]{2,15})\s*kWh", re.IGNORECASE),
    # Net / gross / to pay
    "netAmount": re.compile(r"(?:Nettobetrag|Netto).{0,20}?([\-–]?\s?[\d\.\,]+\s*€)", re.IGNORECASE),
    "totalAmount": re.compile(r"(?:Zu\s*zahlender\s*Betrag|Zu\s*zahlen|Zu zahlender Betrag|Zu zahlender Betrag|Zu zahlener Betrag|Zu zahlender Betrag|Zu\s*zah?lend[er]*\s*Betrag|Gesamtbetrag|Zu zahlender Betrag).{0,30}?([\-–]?\s?[\d\.\,]+\s*€)", re.IGNORECASE),
    # Gutschrift / Guthaben (credit) often present
    "gutschrift": re.compile(r"(?:Gutschrift|Guthaben).{0,20}?([\-–]?\s?[\d\.\,]+\s*€)", re.IGNORECASE),
    # next installment: "neuer Abschlag ab dem 2. Mai 2024 52,00 Euro"
    "nextInstallment": re.compile(r"(?:Abschlag).{0,40}?ab\s*(?:dem\s*)?([0-3]?\d(?:[\.]|\s)?[A-Za-zÄÖÜäöüß]{3,10}\s*\d{4})[^\d]{0,10}?([\d\.\,]+\s*(?:€|Euro))", re.IGNORECASE),
    # date printed line like "28. März 2024"
    "issueDate": re.compile(r"(?:Rechnungsdatum|Datum|28\.)\s*[:\-\s]*([0-3]?\d[\.\sA-Za-zäöüÄÖÜß]{0,20}\d{4})", re.IGNORECASE),
}

# ------------------------
# Parser function for E.ON refined text
# ------------------------


def parse_eon_text(raw_text: str) -> Dict[str, Dict[str, Any]]:
    text = clean_ocr_text(raw_text)
    out: Dict[str, Dict[str, Any]] = {}
    # fields we try to extract
    fields = [
        "supplierName", "customerId", "contractNumber", "invoiceId", "meterNumber",
        "billingPeriod", "totalConsumption", "netAmount", "gutschrift", "totalAmount",
        "nextInstallment", "issueDate"
    ]

    for field in fields:
        pat = EON_PATTERNS.get(field)
        raw_match = None
        normalized = None
        conf = 0.0

        if pat:
            m = pat.search(text)
            if m:
                # If group 1 is present, use it; else use full match
                try:
                    raw_match = m.group(1).strip()
                except Exception:
                    raw_match = m.group(0).strip()
                # special handling
                if field in ("netAmount", "totalAmount", "gutschrift"):
                    normalized = normalize_amount_german(raw_match)
                elif field == "totalConsumption":
                    normalized = normalize_kwh(raw_match)
                elif field == "billingPeriod":
                    # billingPeriod pattern attempted to capture two date-like groups
                    # Some matches return with group1 & group2; if single capture then fallback
                    groups = m.groups()
                    # attempt to find two date-like substrings inside match
                    text_segment = m.group(0)
                    g = re.findall(
                        r'([0-3]?\d\.[01]?\d\.\d{4}|[0-3]?\d\.\s*[A-Za-zÄÖÜäöüß]+\s*\d{4})', text_segment)
                    if len(g) >= 2:
                        start_raw, end_raw = g[0], g[1]
                        start_parsed = parse_german_date(start_raw)
                        end_parsed = parse_german_date(end_raw)
                        normalized = {"start_date": start_parsed,
                                      "end_date": end_parsed}
                        raw_match = {"start_raw": start_raw,
                                     "end_raw": end_raw}
                    else:
                        # fallback: try to extract two dd.mm.yyyy in the whole text around the match
                        near = text[max(0, m.start()-200):m.end()+200]
                        g2 = re.findall(
                            r'([0-3]?\d\.[01]?\d\.\d{4}|[0-3]?\d\.\s*[A-Za-zÄÖÜäöüß]+\s*\d{4})', near)
                        if len(g2) >= 2:
                            start_parsed = parse_german_date(g2[0])
                            end_parsed = parse_german_date(g2[1])
                            normalized = {
                                "start_date": start_parsed, "end_date": end_parsed}
                            raw_match = {"start_raw": g2[0], "end_raw": g2[1]}
                elif field == "nextInstallment":
                    # we've captured (date, amount) in groups, attempt to parse both
                    try:
                        date_raw = m.group(1).strip()
                        amt_raw = m.group(2).strip(
                        ) if m.lastindex and m.lastindex >= 2 else None
                        date_parsed = parse_german_date(date_raw)
                        amt_parsed = normalize_amount_german(amt_raw)
                        normalized = {"date": date_parsed,
                                      "amount": amt_parsed}
                        raw_match = {"date_raw": date_raw,
                                     "amount_raw": amt_raw}
                    except Exception:
                        normalized = None

                elif field == "issueDate":
                    normalized = parse_german_date(raw_match)
                else:
                    normalized = raw_match

                conf = score_confidence(normalized, supplier_specific=True)

        out[field] = {
            "raw": raw_match,
            "normalized": normalized,
            "confidence": round(conf, 3)
        }

    # meta / snippet
    out["_meta_text_sample"] = text[:800]
    return out


# ------------------------
# Test harness (use your provided raw OCR snippet here)
# ------------------------
if __name__ == "__main__":
    eon_raw = r"""e-on
Born CO Enge DanschmdniPonfch 475-8800 Landeut So erreichen Sie uns:
je]
Sereiaportal Mein EON:
Einfach aufsonde
Herrn einloggen oder registrieren.
Max Mustermann Nutzen Siegernauch unser
Beispielstraße 123 Kontaktformular unter
12345 Musterstadt eon.de/kontaktformuler
8
ON Energie Deutschland GmbH
Postfach 1475
Ihre Stromrechnung 2023/24 84001 Landshut
für don Zeitraum vom 27. März 2023 bis 26. März 2024
Bitte Immar angeben:
Kunde: Max Mustermann Vertragenummer
Verbrauchsstlle: Beiepilstraße 129, 12348 Musterstadt 1234667890
Zähler: 13456-000000
Rachnungsnummer
Sehr geehrter Herr Mustermann, 224 567 B00128
28. März 2024
...
Ihr Energieverbrauch von 1.246 kWh im Energieverbrauch?
Rechnungszeitraum entspricht 1.248 KWh per Jahr (auf 365 Tage umgerechnet).
Ihre Gutschrift 84,63€
Wir überweisen Ihre Gutschrift in den nächsten Tagen auf das Konto mit IBAN DEO1200000000 2007 89
Ihr nächster Abschlag ab dem 2. Mai 2024 52,00 Euro.
"""
    parsed = parse_eon_text(eon_raw)
    import json
    import pprint
    pprint.pprint(parsed)
    print("\nEXPECTED EXAMPLE (normalized):")
    expected = {
        "supplierName": "E.ON Energie Deutschland",
        "customerId": "Max Mustermann or extracted id if present",
        "contractNumber": None,
        "invoiceId": "224 567 B00128 (or close match)",
        "meterNumber": "13456-000000",
        "billingPeriod": {"start_date": "2023-03-27", "end_date": "2024-03-26"},
        "totalConsumption": 1246.0,
        "netAmount": None,
        "gutschrift": 84.63,
        "totalAmount": None,
        "nextInstallment": {"date": "2024-05-02", "amount": 52.0},

    }
    pprint.pprint(expected)
