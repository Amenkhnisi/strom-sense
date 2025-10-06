from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from routes import ocr_pdf
import pytesseract
from models import HealthResponse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Energy Bill OCR Service",
    description="Microservice for extracting and parsing German energy bills using Tesseract OCR",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# add routes
app.include_router(ocr_pdf.route)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("=" * 70)
    logger.info("Energy Bill OCR Service Starting...")
    logger.info("=" * 70)

    try:
        # Check Tesseract availability
        version = pytesseract.get_tesseract_version()
        logger.info(f"✓ Tesseract version: {version}")

        # Check German language support
        languages = pytesseract.get_languages()
        if 'deu' in languages:
            logger.info("✓ German language pack (deu) available")
        else:
            logger.warning("⚠ German language pack (deu) not found!")

        logger.info(f"✓ Supported languages: {', '.join(languages)}")
        logger.info("✓ Service ready to accept requests")

    except Exception as e:
        logger.error(f"✗ Startup failed: {e}")
        raise

    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Energy Bill OCR Service shutting down...")


@app.get("/", response_model=HealthResponse, tags=["Api Health check"])
async def health():
    """
    Health check endpoint
    Returns service status and Tesseract information
    """
    try:
        tesseract_version = pytesseract.get_tesseract_version()

        # Get supported languages
        languages = pytesseract.get_languages()

        return HealthResponse(
            service="Energy Bill OCR Service",
            version="1.0.0",
            status="running",
            tesseract_version=str(tesseract_version),
            supported_languages=languages
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
