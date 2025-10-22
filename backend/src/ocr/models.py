from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Optional, List, Union
from datetime import date, datetime


class UserBillCreate(BaseModel):
    user_id: int
    bill_year: int = Field(..., ge=2000, le=2100)
    consumption_kwh: float = Field(..., gt=0)
    total_cost_euros: float = Field(..., gt=0)
    billing_start_date: date
    billing_end_date: date
    tariff_rate: Optional[float] = Field(None, gt=0)

    @field_validator('billing_end_date')
    def end_after_start(cls, v, info: ValidationInfo):
        start_date = info.data.get('billing_start_date')
        if start_date and v <= start_date:
            raise ValueError(
                'Billing end date must be after billing start date')
        return v


class UserBillResponse(BaseModel):
    id: int
    user_id: int
    bill_year: int
    consumption_kwh: float
    total_cost_euros: float
    billing_start_date: date
    billing_end_date: date
    tariff_rate: Optional[float]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ============= BILL METRICS SCHEMAS =============

class BillMetricsResponse(BaseModel):
    id: int
    bill_id: int
    days_in_billing_period: int
    daily_avg_consumption_kwh: float
    cost_per_kwh: float
    yoy_consumption_change_percent: Optional[Union[float, str]]
    previous_year_consumption_kwh: Optional[Union[float,
                                                  str]]
    difference_kwh: Optional[Union[float, str]] = 0.0
    calculated_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }


# ============= COMBINED RESPONSE SCHEMAS =============

class UserBillWithMetrics(UserBillResponse):
    """Bill with calculated metrics"""
    metrics: Optional[dict] = None

# ============= HEALTH CHECK SCHEMA =============


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    tesseract_version: str
    supported_languages: List[str]
