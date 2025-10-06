import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
import logging
from utils.Tesseract_config import TESSERACT_CONFIG
from utils.utility_functions import preprocess_image


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str, preprocess: bool = True) -> str:
    """
    Extract text from PDF using Tesseract OCR

    Args:
        pdf_path: Path to PDF file
        preprocess: Whether to preprocess images before OCR

    Returns:
        Extracted text
    """
    try:
        logger.info(f"Converting PDF to images: {pdf_path}")

        # Convert PDF to images (300 DPI for better quality)
        images = convert_from_path(
            pdf_path,
            dpi=300,
            fmt='jpeg',
            thread_count=2
        )

        logger.info(f"PDF converted to {len(images)} page(s)")

        # OCR each page
        full_text = ""
        for i, image in enumerate(images):
            logger.info(f"Processing page {i+1}/{len(images)}")

            # Preprocess if enabled
            if preprocess:
                image = preprocess_image(image)

            # Apply OCR with German language pack
            page_text = pytesseract.image_to_string(
                image, config=TESSERACT_CONFIG)
            full_text += page_text + "\n\n"

            logger.info(
                f"Page {i+1} processed, extracted {len(page_text)} characters")

        logger.info(f"Total text extracted: {len(full_text)} characters")
        return full_text

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise Exception(f"Failed to process PDF: {str(e)}")


def extract_text_from_image(image_bytes: bytes, preprocess: bool = True) -> str:
    """
    Extract text from image using Tesseract OCR

    Args:
        image_bytes: Image file bytes
        preprocess: Whether to preprocess image before OCR

    Returns:
        Extracted text
    """
    try:
        logger.info("Loading image from bytes")
        image = Image.open(io.BytesIO(image_bytes))

        logger.info(f"Image loaded: {image.size} pixels, mode: {image.mode}")

        # Preprocess if enabled
        if preprocess:
            image = preprocess_image(image)

        # Apply OCR
        text = pytesseract.image_to_string(image, config=TESSERACT_CONFIG)

        logger.info(f"Text extracted: {len(text)} characters")
        return text

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise Exception(f"Failed to process image: {str(e)}")
