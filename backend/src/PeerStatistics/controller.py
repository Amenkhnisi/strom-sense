"""
API routes for peer statistics and comparison
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from .service import PeerService
from .schemas import PeerStatisticsResponse


router = APIRouter(
    prefix="/peers",
    tags=["Peer Statistics"]
)


@router.post("/calculate")
def calculate_peer_statistics(
    year: Optional[int] = Query(
        None, description="Specific year (leave empty for all)"),
    force_recalculate: bool = Query(False, description="Force recalculation"),
    db: Session = Depends(get_db)
):
    """
    Calculate peer statistics for all household groups.

    This should be run periodically or when new bills are added.

    Example: POST /peers/calculate?year=2024
    """

    service = PeerService(db)
    result = service.calculate_all_peer_statistics(year, force_recalculate)

    return {
        "message": "Peer statistics calculated successfully",
        "year": year or "all",
        "stats": result
    }


@router.get("/statistics/{household_size}/{year}")
def get_peer_statistics(
    household_size: int,
    year: int,
    property_type: Optional[str] = Query(None, pattern="^(apartment|house)$"),
    db: Session = Depends(get_db)
):
    """
    Get peer statistics for a specific group.

    Example: GET /peers/statistics/3/2024?property_type=apartment
    """

    if household_size < 1 or household_size > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Household size must be between 1 and 10"
        )

    service = PeerService(db)
    stats = service.get_peer_statistics(household_size, property_type, year)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No peer statistics found for {household_size}-person "
            f"{property_type or 'all'} households in {year}"
        )

    return {
        "household_size": stats.household_size,
        "property_type": stats.property_type or "all",
        "year": stats.year,
        "sample_size": stats.sample_size,
        "statistics": {
            "average_kwh": stats.avg_consumption_kwh,
            "median_kwh": stats.median_consumption_kwh,
            "std_deviation_kwh": stats.std_dev_consumption_kwh,
            "percentile_25_kwh": stats.percentile_25_kwh,
            "percentile_75_kwh": stats.percentile_75_kwh,
            "interquartile_range": stats.percentile_75_kwh - stats.percentile_25_kwh
        },
        "cost_statistics": {
            "average_cost_euros": stats.avg_cost_euros,
            "average_cost_per_kwh": stats.avg_cost_per_kwh
        }
    }


@router.get("/compare/{user_id}/{year}")
def compare_user_to_peers(
    user_id: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Compare a user's consumption to their peer group.

    Example: GET /peers/compare/1/2024

    Returns detailed comparison including z-score, percentile, etc.
    """

    service = PeerService(db)
    comparison = service.compare_to_peers(user_id, year)

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not compare user {user_id} for year {year}. "
            "User, bill, or peer data may be missing."
        )

    # Add interpretation
    z_score = comparison["z_score"]
    percent_diff = comparison["percent_difference"]

    if abs(z_score) <= 1:
        interpretation = "Your consumption is within normal range compared to similar households."
        emoji = "✅"
    elif abs(z_score) <= 2:
        if z_score > 0:
            interpretation = "Your consumption is moderately higher than similar households."
            emoji = "⚠️"
        else:
            interpretation = "Your consumption is moderately lower than similar households."
            emoji = "✅"
    else:
        if z_score > 0:
            interpretation = "Your consumption is significantly higher than similar households."
            emoji = "🔴"
        else:
            interpretation = "Your consumption is significantly lower than similar households."
            emoji = "🟢"

    comparison["interpretation"] = f"{emoji} {interpretation}"

    return comparison


@router.get("/groups")
def list_peer_groups(
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """
    List all available peer groups with their statistics.

    Example: GET /peers/groups?year=2024
    """

    service = PeerService(db)
    groups = service.get_all_peer_groups(year)

    if not groups:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No peer statistics available. Run POST /peers/calculate first."
        )

    return {
        "total_groups": len(groups),
        "groups": groups
    }


@router.get("/benchmark/{household_size}/{year}")
def get_benchmark_ranges(
    household_size: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get consumption benchmarks for a household size.

    Returns ranges for different performance levels.

    Example: GET /peers/benchmark/3/2024
    """

    service = PeerService(db)

    # Try apartment first
    stats_apt = service.get_peer_statistics(household_size, "apartment", year)
    stats_house = service.get_peer_statistics(household_size, "house", year)
    stats_all = service.get_peer_statistics(household_size, None, year)

    if not any([stats_apt, stats_house, stats_all]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No benchmark data for {household_size}-person households in {year}"
        )

    def create_ranges(stats):
        if not stats:
            return None

        return {
            "excellent": f"< {stats.percentile_25_kwh:.0f} kWh",
            "good": f"{stats.percentile_25_kwh:.0f} - {stats.avg_consumption_kwh:.0f} kWh",
            "average": f"{stats.avg_consumption_kwh:.0f} - {stats.percentile_75_kwh:.0f} kWh",
            "high": f"> {stats.percentile_75_kwh:.0f} kWh",
            "statistics": {
                "25th_percentile": stats.percentile_25_kwh,
                "average": stats.avg_consumption_kwh,
                "median": stats.median_consumption_kwh,
                "75th_percentile": stats.percentile_75_kwh
            }
        }

    return {
        "household_size": household_size,
        "year": year,
        "apartment": create_ranges(stats_apt),
        "house": create_ranges(stats_house),
        "all_types": create_ranges(stats_all)
    }
