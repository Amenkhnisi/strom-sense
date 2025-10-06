from pydantic import BaseModel, Field
from typing import Optional, List

# Pydantic Models


class ParseTextRequest(BaseModel):
    text: str = Field(..., description="Raw text to parse", min_length=10)


class BillingPeriod(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class NextInstallment(BaseModel):
    date: Optional[str] = None
    amount: Optional[str] = None


class ParsedInvoiceData(BaseModel):
    supplierName: Optional[str] = None
    customerId: Optional[str] = None
    meterNumber: Optional[str] = None
    billingPeriod: Optional[BillingPeriod] = None
    totalConsumption: Optional[str] = None
    netAmount: Optional[str] = None
    vatAmount: Optional[str] = None
    totalAmount: Optional[str] = None
    paymentsMade: Optional[str] = None
    balance: Optional[str] = None
    balanceType: Optional[str] = None
    nextInstallment: Optional[NextInstallment] = None
    workPrice: Optional[str] = None
    basicFee: Optional[str] = None
    vatRate: Optional[str] = None


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
