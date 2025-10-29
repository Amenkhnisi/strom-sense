from ocr.models import UserBillResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# ============= ANOMALY DETECTION SCHEMAS =============

class AnomalyDetectionResponse(BaseModel):
    id: int
    user_id: int
    bill_id: int
    detection_date: datetime
    anomaly_type: str
    severity_level: str
    severity_score: float
    historical_score: Optional[float]
    peer_score: Optional[float]
    predictive_score: Optional[float]
    current_consumption_kwh: float
    comparison_value: Optional[float]
    deviation_percent: Optional[float]
    explanation_text: str
    recommendations_text: Optional[str]
    estimated_extra_cost_euros: Optional[float]
    is_dismissed: bool
    user_feedback: Optional[str]

    class Config:
        from_attributes = True


class AnomalyDismissRequest(BaseModel):
    """Request to dismiss an anomaly alert"""
    feedback: Optional[str] = None
    pass


# ============= COMBINED RESPONSE SCHEMAS =============


class UserBillWithAnomalies(UserBillResponse):
    """Bill with detected anomalies"""
    anomalies: List[AnomalyDetectionResponse] = []
