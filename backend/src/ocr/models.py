from pydantic import BaseModel, Field
from typing import Optional, Dict, Any,  List
from datetime import date

# Pydantic Models


class ParseTextRequest(BaseModel):
    text: str = Field(..., description="Raw text to parse", min_length=10)


class FieldValue(BaseModel):
    raw: Optional[str]
    normalized: Optional[Any]
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class BillingPeriod(BaseModel):
    start_date: Optional[date]
    end_date: Optional[date]


class ParsedInvoiceData(BaseModel):
    supplier: str
    supplierName: Optional[FieldValue]
    customerId: Optional[FieldValue]
    contractNumber: Optional[FieldValue]
    invoiceId: Optional[FieldValue]
    meterNumber: Optional[FieldValue]
    billingPeriod: Optional[FieldValue]
    totalConsumption: Optional[FieldValue]
    totalAmount: Optional[FieldValue]
    issueDate: Optional[FieldValue]
    additionalFields: Optional[Dict[str, FieldValue]] = {}


class OCRResponse(BaseModel):
    success: bool
    request_id: str
    timestamp: str
    raw_text: Optional[str] = None
    parsed_data: Optional[ParsedInvoiceData] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    tesseract_version: str
    supported_languages: List[str]
