"""
tests/test_models.py
Test database models
"""

import pytest
from datetime import date
from entities import UserProfile, UserBill, BillMetrics, AnomalyDetection


class TestUserProfile:
    """Test UserProfile model"""

    def test_create_user(self, db_session):
        """Test creating a user"""
        user = UserProfile(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123",
            postal_code="10115",
            household_size=3,
            property_type="apartment",
            created_at=date.today()
        )
        db_session.add(user)
        db_session.commit()

        assert user.user_id is not None
        assert user.email == "test@example.com"
        assert user.household_size == 3

    def test_user_relationships(self, sample_user_with_bills):
        """Test user relationships with bills"""
        user, bills = sample_user_with_bills

        assert len(user.bills) == 2
        assert user.bills[0].user_id == user.user_id


class TestUserBill:
    """Test UserBill model"""

    def test_create_bill(self, db_session, sample_user):
        """Test creating a bill"""
        bill = UserBill(
            user_id=sample_user.user_id,
            bill_year=2024,
            consumption_kwh=3500.0,
            total_cost_euros=1225.0,
            billing_start_date=date(2023, 12, 15),
            billing_end_date=date(2024, 12, 14),
            tariff_rate=0.35
        )
        db_session.add(bill)
        db_session.commit()

        assert bill.id is not None
        assert bill.consumption_kwh == 3500.0
        assert bill.user.email == "test@example.com"

    def test_bill_relationships(self, sample_user_with_bills):
        """Test bill relationships"""
        user, bills = sample_user_with_bills

        assert bills[0].user == user
        assert bills[1].user == user


class TestBillMetrics:
    """Test BillMetrics model"""

    def test_create_metrics(self, db_session, sample_user_with_bills):
        """Test creating bill metrics"""
        user, bills = sample_user_with_bills

        metrics = BillMetrics(
            bill_id=bills[0].id,
            days_in_billing_period=365,
            daily_avg_consumption_kwh=8.77,
            cost_per_kwh=0.38,
            yoy_consumption_change_percent=None
        )
        db_session.add(metrics)
        db_session.commit()

        assert metrics.id is not None
        assert metrics.bill_id == bills[0].id
        assert metrics.daily_avg_consumption_kwh == 8.77


class TestAnomalyDetection:
    """Test AnomalyDetection model"""

    def test_create_anomaly(self, db_session, sample_user_with_bills):
        """Test creating an anomaly detection"""
        user, bills = sample_user_with_bills

        anomaly = AnomalyDetection(
            user_id=user.user_id,
            bill_id=bills[1].id,
            anomaly_type="consumption_spike",
            severity_level="critical",
            severity_score=8.5,
            current_consumption_kwh=4500.0,
            explanation_text="Test anomaly"
        )
        db_session.add(anomaly)
        db_session.commit()

        assert anomaly.id is not None
        assert anomaly.severity_level == "critical"
        assert anomaly.is_dismissed is False
