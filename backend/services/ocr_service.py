import requests
from dotenv import load_dotenv
import os

load_dotenv()

OCR_API_URL = os.environ.get("OCR_API_URL")
OCR_API_KEY = os.environ.get("OCR_API_KEY")  # Replace with your actual key


def run_ocr(file_path: str) -> str:
    """
    Send file to OCR.space API and return raw extracted text.
    """
    with open(file_path, "rb") as f:
        response = requests.post(
            OCR_API_URL,
            files={"file": f},
            data={"apikey": OCR_API_KEY, "language": "ger"}
        )

    result = response.json()
    parsed_text = result.get("ParsedResults", [{}])[0].get("ParsedText", "")
    return parsed_text
