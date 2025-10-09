from fastapi import FastAPI, HTTPException, Request, Depends
import logging
from routes import ocr_pdf, ocr_image, ocr_text, invoice, auth
import pytesseract
from schemas import HealthResponse
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import os


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ENV = os.environ.get("ENV")

# Initialize FastAPI app
app = FastAPI(
    title="Energy Bill OCR Service",
    description="Microservice for extracting and parsing German energy bills using Tesseract OCR",
    version="1.0.0",
    docs_url="/docs" if ENV == "dev" else None,
    redoc_url="/redoc" if ENV == "dev" else None

)

# Protect routes


""" @app.get("/docs", include_in_schema=False)
def get_documentation(username: str = Depends(verify_credentials)):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="API Docs"
    )


@app.get("/redoc", include_in_schema=False)
def get_redoc(username: str = Depends(verify_credentials)):
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="ReDoc"
    )


@app.get("/openapi.json", include_in_schema=False)
def get_openapi(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    return app.openapi()
 """
# Global exception handler


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


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
app.include_router(ocr_image.route)
app.include_router(ocr_text.route)
app.include_router(invoice.route)
app.include_router(auth.router)


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
