import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Seattle Lat/Lon
LAT = 47.6062
LON = -122.3321

class WeatherService:
    def __init__(self):
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"

    def get_yearly_temperature_trend(self, year: int):
        """
        Fetches daily mean temperature for the given year (or YTD).
        Returns a list of daily temps or a simplified cooling degree metric.
        """
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        # If current year and in future, cap at today? Open-Meteo Archive is for past.
        # Use Forecast API for recent/future? For this prototype, we stick to Archive for 2023/2024 history.

        params = {
            "latitude": LAT,
            "longitude": LON,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_mean",
            "timezone": "America/Los_Angeles"
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("daily", {}).get("temperature_2m_mean", [])
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            return []

    def calculate_weather_factor(self, year: int, doy: int):
        """
        Returns a float representing phenological acceleration based on temperature history up to DOY.
        """
        # Simplification: Fetch full year once or mock it for speed in this sandbox
        # Real impl would cache this.

        # Mock logic: If 2024 was hotter than average, delayed fall? Or drought stress = earlier?
        # Let's assume standard behavior for now (return 1.0) or random daily fluctuation.
        return 1.0

weather_service = WeatherService()
