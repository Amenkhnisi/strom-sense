"""
Test service layer business logic
"""

import pytest
from ocr import MetricsService
from PeerStatistics import PeerService
from weather import WeatherService
from AnomalyDetection import AnomalyDetectionService


class TestMetricsService:
    """Test MetricsService"""

    def test_calculate_for_bill(self, db_session, sample_user_with_bills):
        """Test calculating metrics for a bill"""
        user, bills = sample_user_with_bills
        service = MetricsService(db_session)

        metrics = service.calculate_for_bill(bills[0].id)

        assert metrics is not None
        assert metrics.bill_id == bills[0].id
        assert metrics.days_in_billing_period == 364
        assert metrics.daily_avg_consumption_kwh > 0
        assert metrics.cost_per_kwh > 0

    def test_calculate_yoy_change(self, db_session, sample_user_with_bills):
        """Test year-over-year calculation"""
        user, bills = sample_user_with_bills
        service = MetricsService(db_session)

        # Calculate for 2024 bill (should have YoY data)
        metrics = service.calculate_for_bill(bills[1].id)

        assert metrics.yoy_consumption_change_percent is not None
        assert metrics.previous_year_consumption_kwh == 3200.0
        # (4500 - 3200) / 3200 * 100 = 40.625%
        assert abs(metrics.yoy_consumption_change_percent - 40.625) < 0.1

    def test_calculate_for_user(self, db_session, sample_user_with_bills):
        """Test calculating metrics for all user bills"""
        user, bills = sample_user_with_bills
        service = MetricsService(db_session)

        result = service.calculate_for_user(user.user_id)

        assert result['total'] == 2
        assert result['processed'] == 2
        assert result['errors'] == 0


class TestPeerService:
    """Test PeerService"""

    def test_calculate_peer_statistics(self, db_session, multiple_users_with_bills):
        """Test calculating peer statistics"""
        service = PeerService(db_session)

        stats = service.calculate_peer_statistics(
            household_size=3,
            property_type="apartment",
            year=2024
        )

        assert stats is not None
        assert stats.sample_size == 5
        assert stats.avg_consumption_kwh > 0
        assert stats.std_dev_consumption_kwh > 0

    def test_compare_to_peers(self, db_session, multiple_users_with_bills, sample_peer_statistics):
        """Test comparing user to peers"""
        users = multiple_users_with_bills
        first_user = users[0][0]

        service = PeerService(db_session)
        comparison = service.compare_to_peers(first_user.user_id, 2024)

        assert comparison is not None
        assert 'user_consumption_kwh' in comparison
        assert 'peer_avg_kwh' in comparison
        assert 'z_score' in comparison
        assert 'percentile' in comparison

    def test_calculate_peer_score(self, db_session):
        """Test peer score calculation"""
        service = PeerService(db_session)

        # Test within 1 std dev (should be low score)
        score1 = service.calculate_peer_score(3500, 3400, 600)
        assert 0 <= score1 <= 3

        # Test 2 std devs away (should be higher score)
        score2 = service.calculate_peer_score(4600, 3400, 600)
        assert 7 <= score2 <= 9

        # Test 3+ std devs away (should be max score)
        score3 = service.calculate_peer_score(5200, 3400, 600)
        assert score3 == 10


class TestWeatherService:
    """Test WeatherService"""

    def test_get_heating_degree_days(self, db_session, sample_weather_cache):
        """Test getting HDD from cache"""
        service = WeatherService(db_session)

        hdd = service.get_heating_degree_days("10115", 2023)

        assert hdd is not None
        assert hdd == 2600.0

    def test_calculate_weather_adjustment_factor(self, db_session, sample_weather_cache):
        """Test weather adjustment factor calculation"""
        service = WeatherService(db_session)

        factor = service.calculate_weather_adjustment_factor(
            "10115", 2024, 2023)

        assert factor is not None
        # 2024 HDD (2750) / 2023 HDD (2600) = 1.058
        assert abs(factor - 1.058) < 0.01

    def test_get_weather_normalized_consumption(self, db_session, sample_weather_cache):
        """Test weather normalization"""
        service = WeatherService(db_session)

        normalized = service.get_weather_normalized_consumption(
            actual_consumption=4500,
            postal_code="10115",
            actual_year=2024,
            baseline_year=2023
        )

        assert normalized is not None
        assert normalized < 4500  # Should be lower after normalization


