"""
Pytest configuration and fixtures
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import date

from database import Base, get_db
from main import app
from entities import UserProfile, UserBill, BillMetrics, PeerStatistics, WeatherCache


# Test database URL (use SQLite for testing)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============= TEST DATA FIXTURES =============


@pytest.fixture
def sample_user(db_session):
    """Create a sample user"""
    user = UserProfile(

        email="test@example.com",
        username="testuser",
        hashed_password="hashed_dummy_password",
        postal_code="10115",
        household_size=3,
        property_type="apartment",
        property_size_sqm=85.0,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_user_with_bills(db_session, sample_user):
    """Create a user with bills for 2023 and 2024"""
    bills = []

    # 2023 bill
    bill_2023 = UserBill(
        user_id=sample_user.user_id,
        bill_year=2023,
        consumption_kwh=3200.0,
        total_cost_euros=1216.0,
        billing_start_date=date(2022, 12, 15),
        billing_end_date=date(2023, 12, 14),
        tariff_rate=0.38
    )
    db_session.add(bill_2023)
    bills.append(bill_2023)

    # 2024 bill (with spike)
    bill_2024 = UserBill(
        user_id=sample_user.user_id,
        bill_year=2024,
        consumption_kwh=4500.0,
        total_cost_euros=1575.0,
        billing_start_date=date(2023, 12, 15),
        billing_end_date=date(2024, 12, 14),
        tariff_rate=0.35
    )
    db_session.add(bill_2024)
    bills.append(bill_2024)

    db_session.commit()
    for bill in bills:
        db_session.refresh(bill)

    return sample_user, bills


@pytest.fixture
def multiple_users_with_bills(db_session):
    """Create multiple users with bills for peer comparison"""
    users = []

    for i in range(5):
        user = UserProfile(
            email=f"user{i}@example.com",
            username=f"user{i}",
            hashed_password="hashed_dummy_password",
            postal_code="10115",
            household_size=3,
            property_type="apartment",
            property_size_sqm=80.0 + i * 5,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        db_session.flush()

        # Create 2024 bill with varying consumption
        bill = UserBill(
            user_id=user.user_id,
            bill_year=2024,
            consumption_kwh=3200.0 + i * 200,  # 3200, 3400, 3600, 3800, 4000
            total_cost_euros=(3200.0 + i * 200) * 0.35,
            billing_start_date=date(2023, 12, 15),
            billing_end_date=date(2024, 12, 14),
            tariff_rate=0.35
        )
        db_session.add(bill)
        users.append((user, bill))

    db_session.commit()
    return users


@pytest.fixture
def sample_weather_cache(db_session):
    """Create sample weather cache entries"""
    weather_entries = []

    for year in [2023, 2024]:
        entry = WeatherCache(
            postal_code="10115",
            year=year,
            heating_degree_days=2600.0 + (year - 2023) * 150,  # 2024 is colder
            average_temperature_celsius=10.5 - (year - 2023) * 0.5
        )
        db_session.add(entry)
        weather_entries.append(entry)

    db_session.commit()
    return weather_entries


@pytest.fixture
def sample_peer_statistics(db_session):
    """Create sample peer statistics"""
    stats = PeerStatistics(
        household_size=3,
        property_type="apartment",
        year=2024,
        sample_size=10,
        avg_consumption_kwh=3500.0,
        std_dev_consumption_kwh=600.0,
        median_consumption_kwh=3400.0,
        percentile_25_kwh=3000.0,
        percentile_75_kwh=4000.0
    )
    db_session.add(stats)
    db_session.commit()
    db_session.refresh(stats)
    return stats
