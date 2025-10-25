from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ============= PEER STATISTICS SCHEMAS =============

class PeerStatisticsResponse(BaseModel):
    id: int
    household_size: int
    property_type: Optional[str]
    year: int
    sample_size: int
    avg_consumption_kwh: float
    std_dev_consumption_kwh: float
    calculated_at: datetime

    class Config:
        from_attributes = True
