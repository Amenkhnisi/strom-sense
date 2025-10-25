from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from src.AnomalyDetection.schemas import AnomalyDetectionResponse
from src.ocr.models import UserBillResponse


class UserProfileCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    hashed_password: str = Field(..., min_length=8)
    postal_code: int = Field(..., ge=10000, le=99999,
                             description="5-digit postal code")
    household_size: Optional[int] = Field(None, ge=1, le=10)
    property_type: Optional[str] = Field(None, pattern="^(apartment|house)$")
    property_size_sqm: Optional[float] = Field(None, gt=0)


class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr]
    username: Optional[str] = Field(..., min_length=3, max_length=50)
    hashed_password: Optional[str] = Field(..., min_length=8)
    postal_code: Optional[int] = Field(..., ge=10000, le=99999)
    household_size: Optional[int] = Field(None, ge=1, le=10)
    property_type: Optional[str] = Field(None, pattern="^(apartment|house)$")
    property_size_sqm: Optional[float] = Field(None, gt=0)


class UserProfileResponse(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    postal_code: int
    household_size: Optional[int]
    property_type: Optional[str]
    property_size_sqm: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):

    user: UserProfileResponse
    latest_bill: Optional[UserBillResponse]
    active_anomalies: List[AnomalyDetectionResponse]
    total_bills_count: int
    metrics_summary: Optional[List[dict]]  # List of metrics summaries per bill


class OverallSummary(BaseModel):
    current_year: int
    current_year_consumption_kwh: float
    previous_year: int
    previous_year_consumption_kwh: float
    yoy_change_percent: float
    difference_kwh: float
    cost_change_euros: float
