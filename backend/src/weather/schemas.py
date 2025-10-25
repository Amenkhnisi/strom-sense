from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ============= WEATHER CACHE SCHEMAS =============

class WeatherCacheResponse(BaseModel):
    id: int
    postal_code: str
    year: int
    heating_degree_days: float
    average_temperature_celsius: Optional[float]
    fetched_at: datetime

    class Config:
        from_attributes = True
