"""
controllers/weather_controller.py
API routes for weather data
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from .service import WeatherService
from .schemas import WeatherCacheResponse


router = APIRouter(
    prefix="/weather",
    tags=["Weather"]
)


@router.get("/hdd/{postal_code}/{year}")
def get_heating_degree_days(
    postal_code: str,
    year: int,
    force_refresh: bool = Query(False, description="Force fetch from API"),
    db: Session = Depends(get_db)
):
    """
    Get heating degree days for a postal code and year

    Example: GET /weather/hdd/10115/2024
    """
    CURRENT_YEAR = 2025
    if year < 2020 or year > CURRENT_YEAR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=F"Year must be between 2000 and {CURRENT_YEAR}"
        )

    if len(postal_code) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid postal code"
        )

    service = WeatherService(db)
    hdd = service.get_heating_degree_days(
        postal_code, year, force_refresh)

    if hdd is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather data not available for {postal_code}/{year}"
        )

    return {
        "postal_code": postal_code,
        "year": year,
        "heating_degree_days": hdd["hdd"]if isinstance(hdd, dict) else hdd,
        "average_temperature_celsius": hdd["avg_temp"] if isinstance(hdd, dict) else None,
        "source": "cache" if not force_refresh else "api"
    }


@router.get("/adjustment-factor/{postal_code}")
def get_weather_adjustment(
    postal_code: str,
    current_year: int = Query(..., description="Current year"),
    previous_year: int = Query(..., description="Previous year"),
    db: Session = Depends(get_db)
):
    """
    Calculate weather adjustment factor between two years

    Example: GET /weather/adjustment-factor/10115?current_year=2024&previous_year=2023

    Returns:
        factor > 1.0: Current year was colder
        factor < 1.0: Current year was warmer
    """

    service = WeatherService(db)
    factor = service.calculate_weather_adjustment_factor(
        postal_code,
        current_year,
        previous_year
    )

    if factor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weather data not available for comparison"
        )

    current_hdd = service.get_heating_degree_days(postal_code, current_year)
    previous_hdd = service.get_heating_degree_days(postal_code, previous_year)

    return {
        "postal_code": postal_code,
        "current_year": current_year,
        "previous_year": previous_year,
        "current_hdd": current_hdd,
        "previous_hdd": previous_hdd,
        "adjustment_factor": factor,
        "interpretation": (
            f"{current_year} was {abs((factor - 1) * 100):.1f}% "
            f"{'colder' if factor > 1 else 'warmer'} than {previous_year}"
        )
    }


@router.post("/normalize-consumption")
def normalize_consumption(
    actual_consumption: float = Query(..., gt=0,
                                      description="Actual consumption in kWh"),
    postal_code: str = Query(..., description="Postal code"),
    actual_year: int = Query(..., description="Year of actual consumption"),
    baseline_year: int = Query(..., description="Year to normalize to"),
    db: Session = Depends(get_db)
):
    """
    Normalize consumption for weather differences

    Example: POST /weather/normalize-consumption?actual_consumption=4500&postal_code=10115&actual_year=2024&baseline_year=2023

    Returns what consumption would have been if weather was same as baseline
    """

    service = WeatherService(db)
    normalized = service.get_weather_normalized_consumption(
        actual_consumption,
        postal_code,
        actual_year,
        baseline_year
    )

    if normalized is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weather data not available for normalization"
        )

    factor = service.calculate_weather_adjustment_factor(
        postal_code,
        actual_year,
        baseline_year
    )

    return {
        "actual_consumption_kwh": actual_consumption,
        "normalized_consumption_kwh": normalized,
        "difference_kwh": round(actual_consumption - normalized, 2),
        "weather_adjustment_factor": factor,
        "explanation": (
            f"After adjusting for weather, consumption would have been "
            f"{normalized:.0f} kWh instead of {actual_consumption:.0f} kWh "
            f"if {actual_year} had the same weather as {baseline_year}"
        )
    }


@router.delete("/cache")
def clear_weather_cache(
    postal_code: Optional[str] = Query(
        None, description="Clear specific postal code"),
    year: Optional[int] = Query(None, description="Clear specific year"),
    db: Session = Depends(get_db)
):
    """
    Clear weather cache

    Examples:
    - DELETE /weather/cache (clear all)
    - DELETE /weather/cache?postal_code=10115 (clear postal code)
    - DELETE /weather/cache?year=2024 (clear year)
    """

    service = WeatherService(db)
    count = service.clear_cache(postal_code, year)

    return {
        "message": f"Cleared {count} cache entries",
        "postal_code": postal_code,
        "year": year
    }


@router.get("/cache", response_model=list)
def list_weather_cache(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List all cached weather data
    """
    from entities import WeatherCache

    cache_entries = db.query(WeatherCache).offset(skip).limit(limit).all()

    return [
        {
            "postal_code": entry.postal_code,
            "year": entry.year,
            "heating_degree_days": entry.heating_degree_days,
            "average_temperature_celsius": entry.average_temperature_celsius,
            "fetched_at": entry.fetched_at
        }
        for entry in cache_entries
    ]


@router.post("/prefetch")
def prefetch_weather_data(
    years: list[int] = Query(
        [2022, 2023, 2024], description="Years to prefetch"),
    db: Session = Depends(get_db)
):
    """
    Pre-fetch weather data for common German cities.
    This warms up the cache for better performance.

    Example: POST /weather/prefetch?years=2022&years=2023&years=2024
    """

    service = WeatherService(db)
    result = service.prefetch_common_locations(years)

    return {
        "message": "Weather data prefetch complete",
        "fetched": result["fetched"],
        "cached": result["cached"],
        "years": years
    }
