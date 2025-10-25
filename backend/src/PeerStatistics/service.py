"""
services/peer_service.py
Service for calculating and managing peer statistics
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from entities import UserProfile, UserBill, PeerStatistics
from datetime import datetime
from typing import Optional, Dict, List
import statistics


class PeerService:
    """Service for peer comparison and statistics"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_peer_statistics(
        self,
        household_size: int,
        property_type: Optional[str],
        year: int,
        min_sample_size: int = 3
    ) -> Optional[PeerStatistics]:
        """
        Calculate statistics for a peer group.

        Args:
            household_size: Number of people (1-5+)
            property_type: "apartment" or "house" (None for all)
            year: Year to calculate for
            min_sample_size: Minimum number of bills required

        Returns:
            PeerStatistics object or None if insufficient data
        """

        # Query bills matching criteria
        query = self.db.query(UserBill).join(
            UserProfile, UserBill.user_id == UserProfile.user_id
        ).filter(
            UserProfile.household_size == household_size,
            UserBill.bill_year == year
        )

        # Filter by property type if specified
        if property_type:
            query = query.filter(UserProfile.property_type == property_type)

        bills = query.all()

        # Check if we have enough samples
        if len(bills) < min_sample_size:
            print(
                f"⚠️  Insufficient data: {len(bills)} bills (need {min_sample_size})")
            return None

        # Extract consumption values
        consumptions = [bill.consumption_kwh for bill in bills]
        costs = [bill.total_cost_euros for bill in bills]

        # Calculate statistics
        avg_consumption = statistics.mean(consumptions)
        std_dev = statistics.stdev(consumptions) if len(
            consumptions) > 1 else 0
        median = statistics.median(consumptions)

        # Calculate percentiles
        sorted_consumptions = sorted(consumptions)
        percentile_25 = sorted_consumptions[len(sorted_consumptions) // 4]
        percentile_75 = sorted_consumptions[(
            len(sorted_consumptions) * 3) // 4]

        # Calculate cost statistics
        avg_cost = statistics.mean(costs) if costs else None
        avg_cost_per_kwh = (sum(costs) / sum(consumptions)
                            ) if sum(consumptions) > 0 else None

        # Check if statistics already exist
        existing = self.db.query(PeerStatistics).filter(
            PeerStatistics.household_size == household_size,
            PeerStatistics.property_type == property_type,
            PeerStatistics.year == year
        ).first()

        if existing:
            # Update existing
            existing.sample_size = len(bills)
            existing.avg_consumption_kwh = round(avg_consumption, 2)
            existing.std_dev_consumption_kwh = round(std_dev, 2)
            existing.median_consumption_kwh = round(median, 2)
            existing.percentile_25_kwh = round(percentile_25, 2)
            existing.percentile_75_kwh = round(percentile_75, 2)
            existing.avg_cost_euros = round(avg_cost, 2) if avg_cost else None
            existing.avg_cost_per_kwh = round(
                avg_cost_per_kwh, 4) if avg_cost_per_kwh else None
            existing.calculated_at = datetime.utcnow()
            stats = existing
        else:
            # Create new
            stats = PeerStatistics(
                household_size=household_size,
                property_type=property_type,
                year=year,
                sample_size=len(bills),
                avg_consumption_kwh=round(avg_consumption, 2),
                std_dev_consumption_kwh=round(std_dev, 2),
                median_consumption_kwh=round(median, 2),
                percentile_25_kwh=round(percentile_25, 2),
                percentile_75_kwh=round(percentile_75, 2),
                avg_cost_euros=round(avg_cost, 2) if avg_cost else None,
                avg_cost_per_kwh=round(
                    avg_cost_per_kwh, 4) if avg_cost_per_kwh else None
            )
            self.db.add(stats)

        self.db.commit()
        self.db.refresh(stats)

        return stats

    def calculate_all_peer_statistics(
        self,
        year: Optional[int] = None,
        force_recalculate: bool = False
    ) -> Dict[str, int]:
        """
        Calculate peer statistics for all combinations.

        Args:
            year: Specific year (None for all years with data)
            force_recalculate: Recalculate even if exists

        Returns:
            Dictionary with calculation results
        """

        print("\n" + "="*60)
        print("📊 CALCULATING PEER STATISTICS")
        print("="*60 + "\n")

        # Get all years if not specified
        if year is None:
            years = self.db.query(UserBill.bill_year).distinct().all()
            years = [y[0] for y in years]
        else:
            years = [year]

        # Get all unique household sizes
        household_sizes = self.db.query(
            UserProfile.household_size).distinct().all()
        household_sizes = [h[0] for h in household_sizes if h[0] is not None]

        # Property types to calculate
        property_types = ["apartment", "house", None]  # None = all types

        created = 0
        updated = 0
        skipped = 0
        errors = 0

        # Calculate for all combinations
        for year_val in years:
            print(f"Processing year {year_val}...")

            for household_size in household_sizes:
                for property_type in property_types:
                    try:
                        # Check if already exists
                        existing = self.db.query(PeerStatistics).filter(
                            PeerStatistics.household_size == household_size,
                            PeerStatistics.property_type == property_type,
                            PeerStatistics.year == year_val
                        ).first()

                        if existing and not force_recalculate:
                            skipped += 1
                            continue

                        # Calculate
                        stats = self.calculate_peer_statistics(
                            household_size, property_type, year_val
                        )

                        if stats:
                            if existing:
                                updated += 1
                            else:
                                created += 1

                    except Exception as e:
                        print(
                            f"❌ Error for {household_size}/{property_type}/{year_val}: {e}")
                        errors += 1

        print("\n" + "="*60)
        print("✨ PEER STATISTICS CALCULATION COMPLETE")
        print("="*60)
        print(f"\n📈 Results:")
        print(f"   Created: {created}")
        print(f"   Updated: {updated}")
        print(f"   Skipped: {skipped}")
        print(f"   Errors: {errors}")
        print()

        return {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": errors
        }

    def get_peer_statistics(
        self,
        household_size: int,
        property_type: Optional[str],
        year: int
    ) -> Optional[PeerStatistics]:
        """
        Get peer statistics for a specific group.

        Args:
            household_size: Number of people
            property_type: "apartment" or "house" or None
            year: Year

        Returns:
            PeerStatistics or None
        """

        return self.db.query(PeerStatistics).filter(
            PeerStatistics.household_size == household_size,
            PeerStatistics.property_type == property_type,
            PeerStatistics.year == year
        ).first()

    def compare_to_peers(
        self,
        user_id: int,
        bill_year: int
    ) -> Optional[Dict]:
        """
        Compare a user's consumption to their peer group.

        Args:
            user_id: User ID
            bill_year: Year of the bill

        Returns:
            Dictionary with comparison results
        """

        # Get user profile
        user = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not user:
            return None

        # Get user's bill
        bill = self.db.query(UserBill).filter(
            UserBill.user_id == user_id,
            UserBill.bill_year == bill_year
        ).first()

        if not bill:
            return None

        # Get peer statistics (try specific property type first)
        peer_stats = self.get_peer_statistics(
            user.household_size,
            user.property_type,
            bill_year
        )

        # Fallback to all property types if specific not available
        if not peer_stats:
            peer_stats = self.get_peer_statistics(
                user.household_size,
                None,
                bill_year
            )

        if not peer_stats:
            return None

        # Calculate comparison metrics
        user_consumption = bill.consumption_kwh
        peer_avg = peer_stats.avg_consumption_kwh
        peer_std_dev = peer_stats.std_dev_consumption_kwh

        # Calculate z-score (standard deviations from mean)
        z_score = (user_consumption - peer_avg) / \
            peer_std_dev if peer_std_dev > 0 else 0

        # Calculate percentage difference
        percent_diff = ((user_consumption - peer_avg) / peer_avg) * 100

        # Determine percentile
        percentile = None
        if user_consumption <= peer_stats.percentile_25_kwh:
            percentile = "bottom 25%"
        elif user_consumption >= peer_stats.percentile_75_kwh:
            percentile = "top 25%"
        else:
            percentile = "middle 50%"

        # Classification
        if abs(z_score) <= 1:
            classification = "normal"
        elif abs(z_score) <= 2:
            classification = "moderate_outlier"
        else:
            classification = "significant_outlier"

        return {
            "user_consumption_kwh": user_consumption,
            "peer_avg_kwh": peer_avg,
            "peer_median_kwh": peer_stats.median_consumption_kwh,
            "peer_std_dev_kwh": peer_std_dev,
            "difference_kwh": user_consumption - peer_avg,
            "percent_difference": round(percent_diff, 1),
            "z_score": round(z_score, 2),
            "percentile": percentile,
            "classification": classification,
            "peer_group": {
                "household_size": peer_stats.household_size,
                "property_type": peer_stats.property_type or "all",
                "sample_size": peer_stats.sample_size
            }
        }

    def get_all_peer_groups(self, year: Optional[int] = None) -> List[Dict]:
        """
        Get all available peer groups.

        Args:
            year: Filter by year (optional)

        Returns:
            List of peer group summaries
        """

        query = self.db.query(PeerStatistics)

        if year:
            query = query.filter(PeerStatistics.year == year)

        stats = query.order_by(
            PeerStatistics.year.desc(),
            PeerStatistics.household_size,
            PeerStatistics.property_type
        ).all()

        return [
            {
                "household_size": s.household_size,
                "property_type": s.property_type or "all",
                "year": s.year,
                "sample_size": s.sample_size,
                "avg_consumption_kwh": s.avg_consumption_kwh,
                "median_consumption_kwh": s.median_consumption_kwh,
                "range": f"{s.percentile_25_kwh:.0f} - {s.percentile_75_kwh:.0f} kWh"
            }
            for s in stats
        ]

    def calculate_peer_score(
        self,
        user_consumption: float,
        peer_avg: float,
        peer_std_dev: float
    ) -> float:
        """
        Calculate a peer comparison score (0-10).

        Higher score = more deviation from peers

        Args:
            user_consumption: User's consumption
            peer_avg: Peer average
            peer_std_dev: Peer standard deviation

        Returns:
            Score from 0-10
        """

        if peer_std_dev == 0:
            return 0

        # Calculate z-score
        z_score = abs((user_consumption - peer_avg) / peer_std_dev)

        # Map z-score to 0-10 scale
        # 0 std dev = 0 score
        # 1 std dev = 3 score
        # 2 std dev = 7 score
        # 3+ std dev = 10 score

        if z_score <= 1:
            score = z_score * 3
        elif z_score <= 2:
            score = 3 + (z_score - 1) * 4
        elif z_score <= 3:
            score = 7 + (z_score - 2) * 3
        else:
            score = 10

        return round(min(score, 10), 2)
