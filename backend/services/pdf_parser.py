

from typing import Dict, Any, Optional
import requests
import re
from dotenv import load_dotenv
import os

load_dotenv()

OCR_API_URL = os.environ.get("OCR_API_URL")
OCR_API_KEY = os.environ.get("OCR_API_KEY")  # Replace with your actual key


def extract_text_from_ocr_space(file_path: str, language: str = "ger") -> str:
    """
    Send file to OCR.space API and return extracted text.
    """
    url = "https://api.ocr.space/parse/image"
    with open(file_path, "rb") as f:
        payload = {
            "apikey": OCR_API_KEY,
            "language": language,
            "isOverlayRequired": False,
        }
        files = {"file": f}
        response = requests.post(url, files=files, data=payload)
        response.raise_for_status()

    result = response.json()
    if result.get("IsErroredOnProcessing"):
        raise Exception(f"OCR.space error: {result.get('ErrorMessage')}")
    parsed_text = ""
    for item in result.get("ParsedResults", []):
        parsed_text += item.get("ParsedText", "")
    return parsed_text


""" def extract_text_from_ocr_space(file_bytes: bytes) -> str:
    response = requests.post(
        OCR_API_URL,
        files={"file": ("bill.pdf", file_bytes)},
        data={
            "apikey": OCR_API_KEY,
            "language": "ger",
            "isOverlayRequired": False,
        },
    )

    result = response.json()
    if result.get("IsErroredOnProcessing"):
        raise RuntimeError(f"OCR.space error: {result.get('ErrorMessage')}")

    parsed_results = result.get("ParsedResults", [])
    if not parsed_results:
        raise ValueError("No text found in OCR response.")

    return parsed_results[0].get("ParsedText", "")
 """

""" def extract_key_data(text: str) -> dict:
    data = {}

    # Normalize text
    clean_text = text.replace("\r", "").replace("\n", " ").lower()

    # 1. Monthly kWh – match all kWh values and sum them
    kwh_matches = re.findall(r"(\d{3,4})\s?kwh", clean_text)
    if kwh_matches:
        total_kwh = sum(int(kwh) for kwh in kwh_matches)
        data["monthly_kwh"] = total_kwh

    # 2. Billing date – match DD. Month YYYY or DD.MM.YYYY
    date_match = re.search(
        r"\b(\d{1,2}\.\s?[a-zäöü]+\.?\s?\d{4})\b", clean_text)
    if date_match:
        data["billing_date"] = date_match.group(1)

    # 3. Customer number – fuzzy match common OCR errors
    cust_match = re.search(r"kunden\w{4,8}[^\d]{0,10}(\d{6,12})", clean_text)

    if cust_match:
        data["customer_number"] = cust_match.group(2)

    # 4. Billing period – match full range
    period_match = re.search(
        r"vom\s+(\d{1,2}\.\s?[a-zäöü]+\.?\s?\d{4})\s+bis\s+(\d{1,2}\.\s?[a-zäöü]+\.?\s?\d{4})", clean_text)
    if period_match:
        data["billing_period"] = [period_match.group(1), period_match.group(2)]

    return data """


def normalize_number(value: str) -> float:
    if not value:
        return None
    value = value.replace(".", "").replace(",", ".")
    value = re.sub(r"[^\d.-]", "", value)
    try:
        return round(float(value), 2)
    except ValueError:
        return None


def extract_key_data(text: str) -> Dict[str, Optional[str]]:
    patterns = {
        "supplierName": r"(?:Greenpeace|Green Planet Energy|Lieferant|Anbieter)\s*(?:Enerqg|Energy)?",
        "customerId": r"(?:Kundenservice|Kundennummer|Vertrags[-\s]?Nr\.?)\s*[:\-]?\s*([\w\-]+)",
        "billingPeriod": r"(?:Lieferzeitraum *vom)\s*(\d{2}\.\d{2}\.\d{4})\s*(?:bis|–|-)\s*(\d{2}\.\d{2}\.\d{4})",
        "totalAmount": r"(?:Bruttobetrag|Gesamtbetrag|Guthaben)\s*[:\-]?\s*([\d\.,]+\s*€)",
        "totalConsumption": r"(?:Verbrauch)\s*([\d\.,]+)\s*kWh",
        "workPrice": r"(?:Arbeitspreis|Preis je kWh)\s*[:\-]?\s*([\d\.,]+\s*ct)?",
        "basicFee": r"(?:Grundpreis|Grundgebühr)\s*[:\-]?\s*([\d\.,]+\s*€)?",
        "vatRate": r"(?:MwSt|USt|Mehrwertsteuer)\s*[:\-]?\s*([\d\.,]+%)?"
    }

    result = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            if len(match.groups()) > 0:
                result[key] = match.groups()
                if len(result[key]) == 1:
                    result[key] = result[key][0]
            else:
                result[key] = match.group(0).strip()
        else:
            result[key] = None

    return result
