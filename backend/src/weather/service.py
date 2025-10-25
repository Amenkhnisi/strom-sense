"""
services/weather_service.py (Production Version)
Real weather API integration using Open-Meteo
"""

from sqlalchemy.orm import Session
from entities import WeatherCache
from datetime import datetime
from typing import Optional,  Tuple
from database import get_db
from fastapi import Depends
import requests
from requests.exceptions import RequestException


class WeatherService:
    """Service for fetching and caching real weather data"""

    # Base temperature for HDD calculation (standard is 18°C)
    BASE_TEMPERATURE = 18.0

    # Open-Meteo API endpoint (free, no API key needed)
    API_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_heating_degree_days(
        self,
        postal_code: str,
        year: int,
        force_refresh: bool = False
    ) -> Optional[float]:
        """
        Get heating degree days for a postal code and year.
        Uses cache if available, otherwise fetches from API.

        Args:
            postal_code: German postal code (e.g., "10115")
            year: Year (e.g., 2024)
            force_refresh: Force API call even if cached

        Returns:
            Heating degree days (float) or None if unavailable
        """

        # Check cache first
        if not force_refresh:
            cached = self._get_from_cache(postal_code, year)
            if cached:
                print(
                    f"✅ Using cached HDD for {postal_code}/{year}: {cached.heating_degree_days}")
                return cached.heating_degree_days

        # Fetch from API
        print(f"🌡️  Fetching real HDD data for {postal_code}/{year}...")

        try:
            hdd, avg_temp = self._fetch_from_api(postal_code, year)

            if hdd is not None:
                # Save to cache
                self._save_to_cache(postal_code, year, hdd, avg_temp)
                print(
                    f"✅ Fetched and cached HDD: {hdd} (Avg temp: {avg_temp:.1f}°C)")
                return {"hdd": hdd, "avg_temp": avg_temp}
            else:
                print(f"⚠️  Could not fetch HDD for {postal_code}/{year}")
                return None

        except Exception as e:
            print(f"❌ Error fetching weather data: {e}")
            return None

    def _get_from_cache(self, postal_code: str, year: int) -> Optional[WeatherCache]:
        """Get weather data from cache"""
        return self.db.query(WeatherCache).filter(
            WeatherCache.postal_code == str(postal_code),
            WeatherCache.year == year
        ).first()

    def _save_to_cache(
        self,
        postal_code: str,
        year: int,
        hdd: float,
        avg_temp: float = None
    ):
        """Save weather data to cache"""

        # Check if already exists
        existing = self._get_from_cache(postal_code, year)

        if existing:
            # Update existing
            existing.heating_degree_days = hdd
            existing.average_temperature_celsius = avg_temp
            existing.fetched_at = datetime.utcnow()
        else:
            # Create new
            cache_entry = WeatherCache(
                postal_code=postal_code,
                year=year,
                heating_degree_days=hdd,
                average_temperature_celsius=avg_temp
            )
            self.db.add(cache_entry)

        self.db.commit()

    def _get_coordinates_from_postal_code(self, postal_code: str) -> Tuple[float, float]:
        """
        Get approximate coordinates for German postal code.

        In production, you might want to use a postal code geocoding service.
        For now, we use approximate coordinates for major German regions.
        """

        # Get first digit to determine region
        prefix = postal_code[0] if postal_code else "5"

        # Approximate coordinates for German regions (latitude, longitude)
        coordinates = {
            "0": (51.05, 13.74),   # Dresden (East Germany)
            "1": (52.52, 13.40),   # Berlin
            "2": (53.55, 9.99),    # Hamburg (North)
            "3": (52.37, 9.73),    # Hannover (Central North)
            "4": (51.23, 6.78),    # Düsseldorf (West)
            "5": (50.94, 6.96),    # Cologne (West)
            "6": (50.11, 8.68),    # Frankfurt (Central)
            "7": (48.78, 9.18),    # Stuttgart (South West)
            "8": (48.14, 11.58),   # Munich (South Bavaria)
            "9": (49.45, 11.08),   # Nuremberg (North Bavaria)
        }

        # Default: Center of Germany
        return coordinates.get(prefix, (51.16, 10.45))

    def _fetch_from_api(self, postal_code: str, year: int) -> Tuple[Optional[float], Optional[float]]:
        """
        Fetch real weather data from Open-Meteo API and calculate HDD.

        Returns:
            Tuple of (heating_degree_days, average_temperature) or (None, None)
        """

        # Get coordinates
        latitude, longitude = self._get_coordinates_from_postal_code(
            postal_code)

        # Define date range for the year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        # API parameters
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_mean",
            "timezone": "Europe/Berlin"
        }

        try:
            # Make API request
            response = requests.get(
                self.API_BASE_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Extract daily temperatures
            if "daily" not in data or "temperature_2m_mean" not in data["daily"]:
                print(f"⚠️  No temperature data in API response")
                return None, None

            temperatures = data["daily"]["temperature_2m_mean"]

            # Calculate HDD
            hdd = self._calculate_hdd_from_temperatures(temperatures)

            # Calculate average temperature
            avg_temp = sum(temperatures) / \
                len(temperatures) if temperatures else None

            return hdd, avg_temp

        except RequestException as e:
            print(f"❌ API request failed: {e}")
            return None, None
        except Exception as e:
            print(f"❌ Error processing weather data: {e}")
            return None, None

    def _calculate_hdd_from_temperatures(self, daily_temperatures: list) -> float:
        """
        Calculate Heating Degree Days from daily average temperatures.

        HDD formula: For each day where temp < 18°C, HDD += (18 - temp)

        Args:
            daily_temperatures: List of daily average temperatures

        Returns:
            Total heating degree days for the period
        """

        hdd = 0.0

        for temp in daily_temperatures:
            if temp is not None and temp < self.BASE_TEMPERATURE:
                hdd += (self.BASE_TEMPERATURE - temp)

        return round(hdd, 1)

    def calculate_weather_adjustment_factor(
        self,
        postal_code: str,
        current_year: int,
        previous_year: int
    ) -> Optional[float]:
        """
        Calculate weather adjustment factor between two years.

        Factor > 1.0 means current year was colder (more heating needed)
        Factor < 1.0 means current year was warmer (less heating needed)

        Args:
            postal_code: Postal code
            current_year: Current year
            previous_year: Previous year

        Returns:
            Adjustment factor (e.g., 1.08 = 8% colder)
        """

        current_hdd = self.get_heating_degree_days(postal_code, current_year)
        previous_hdd = self.get_heating_degree_days(postal_code, previous_year)

        if current_hdd is None or previous_hdd is None or previous_hdd == 0:
            return None

        factor = current_hdd / previous_hdd
        return round(factor, 3)

    def get_weather_normalized_consumption(
        self,
        actual_consumption: float,
        postal_code: str,
        actual_year: int,
        baseline_year: int
    ) -> Optional[float]:
        """
        Normalize consumption for weather differences.

        Returns what consumption WOULD have been if weather was same as baseline.

        Args:
            actual_consumption: Actual consumption in kWh
            postal_code: Postal code
            actual_year: Year of actual consumption
            baseline_year: Year to normalize to

        Returns:
            Weather-normalized consumption
        """

        factor = self.calculate_weather_adjustment_factor(
            postal_code,
            actual_year,
            baseline_year
        )

        if factor is None:
            return None

        # Normalize: if actual year was colder, reduce consumption to baseline
        normalized = actual_consumption / factor
        return round(normalized, 2)

    def get_expected_consumption_with_weather(
        self,
        baseline_consumption: float,
        postal_code: str,
        baseline_year: int,
        target_year: int
    ) -> Optional[float]:
        """
        Calculate expected consumption for target year based on baseline,
        adjusted for weather differences.

        This is useful for anomaly detection.

        Args:
            baseline_consumption: Known consumption from baseline year
            postal_code: Postal code
            baseline_year: Year of known consumption
            target_year: Year to predict for

        Returns:
            Expected consumption for target year
        """

        factor = self.calculate_weather_adjustment_factor(
            postal_code,
            target_year,
            baseline_year
        )

        if factor is None:
            return None

        # Adjust baseline by weather factor
        expected = baseline_consumption * factor
        return round(expected, 2)

    def clear_cache(self, postal_code: str = None, year: int = None) -> int:
        """
        Clear weather cache

        Args:
            postal_code: Clear only this postal code (optional)
            year: Clear only this year (optional)

        Returns:
            Number of entries cleared
        """

        query = self.db.query(WeatherCache)

        if postal_code:
            query = query.filter(WeatherCache.postal_code == str(postal_code))
        if year:
            query = query.filter(WeatherCache.year == year)

        count = query.delete()
        self.db.commit()

        print(f"🗑️  Cleared {count} weather cache entries")
        return count

    def prefetch_common_locations(self, years: list = None):
        """
        Pre-fetch weather data for common German cities.
        Useful for warming up the cache.

        Args:
            years: List of years to fetch (default: [2022, 2023, 2024])
        """

        if years is None:
            years = [2022, 2023, 2024]

        # Major German cities by postal code prefix
        common_postal_codes = [
            "10115",  # Berlin
            "20095",  # Hamburg
            "30159",  # Hannover
            "40210",  # Düsseldorf
            "50667",  # Cologne
            "60311",  # Frankfurt
            "70173",  # Stuttgart
            "80331",  # Munich
            "90402",  # Nuremberg
        ]

        print(
            f"\n🔄 Pre-fetching weather data for {len(common_postal_codes)} cities...")

        fetched = 0
        cached = 0

        for postal_code in common_postal_codes:
            for year in years:
                # Check if already cached
                if self._get_from_cache(postal_code, year):
                    cached += 1
                    continue

                # Fetch from API
                hdd = self.get_heating_degree_days(
                    postal_code, year, force_refresh=False)
                if hdd:
                    fetched += 1

        print(
            f"✅ Pre-fetch complete: {fetched} fetched, {cached} already cached")
        return {"fetched": fetched, "cached": cached}
