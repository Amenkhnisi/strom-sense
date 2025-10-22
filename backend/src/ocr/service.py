"""
Business logic for calculating bill metrics
"""

from sqlalchemy.orm import Session
from entities import UserBill, BillMetrics
from datetime import datetime
from typing import Optional, Dict


class MetricsService:
    """Service for calculating and managing bill metrics"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_for_bill(self, bill_id: int) -> Optional[BillMetrics]:
        """
        Calculate metrics for a single bill

        Args:
            bill_id: ID of the bill

        Returns:
            BillMetrics object or None if bill not found
        """
        # Get the bill
        bill = self.db.query(UserBill).filter(UserBill.id == bill_id).first()
        if not bill:
            return None

        # Calculate days in billing period
        days = (bill.billing_end_date - bill.billing_start_date).days

        # Calculate daily average
        daily_avg = bill.consumption_kwh / days if days > 0 else 0

        # Calculate cost per kWh
        cost_per_kwh = bill.total_cost_euros / \
            bill.consumption_kwh if bill.consumption_kwh > 0 else 0

        # Get previous year's bill for YoY comparison
        previous_bill = self.db.query(UserBill).filter(
            UserBill.user_id == bill.user_id,
            UserBill.bill_year == bill.bill_year - 1
        ).first()

        # Calculate year-over-year changes
        yoy_change = None
        prev_consumption = None

        if previous_bill:
            prev_consumption = previous_bill.consumption_kwh
            if prev_consumption > 0:
                yoy_change = (
                    (bill.consumption_kwh - prev_consumption) / prev_consumption) * 100

        # Check if metrics already exist
        existing = self.db.query(BillMetrics).filter(
            BillMetrics.bill_id == bill_id
        ).first()

        if existing:
            # Update existing
            existing.days_in_billing_period = days
            existing.daily_avg_consumption_kwh = round(daily_avg, 2)
            existing.cost_per_kwh = round(cost_per_kwh, 4)
            existing.yoy_consumption_change_percent = round(
                yoy_change, 2) if yoy_change else None
            existing.previous_year_consumption_kwh = round(
                prev_consumption, 2) if prev_consumption else None
            existing.calculated_at = datetime.utcnow()
            metrics = existing
        else:
            # Create new
            metrics = BillMetrics(
                bill_id=bill_id,
                days_in_billing_period=days,
                daily_avg_consumption_kwh=round(daily_avg, 2),
                cost_per_kwh=round(cost_per_kwh, 4),
                yoy_consumption_change_percent=round(
                    yoy_change, 2) if yoy_change else None,
                previous_year_consumption_kwh=round(
                    prev_consumption, 2) if prev_consumption else None
            )
            self.db.add(metrics)

        self.db.commit()
        self.db.refresh(metrics)

        return metrics

    def calculate_for_user(self, user_id: int) -> Dict[str, int]:
        """
        Calculate metrics for all bills of a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with counts of processed bills
        """
        bills = self.db.query(UserBill).filter(
            UserBill.user_id == user_id
        ).all()

        processed = 0
        errors = 0

        for bill in bills:
            try:
                self.calculate_for_bill(bill.id)
                processed += 1
            except Exception as e:
                print(f"Error calculating metrics for bill {bill.id}: {e}")
                errors += 1

        return {
            "total": len(bills),
            "processed": processed,
            "errors": errors
        }

    def get_metrics_by_bill_id(self, bill_id: int) -> Optional[BillMetrics]:
        """
        Get existing metrics for a bill

        Args:
            bill_id: Bill ID

        Returns:
            BillMetrics or None
        """
        return self.db.query(BillMetrics).filter(
            BillMetrics.bill_id == bill_id
        ).first()

    def recalculate_all(self) -> Dict[str, int]:
        """
        Recalculate metrics for ALL bills in database

        Returns:
            Dictionary with statistics
        """
        bills = self.db.query(UserBill).all()

        created = 0
        updated = 0
        errors = 0

        for bill in bills:
            try:
                existing = self.db.query(BillMetrics).filter(
                    BillMetrics.bill_id == bill.id
                ).first()

                self.calculate_for_bill(bill.id)

                if existing:
                    updated += 1
                else:
                    created += 1

            except Exception as e:
                print(f"Error processing bill {bill.id}: {e}")
                errors += 1

        return {
            "total": len(bills),
            "created": created,
            "updated": updated,
            "errors": errors
        }
