"""
Test API endpoints
"""

import pytest
from fastapi import status
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables for testing
API_VERSION = os.getenv("API_VERSION", "/api/v1")


class TestUserEndpoints:
    """Test user API endpoints"""

    def test_create_user(self, client):
        """Test POST /users/"""
        response = client.post(
            f"{API_VERSION}/users/",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "hashed_password": "securepassword",
                "postal_code": "10115",
                "household_size": 3,
                "property_type": "apartment",
                "property_size_sqm": 85.0,
                "created_at": "2024-01-15T10:00:00Z"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["user_id"] is not None

    def test_get_user(self, client, sample_user):
        """Test GET /users/{user_id}"""
        response = client.get(f"{API_VERSION}/users/{sample_user.user_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_user_not_found(self, client):
        """Test GET /users/{user_id} with invalid ID"""
        response = client.get(f"{API_VERSION}/users/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_users(self, client, sample_user):
        """Test GET /users/"""
        response = client.get(f"{API_VERSION}/users/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1

    def test_update_user(self, client, sample_user):
        """Test PATCH /users/{user_id}"""
        response = client.patch(
            f"{API_VERSION}/users/{sample_user.user_id}",
            json={"household_size": 4}
        )

        print(response.json())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["household_size"] == 4


class TestBillEndpoints:
    """Test bill API endpoints"""

    def test_create_bill(self, client, sample_user):
        """Test POST /bills/"""
        response = client.post(
            f"{API_VERSION}/bills/",
            json={
                "user_id": sample_user.user_id,
                "bill_year": 2024,
                "consumption_kwh": 3500.0,
                "total_cost_euros": 1225.0,
                "billing_start_date": "2023-12-15",
                "billing_end_date": "2024-12-14",
                "tariff_rate": 0.35
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["consumption_kwh"] == 3500.0
        assert data["id"] is not None

    def test_get_bill(self, client, sample_user_with_bills):
        """Test GET /bills/{bill_id}"""
        user, bills = sample_user_with_bills

        response = client.get(f"{API_VERSION}/bills/{bills[0].id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["consumption_kwh"] == 3200.0

    def test_get_user_bills(self, client, sample_user_with_bills):
        """Test GET /bills/user/{user_id}"""
        user, bills = sample_user_with_bills

        response = client.get(f"{API_VERSION}/bills/user/{user.user_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_calculate_bill_metrics(self, client, sample_user_with_bills):
        """Test POST /bills/{bill_id}/calculate-metrics"""
        user, bills = sample_user_with_bills

        response = client.post(
            f"{API_VERSION}/bills/{bills[0].id}/calculate-metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["days_in_billing_period"] > 0
        assert data["daily_avg_consumption_kwh"] > 0


class TestWeatherEndpoints:
    """Test weather API endpoints"""

    def test_get_hdd(self, client, sample_weather_cache):
        """Test GET /weather/hdd/{postal_code}/{year}"""
        response = client.get(f"{API_VERSION}/weather/hdd/10115/2023")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["heating_degree_days"] == 2600.0

    def test_get_weather_adjustment(self, client, sample_weather_cache):
        """Test GET /weather/adjustment-factor/{postal_code}"""
        response = client.get(
            f"{API_VERSION}/weather/adjustment-factor/10115",
            params={"current_year": 2024, "previous_year": 2023}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "adjustment_factor" in data
        assert data["adjustment_factor"] > 1.0  # 2024 is colder


class TestPeerEndpoints:
    """Test peer statistics API endpoints"""

    def test_calculate_peer_statistics(self, client, multiple_users_with_bills):
        """Test POST /peers/calculate"""
        response = client.post(
            f"{API_VERSION}/peers/calculate", params={"year": 2024})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "stats" in data
        assert data["stats"]["created"] > 0

    def test_get_peer_statistics(self, client, sample_peer_statistics):
        """Test GET /peers/statistics/{household_size}/{year}"""
        response = client.get(
            f"{API_VERSION}/peers/statistics/3/2024",
            params={"property_type": "apartment"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["household_size"] == 3
        assert data["statistics"]["average_kwh"] > 0

    def test_compare_user_to_peers(self, client, sample_user_with_bills, sample_peer_statistics):
        """Test GET /peers/compare/{user_id}/{year}"""
        user, bills = sample_user_with_bills

        response = client.get(
            f"{API_VERSION}/peers/compare/{user.user_id}/2024")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_consumption_kwh" in data
        assert "peer_avg_kwh" in data
        assert "z_score" in data


class TestAnomalyEndpoints:
    """Test anomaly detection API endpoints"""

    def test_detect_anomalies(self, client, sample_user_with_bills, sample_weather_cache, sample_peer_statistics):
        """Test POST /anomalies/detect/{bill_id}"""
        user, bills = sample_user_with_bills

        # Calculate metrics first
        client.post(f"{API_VERSION}/bills/{bills[0].id}/calculate-metrics")
        client.post(f"{API_VERSION}/bills/{bills[1].id}/calculate-metrics")

        response = client.post(f"{API_VERSION}/anomalies/detect/{bills[1].id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "has_anomaly" in data
        assert "combined_score" in data
        assert "severity" in data
        assert "explanation" in data

    def test_detect_user_anomalies(self, client, sample_user_with_bills, sample_weather_cache, sample_peer_statistics):
        """Test POST /anomalies/detect/user/{user_id}"""
        user, bills = sample_user_with_bills

        # Calculate metrics
        client.post(f"{API_VERSION}/bills/{bills[0].id}/calculate-metrics")
        client.post(f"{API_VERSION}/bills/{bills[1].id}/calculate-metrics")

        response = client.post(
            f"{API_VERSION}/anomalies/detect/user/{user.user_id}",
            params={"year": 2024}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == user.user_id
        assert data["total_bills_checked"] >= 1

    def test_get_user_anomalies(self, client, sample_user_with_bills, sample_weather_cache, sample_peer_statistics):
        """Test GET /anomalies/user/{user_id}"""
        user, bills = sample_user_with_bills

        # Create anomaly first
        client.post(f"{API_VERSION}/bills/{bills[0].id}/calculate-metrics")
        client.post(f"{API_VERSION}/bills/{bills[1].id}/calculate-metrics")
        client.post(f"{API_VERSION}/anomalies/detect/{bills[1].id}")

        response = client.get(f"{API_VERSION}/anomalies/user/{user.user_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_dismiss_anomaly(self, client, sample_user_with_bills, sample_weather_cache, sample_peer_statistics):
        """Test POST /anomalies/{anomaly_id}/dismiss"""
        user, bills = sample_user_with_bills

        # Create anomaly
        client.post(f"{API_VERSION}/bills/{bills[0].id}/calculate-metrics")
        client.post(f"{API_VERSION}/bills/{bills[1].id}/calculate-metrics")
        detect_response = client.post(
            f"{API_VERSION}/anomalies/detect/{bills[1].id}")
        anomaly_id = detect_response.json()["anomaly_id"]

        response = client.post(
            f"{API_VERSION}/anomalies/{anomaly_id}/dismiss",
            json={"feedback": "helpful"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["feedback"] == "helpful"

    def test_get_anomaly_statistics(self, client, sample_user_with_bills, sample_weather_cache, sample_peer_statistics):
        """Test GET /anomalies/stats/overview"""
        user, bills = sample_user_with_bills

        # Create anomaly
        client.post(f"{API_VERSION}/bills/{bills[0].id}/calculate-metrics")
        client.post(f"{API_VERSION}/bills/{bills[1].id}/calculate-metrics")
        client.post(f"{API_VERSION}/anomalies/detect/{bills[1].id}")

        response = client.get(f"{API_VERSION}/anomalies/stats/overview",
                              params={"year": 2024})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_anomalies" in data
        assert "by_severity" in data
        assert "by_type" in data


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root(self, client):
        """Test GET /"""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "online"

    def test_health_check(self, client):
        """Test GET /health"""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
