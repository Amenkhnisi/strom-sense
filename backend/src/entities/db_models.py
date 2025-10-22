from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Boolean, Text, Date
from database.core import Base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


## Bill Metrics Entity ##
class BillMetrics(Base):
    """Pre-calculated metrics for faster anomaly detection"""
    __tablename__ = "bill_metrics"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("user_bills.id", ondelete="CASCADE"),
                     nullable=False, unique=True, index=True)

    # Basic calculations
    days_in_billing_period = Column(Integer, nullable=False)
    daily_avg_consumption_kwh = Column(Float, nullable=False)
    cost_per_kwh = Column(Float, nullable=False)

    # Year-over-year comparisons (null if no previous year)
    yoy_consumption_change_percent = Column(Float, nullable=True)
    previous_year_consumption_kwh = Column(Float, nullable=True)

    calculated_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    bill = relationship("UserBill", back_populates="metrics")


## Anomaly Detection Entity ##
class AnomalyDetection(Base):
    """Store detected anomalies with explanations"""
    __tablename__ = "anomaly_detections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "user_profiles.user_id", ondelete="CASCADE"), nullable=False, index=True)
    bill_id = Column(Integer, ForeignKey("user_bills.id"),
                     nullable=False, index=True)

    detection_date = Column(DateTime, default=datetime.now(timezone.utc))

    # Anomaly details
    # "consumption_spike", "peer_outlier", etc.
    anomaly_type = Column(String(50), nullable=False)
    # "normal", "warning", "critical"
    severity_level = Column(String(20), nullable=False, index=True)
    severity_score = Column(Float, nullable=False)  # 0-10

    # Individual detector scores
    historical_score = Column(Float, nullable=True)
    peer_score = Column(Float, nullable=True)
    predictive_score = Column(Float, nullable=True)

    # Comparison data
    current_consumption_kwh = Column(Float, nullable=False)
    comparison_value = Column(Float, nullable=True)
    deviation_percent = Column(Float, nullable=True)

    # User-facing content
    explanation_text = Column(Text, nullable=False)
    recommendations_text = Column(Text, nullable=True)
    estimated_extra_cost_euros = Column(Float, nullable=True)

    # User interaction
    is_dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserProfile", back_populates="anomalies")
    bill = relationship("UserBill", back_populates="anomalies")


## Weather Cache Entity ##
class WeatherCache(Base):
    """Cache weather data to avoid repeated API calls"""
    __tablename__ = "weather_cache"

    id = Column(Integer, primary_key=True, index=True)
    postal_code = Column(String(10), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)

    heating_degree_days = Column(Float, nullable=False)  # HDD value
    average_temperature_celsius = Column(Float, nullable=True)

    fetched_at = Column(DateTime, default=datetime.now(timezone.utc))


## Peer Statistics Entity ##
class PeerStatistics(Base):
    """Pre-calculated peer group statistics"""
    __tablename__ = "peer_statistics"

    id = Column(Integer, primary_key=True, index=True)

    # Peer group definition
    household_size = Column(Integer, nullable=False, index=True)
    property_type = Column(String(50), nullable=True)  # "apartment" or "house"
    year = Column(Integer, nullable=False, index=True)

    # Statistics
    sample_size = Column(Integer, nullable=False)
    avg_consumption_kwh = Column(Float, nullable=False)
    std_dev_consumption_kwh = Column(Float, nullable=False)

    calculated_at = Column(DateTime, default=datetime.now(timezone.utc))


## User Profile Entity ##
class UserProfile(Base):
    """Store basic user information"""
    __tablename__ = "user_profiles"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    postal_code = Column(Integer, nullable=False, index=True)
    household_size = Column(Integer, nullable=True)  # 1, 2, 3, 4, 5+
    property_type = Column(String(50), nullable=True)  # "apartment" or "house"
    property_size_sqm = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    bills = relationship('UserBill', back_populates="user",
                         cascade="all, delete")
    anomalies = relationship(
        'AnomalyDetection', back_populates="user", cascade="all, delete")


## User Bill Entity ##
class UserBill(Base):
    """Store extracted bill data from OCR"""
    __tablename__ = "user_bills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "user_profiles.user_id", ondelete="CASCADE"), nullable=False, index=True)

    # Core bill data (from OCR)
    bill_year = Column(Integer, nullable=False, index=True)
    bill_year_confidence = Column(Float)

    consumption_kwh = Column(Float, nullable=False)
    consumption_kwh_confidence = Column(Float)

    total_cost_euros = Column(Float, nullable=False)
    total_cost_euros_confidence = Column(Float)

    billing_start_date = Column(Date, nullable=False)
    billing_start_date_confidence = Column(Float)

    billing_end_date = Column(Date, nullable=False)
    billing_end_date_confidence = Column(Float)

    tariff_rate = Column(Float, nullable=True)  # euros per kWh
    tariff_rate_confidence = Column(Float)

    uploaded_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    user = relationship("UserProfile", back_populates="bills")
    metrics = relationship("BillMetrics", back_populates="bill",
                           uselist=False, cascade="all, delete")
    anomalies = relationship("AnomalyDetection", back_populates="bill")
