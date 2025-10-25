"""
Complete anomaly detection system with 3 detectors
"""

from sqlalchemy.orm import Session
from entities import UserBill, UserProfile, BillMetrics, AnomalyDetection
from weather import WeatherService
from PeerStatistics import PeerService
from typing import Optional, Dict
from datetime import datetime


class AnomalyDetectionService:
    """Main service for detecting consumption anomalies"""

    def __init__(self, db: Session):
        self.db = db
        self.weather_service = WeatherService(db)
        self.peer_service = PeerService(db)

    # ============= DETECTOR 1: HISTORICAL =============

    def detect_historical_anomaly(
        self,
        bill_id: int
    ) -> Optional[Dict]:
        """
        Detect anomalies by comparing to user's previous year(s).

        Returns:
            Dictionary with detection results or None
        """

        # Get current bill and its metrics
        bill = self.db.query(UserBill).filter(UserBill.id == bill_id).first()
        if not bill:
            return None

        metrics = self.db.query(BillMetrics).filter(
            BillMetrics.bill_id == bill_id
        ).first()

        if not metrics or metrics.yoy_consumption_change_percent is None:
            return {
                "has_anomaly": False,
                "score": 0,
                "reason": "no_historical_data",
                "message": "No previous year data available for comparison"
            }

        # Calculate score based on YoY change
        yoy_change = metrics.yoy_consumption_change_percent
        score = self._calculate_historical_score(yoy_change)

        # Determine anomaly type
        anomaly_type = self._classify_historical_anomaly(yoy_change)

        # Generate explanation
        explanation = self._generate_historical_explanation(
            bill.consumption_kwh,
            metrics.previous_year_consumption_kwh,
            yoy_change
        )

        return {
            "has_anomaly": score >= 5,
            "score": score,
            "anomaly_type": anomaly_type,
            "yoy_change_percent": yoy_change,
            "current_consumption": bill.consumption_kwh,
            "previous_consumption": metrics.previous_year_consumption_kwh,
            "explanation": explanation
        }

    def _calculate_historical_score(self, yoy_change_percent: float) -> float:
        """
        Calculate historical anomaly score (0-10).

        Thresholds:
        - 0-10%: Normal (0-2)
        - 10-20%: Slight concern (3-5)
        - 20-30%: Moderate (6-7)
        - 30-40%: High (8-9)
        - 40%+: Critical (10)
        """

        abs_change = abs(yoy_change_percent)

        if abs_change < 10:
            score = abs_change / 10 * 2  # 0-2
        elif abs_change < 20:
            score = 3 + (abs_change - 10) / 10 * 2  # 3-5
        elif abs_change < 30:
            score = 6 + (abs_change - 20) / 10 * 1  # 6-7
        elif abs_change < 40:
            score = 8 + (abs_change - 30) / 10 * 1  # 8-9
        else:
            score = 10

        return round(score, 2)

    def _classify_historical_anomaly(self, yoy_change_percent: float) -> str:
        """Classify the type of historical anomaly"""

        if abs(yoy_change_percent) < 15:
            return "normal"
        elif yoy_change_percent > 30:
            return "consumption_spike"
        elif yoy_change_percent < -30:
            return "consumption_drop"
        elif yoy_change_percent > 15:
            return "moderate_increase"
        else:
            return "moderate_decrease"

    def _generate_historical_explanation(
        self,
        current: float,
        previous: float,
        yoy_change: float
    ) -> str:
        """Generate human-readable explanation"""

        if yoy_change > 0:
            return (f"Your consumption increased from {previous:,.0f} kWh to "
                    f"{current:,.0f} kWh, a {yoy_change:.1f}% increase compared to last year.")
        else:
            return (f"Your consumption decreased from {previous:,.0f} kWh to "
                    f"{current:,.0f} kWh, a {abs(yoy_change):.1f}% decrease compared to last year.")

    # ============= DETECTOR 2: PEER COMPARISON =============

    def detect_peer_anomaly(
        self,
        bill_id: int
    ) -> Optional[Dict]:
        """
        Detect anomalies by comparing to peer group.

        Returns:
            Dictionary with detection results or None
        """

        # Get bill
        bill = self.db.query(UserBill).filter(UserBill.id == bill_id).first()
        if not bill:
            return None

        # Compare to peers
        comparison = self.peer_service.compare_to_peers(
            bill.user_id, bill.bill_year)

        if not comparison:
            return {
                "has_anomaly": False,
                "score": 0,
                "reason": "no_peer_data",
                "message": "No peer data available for comparison"
            }

        # Calculate score
        score = self.peer_service.calculate_peer_score(
            comparison['user_consumption_kwh'],
            comparison['peer_avg_kwh'],
            comparison['peer_std_dev_kwh']
        )

        # Determine anomaly type
        z_score = comparison['z_score']
        if z_score > 2:
            anomaly_type = "peer_outlier_high"
        elif z_score < -2:
            anomaly_type = "peer_outlier_low"
        elif z_score > 1:
            anomaly_type = "above_peer_average"
        else:
            anomaly_type = "normal"

        # Generate explanation
        explanation = self._generate_peer_explanation(comparison)

        return {
            "has_anomaly": score >= 5,
            "score": score,
            "anomaly_type": anomaly_type,
            "z_score": z_score,
            "user_consumption": comparison['user_consumption_kwh'],
            "peer_average": comparison['peer_avg_kwh'],
            "percent_difference": comparison['percent_difference'],
            "percentile": comparison['percentile'],
            "peer_group_size": comparison['peer_group']['sample_size'],
            "explanation": explanation
        }

    def _generate_peer_explanation(self, comparison: Dict) -> str:
        """Generate peer comparison explanation"""

        diff = comparison['percent_difference']
        peer_avg = comparison['peer_avg_kwh']
        user_cons = comparison['user_consumption_kwh']

        if diff > 0:
            return (f"Your consumption of {user_cons:,.0f} kWh is {diff:.1f}% higher "
                    f"than the average {peer_avg:,.0f} kWh for similar households.")
        else:
            return (f"Your consumption of {user_cons:,.0f} kWh is {abs(diff):.1f}% lower "
                    f"than the average {peer_avg:,.0f} kWh for similar households.")

    # ============= DETECTOR 3: PREDICTIVE (WEATHER-ADJUSTED) =============

    def detect_predictive_anomaly(
        self,
        bill_id: int
    ) -> Optional[Dict]:
        """
        Detect anomalies using weather-adjusted predictions.
        Calculates what consumption SHOULD be based on weather.

        Returns:
            Dictionary with detection results or None
        """

        # Get current bill
        bill = self.db.query(UserBill).filter(UserBill.id == bill_id).first()
        if not bill:
            return None

        # Get user profile
        user = self.db.query(UserProfile).filter(
            UserProfile.user_id == bill.user_id
        ).first()

        # Get previous year's bill
        previous_bill = self.db.query(UserBill).filter(
            UserBill.user_id == bill.user_id,
            UserBill.bill_year == bill.bill_year - 1
        ).first()

        if not previous_bill:
            return {
                "has_anomaly": False,
                "score": 0,
                "reason": "no_baseline_data",
                "message": "No previous year data for weather adjustment"
            }

        # Calculate expected consumption with weather adjustment
        expected = self.weather_service.get_expected_consumption_with_weather(
            previous_bill.consumption_kwh,
            user.postal_code,
            previous_bill.bill_year,
            bill.bill_year
        )

        if expected is None:
            return {
                "has_anomaly": False,
                "score": 0,
                "reason": "no_weather_data",
                "message": "Weather data not available"
            }

        # Calculate deviation
        actual = bill.consumption_kwh
        deviation_kwh = actual - expected
        deviation_percent = (deviation_kwh / expected) * 100

        # Calculate score
        score = self._calculate_predictive_score(deviation_percent)

        # Determine anomaly type
        if abs(deviation_percent) < 15:
            anomaly_type = "normal"
        elif deviation_percent > 25:
            anomaly_type = "unexplained_spike"
        elif deviation_percent < -25:
            anomaly_type = "unexplained_drop"
        else:
            anomaly_type = "moderate_deviation"

        # Generate explanation
        explanation = self._generate_predictive_explanation(
            actual, expected, deviation_percent, bill.bill_year, bill.bill_year - 1
        )

        return {
            "has_anomaly": score >= 5,
            "score": score,
            "anomaly_type": anomaly_type,
            "actual_consumption": actual,
            "expected_consumption": expected,
            "deviation_kwh": round(deviation_kwh, 2),
            "deviation_percent": round(deviation_percent, 2),
            "explanation": explanation
        }

    def _calculate_predictive_score(self, deviation_percent: float) -> float:
        """
        Calculate predictive anomaly score (0-10).

        Thresholds:
        - 0-15%: Normal (0-3)
        - 15-25%: Moderate (4-6)
        - 25-40%: High (7-9)
        - 40%+: Critical (10)
        """

        abs_dev = abs(deviation_percent)

        if abs_dev < 15:
            score = abs_dev / 15 * 3  # 0-3
        elif abs_dev < 25:
            score = 4 + (abs_dev - 15) / 10 * 2  # 4-6
        elif abs_dev < 40:
            score = 7 + (abs_dev - 25) / 15 * 2  # 7-9
        else:
            score = 10

        return round(score, 2)

    def _generate_predictive_explanation(
        self,
        actual: float,
        expected: float,
        deviation: float,
        current_year: int,
        baseline_year: int
    ) -> str:
        """Generate predictive explanation"""

        if deviation > 0:
            return (f"After adjusting for weather differences, your consumption of "
                    f"{actual:,.0f} kWh is {deviation:.1f}% higher than the expected "
                    f"{expected:,.0f} kWh based on {baseline_year} patterns.")
        else:
            return (f"After adjusting for weather differences, your consumption of "
                    f"{actual:,.0f} kWh is {abs(deviation):.1f}% lower than the expected "
                    f"{expected:,.0f} kWh based on {baseline_year} patterns.")

    # ============= COMBINED ANOMALY ENGINE =============

    def detect_all_anomalies(
        self,
        bill_id: int
    ) -> Optional[Dict]:
        """
        Run all three detectors and combine results.

        Returns:
            Complete anomaly detection result
        """

        # Get bill
        bill = self.db.query(UserBill).filter(UserBill.id == bill_id).first()
        if not bill:
            return None

        # Run all detectors
        historical = self.detect_historical_anomaly(bill_id)
        peer = self.detect_peer_anomaly(bill_id)
        predictive = self.detect_predictive_anomaly(bill_id)

        # Extract scores
        hist_score = historical['score'] if historical else 0
        peer_score = peer['score'] if peer else 0
        pred_score = predictive['score'] if predictive else 0

        # Calculate weighted combined score
        # Weights: Historical 40%, Peer 30%, Predictive 30%
        combined_score = (hist_score * 0.4) + \
            (peer_score * 0.3) + (pred_score * 0.3)
        combined_score = round(combined_score, 2)

        # Determine overall severity
        if combined_score < 4:
            severity = "normal"
        elif combined_score < 7:
            severity = "warning"
        else:
            severity = "critical"

        # Determine primary anomaly type (highest score)
        primary_type = self._determine_primary_anomaly_type(
            historical, peer, predictive
        )

        # Generate combined explanation
        explanation = self._generate_combined_explanation(
            historical, peer, predictive, primary_type
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            primary_type, historical, peer, predictive
        )

        # Calculate estimated financial impact
        financial_impact = self._calculate_financial_impact(
            bill, historical, predictive)

        return {
            "bill_id": bill_id,
            "user_id": bill.user_id,
            "bill_year": bill.bill_year,
            "has_anomaly": combined_score >= 4,
            "severity": severity,
            "combined_score": combined_score,
            "primary_anomaly_type": primary_type,
            "detector_scores": {
                "historical": hist_score,
                "peer": peer_score,
                "predictive": pred_score
            },
            "detector_results": {
                "historical": historical,
                "peer": peer,
                "predictive": predictive
            },
            "explanation": explanation,
            "recommendations": recommendations,
            "estimated_extra_cost_euros": financial_impact
        }

    def _determine_primary_anomaly_type(
        self,
        historical: Dict,
        peer: Dict,
        predictive: Dict
    ) -> str:
        """Determine which detector found the strongest anomaly"""

        scores = [
            (historical['score'] if historical else 0,
             historical['anomaly_type'] if historical["has_anomaly"] == True else 'normal'),
            (peer['score'] if peer else 0,
             peer.get(
                 'anomaly_type', 'normal') if historical else 'normal'),
            (predictive['score'] if predictive else 0,
             # predictive['anomaly_type'] if predictive['anomaly_type'] is not None else 'normal',
             predictive.get(
                 'anomaly_type', 'normal') if historical else 'normal'

             )
        ]

        # Get highest scoring anomaly type
        max_score, anomaly_type = max(scores, key=lambda x: x[0])

        return anomaly_type if max_score >= 4 else "normal"

    def _generate_combined_explanation(
        self,
        historical: Dict,
        peer: Dict,
        predictive: Dict,
        primary_type: str
    ) -> str:
        """Generate comprehensive explanation combining all detectors"""

        parts = []

        # Start with primary finding
        if historical and historical['has_anomaly']:
            parts.append(historical['explanation'])

        if peer and peer['has_anomaly']:
            parts.append(peer['explanation'])

        if predictive and predictive['has_anomaly']:
            parts.append(predictive['explanation'])

        if not parts:
            return "Your energy consumption is within normal range across all metrics."

        return " ".join(parts)

    def _generate_recommendations(
        self,
        primary_type: str,
        historical: Dict,
        peer: Dict,
        predictive: Dict
    ) -> str:
        """Generate actionable recommendations"""

        recommendations = []

        if primary_type == "consumption_spike":
            recommendations.append(
                "• Check for new appliances or changed usage patterns")
            recommendations.append(
                "• Review heating/cooling system efficiency")
            recommendations.append("• Consider an energy audit")

        if primary_type == "peer_outlier_high":
            recommendations.append(
                "• Your consumption is higher than similar households")
            recommendations.append("• Check insulation and window seals")
            recommendations.append("• Review thermostat settings")
            recommendations.append("• Consider energy-efficient appliances")

        if primary_type == "unexplained_spike":
            recommendations.append(
                "• Consumption increase cannot be explained by weather")
            recommendations.append("• Check for equipment malfunctions")
            recommendations.append("• Review usage habits")

        if not recommendations:
            recommendations.append("• Continue current energy practices")
            recommendations.append("• Monitor for any changes")

        return "\n".join(recommendations)

    def _calculate_financial_impact(
        self,
        bill: UserBill,
        historical: Dict,
        predictive: Dict
    ) -> Optional[float]:
        """Calculate estimated extra cost due to anomaly"""

        if not bill.tariff_rate:
            return None

        extra_kwh = 0

        # Use predictive deviation if available (most accurate)
        if predictive and predictive.get('deviation_kwh'):
            extra_kwh = max(0, predictive['deviation_kwh'])
        # Fallback to historical
        elif historical and historical.get('current_consumption') and historical.get('previous_consumption'):
            extra_kwh = max(
                0, historical['current_consumption'] - historical['previous_consumption'])

        if extra_kwh > 0:
            return round(extra_kwh * bill.tariff_rate, 2)

        return None

    # ============= SAVE & RETRIEVE ANOMALIES =============

    def save_anomaly_detection(
        self,
        detection_result: Dict
    ) -> AnomalyDetection:
        """
        Save anomaly detection result to database.

        Args:
            detection_result: Result from detect_all_anomalies()

        Returns:
            Saved AnomalyDetection object
        """

        # Check if anomaly already exists for this bill
        existing = self.db.query(AnomalyDetection).filter(
            AnomalyDetection.bill_id == detection_result['bill_id']
        ).first()

        if existing:
            # Update existing
            anomaly = existing
        else:
            # Create new
            anomaly = AnomalyDetection(
                user_id=detection_result['user_id'],
                bill_id=detection_result['bill_id']
            )
            self.db.add(anomaly)

        # Update fields
        anomaly.anomaly_type = detection_result['primary_anomaly_type']
        anomaly.severity_level = detection_result['severity']
        anomaly.severity_score = detection_result['combined_score']

        anomaly.historical_score = detection_result['detector_scores']['historical']
        anomaly.peer_score = detection_result['detector_scores']['peer']
        anomaly.predictive_score = detection_result['detector_scores']['predictive']

        # Get current consumption from bill
        bill = self.db.query(UserBill).filter(
            UserBill.id == detection_result['bill_id']
        ).first()
        anomaly.current_consumption_kwh = bill.consumption_kwh

        # Get comparison value (peer average or previous year)
        if detection_result['detector_results']['peer']:
            anomaly.comparison_value = detection_result['detector_results']['peer'].get(
                'peer_average')
            anomaly.deviation_percent = detection_result['detector_results']['peer'].get(
                'percent_difference')
        elif detection_result['detector_results']['historical']:
            anomaly.comparison_value = detection_result['detector_results']['historical'].get(
                'previous_consumption')
            anomaly.deviation_percent = detection_result['detector_results']['historical'].get(
                'yoy_change_percent')

        anomaly.explanation_text = detection_result['explanation']
        anomaly.recommendations_text = detection_result['recommendations']
        anomaly.estimated_extra_cost_euros = detection_result['estimated_extra_cost_euros']
        anomaly.detection_date = datetime.utcnow()

        self.db.commit()
        self.db.refresh(anomaly)

        return anomaly

    def get_user_anomalies(
        self,
        user_id: int,
        only_active: bool = True
    ) -> list:
        """
        Get all anomalies for a user.

        Args:
            user_id: User ID
            only_active: Only return non-dismissed anomalies

        Returns:
            List of AnomalyDetection objects
        """

        query = self.db.query(AnomalyDetection).filter(
            AnomalyDetection.user_id == user_id
        )

        if only_active:
            query = query.filter(AnomalyDetection.is_dismissed == False)

        return query.order_by(AnomalyDetection.detection_date.desc()).all()

    def dismiss_anomaly(
        self,
        anomaly_id: int,
        feedback: Optional[str] = None
    ) -> Optional[AnomalyDetection]:
        """
        Mark an anomaly as dismissed by the user.

        Args:
            anomaly_id: Anomaly ID
            feedback: Optional user feedback

        Returns:
            Updated AnomalyDetection or None
        """

        anomaly = self.db.query(AnomalyDetection).filter(
            AnomalyDetection.id == anomaly_id
        ).first()

        if not anomaly:
            return None

        anomaly.is_dismissed = True
        anomaly.dismissed_at = datetime.utcnow()
        anomaly.user_feedback = feedback

        self.db.commit()
        self.db.refresh(anomaly)

        return anomaly