class TestAnomalyDetectionService:
    """Test AnomalyDetectionService"""

    def test_detect_historical_anomaly(self, db_session, sample_user_with_bills):
        """Test historical anomaly detection"""
        user, bills = sample_user_with_bills
        service = AnomalyDetectionService(db_session)

        # Calculate metrics first
        metrics_service = MetricsService(db_session)
        metrics_service.calculate_for_bill(bills[1].id)

        result = service.detect_historical_anomaly(bills[1].id)

        assert result is not None
        assert result['has_anomaly'] is True
        assert result['score'] > 5  # Should detect the spike
        assert result['anomaly_type'] == 'consumption_spike'

    def test_detect_peer_anomaly(self, db_session, sample_user_with_bills, sample_peer_statistics):
        """Test peer anomaly detection"""
        user, bills = sample_user_with_bills
        service = AnomalyDetectionService(db_session)

        result = service.detect_peer_anomaly(bills[1].id)

        assert result is not None
        assert 'score' in result
        assert 'z_score' in result

    def test_detect_predictive_anomaly(self, db_session, sample_user_with_bills, sample_weather_cache):
        """Test predictive anomaly detection"""
        user, bills = sample_user_with_bills
        service = AnomalyDetectionService(db_session)

        result = service.detect_predictive_anomaly(bills[1].id)

        assert result is not None
        assert 'score' in result
        assert 'expected_consumption' in result
        assert 'deviation_percent' in result

    def test_detect_all_anomalies(self, db_session, sample_user_with_bills, sample_weather_cache, sample_peer_statistics):
        """Test combined anomaly detection"""
        user, bills = sample_user_with_bills
        service = AnomalyDetectionService(db_session)

        # Calculate metrics first
        metrics_service = MetricsService(db_session)
        metrics_service.calculate_for_bill(bills[0].id)
        metrics_service.calculate_for_bill(bills[1].id)

        result = service.detect_all_anomalies(bills[1].id)

        assert result is not None
        assert 'has_anomaly' in result
        assert 'combined_score' in result
        assert 'severity' in result
        assert 'detector_scores' in result
        assert 'explanation' in result
        assert 'recommendations' in result

    def test_save_anomaly_detection(self, db_session, sample_user_with_bills, sample_weather_cache, sample_peer_statistics):
        """Test saving anomaly to database"""
        user, bills = sample_user_with_bills
        service = AnomalyDetectionService(db_session)

        # Calculate metrics
        metrics_service = MetricsService(db_session)
        metrics_service.calculate_for_bill(bills[0].id)
        metrics_service.calculate_for_bill(bills[1].id)

        # Detect
        result = service.detect_all_anomalies(bills[1].id)

        # Save
        anomaly = service.save_anomaly_detection(result)

        assert anomaly.id is not None
        assert anomaly.user_id == user.user_id
        assert anomaly.bill_id == bills[1].id
        assert anomaly.severity_score > 0

    def test_dismiss_anomaly(self, db_session, sample_user_with_bills, sample_weather_cache, sample_peer_statistics):
        """Test dismissing an anomaly"""
        user, bills = sample_user_with_bills
        service = AnomalyDetectionService(db_session)

        # Create and save anomaly
        metrics_service = MetricsService(db_session)
        metrics_service.calculate_for_bill(bills[0].id)
        metrics_service.calculate_for_bill(bills[1].id)

        result = service.detect_all_anomalies(bills[1].id)
        anomaly = service.save_anomaly_detection(result)

        # Dismiss
        dismissed = service.dismiss_anomaly(anomaly.id, feedback="helpful")

        assert dismissed is not None
        assert dismissed.is_dismissed is True
        assert dismissed.user_feedback == "helpful"
        assert dismissed.dismissed_at is not None
