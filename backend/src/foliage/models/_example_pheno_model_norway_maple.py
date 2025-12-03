import openmeteo_requests
import requests_cache
import pandas as pd
import requests
from retry_requests import retry
import datetime
import time

# New dependency for astronomical calculations
try:
    from astral.sun import sun
    from astral import LocationInfo
except ImportError:
    print("Error: 'astral' library not found. Please run: pip install astral")
    exit(1)

class WeatherFetcher:
    """
    Handles fetching and processing historical weather data from Open-Meteo.
    """
    def __init__(self):
        # Setup the Open-Meteo client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)
        self.url = "https://archive-api.open-meteo.com/v1/archive"

    def get_weather_history(self, lat: float, lon: float, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetches daily historical weather data, including soil moisture.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "sunshine_duration",
                "precipitation_sum"
            ],
            "hourly": ["soil_moisture_7_to_28cm"], # Root zone moisture
            "timezone": "auto"
        }

        try:
            responses = self.openmeteo.weather_api(self.url, params=params)
            response = responses[0]

            # Process Daily Data
            daily = response.Daily()
            daily_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                    end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=daily.Interval()),
                    inclusive="left"
                ).dt.date,
                "max_temp": daily.Variables(0).ValuesAsNumpy(),
                "min_temp": daily.Variables(1).ValuesAsNumpy(),
                "sunshine": daily.Variables(2).ValuesAsNumpy(), # seconds
                "precip": daily.Variables(3).ValuesAsNumpy()
            }

            df_daily = pd.DataFrame(data=daily_data)

            # Process Hourly Data (Soil Moisture) and aggregate to Daily Mean
            hourly = response.Hourly()
            hourly_data = {
                "time": pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left"
                ),
                "soil_moisture": hourly.Variables(0).ValuesAsNumpy()
            }
            df_hourly = pd.DataFrame(data=hourly_data)
            df_hourly['date'] = df_hourly['time'].dt.date

            # Aggregate hourly soil moisture to daily average
            daily_soil = df_hourly.groupby('date')['soil_moisture'].mean().reset_index()

            # Merge
            df_final = pd.merge(df_daily, daily_soil, on='date', how='left')
            return df_final

        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return pd.DataFrame()

class LandUseFetcher:
    """
    Determines if a location is Urban or Rural using OpenStreetMap (Overpass API).
    Used to infer Nitrogen levels and Urban Heat Island effects.
    """
    def __init__(self):
        self.overpass_url = "http://overpass-api.de/api/interpreter"
        self.session = requests_cache.CachedSession('.osm_cache', expire_after=86400) # Cache for 24h

    def is_urban_environment(self, lat: float, lon: float) -> bool:
        """
        Checks for residential, commercial, or industrial land use within 200m.
        """
        # Overpass QL query: Search for specific landuse tags around the point
        query = f"""
                [out:json];
                (
                way(around:200,{lat},{lon})["landuse"~"residential|commercial|industrial|retail"];
                relation(around:200,{lat},{lon})["landuse"~"residential|commercial|industrial|retail"];
                );
                out body;
                """
        try:
            response = self.session.get(self.overpass_url, params={'data': query}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return len(data.get('elements', [])) > 0
            return False
        except Exception as e:
            print(f"OSM Fetch Error (Defaulting to False): {e}")
            return False

class ElevationFetcher:
    """
    Fetches elevation data from Open-Elevation API.
    Higher elevation = Higher UV exposure = Enhanced Anthocyanin (Red) production.
    """
    def __init__(self):
        self.url = "https://api.open-elevation.com/api/v1/lookup"
        self.session = requests_cache.CachedSession('.elevation_cache', expire_after=604800) # Cache for 1 week

    def get_elevation(self, lat: float, lon: float) -> float:
        """
        Returns elevation in meters. Returns 0.0 on failure.
        """
        params = {"locations": f"{lat},{lon}"}
        try:
            response = self.session.get(self.url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # API format: {'results': [{'latitude': x, 'longitude': y, 'elevation': z}]}
                if 'results' in data and len(data['results']) > 0:
                    return float(data['results'][0]['elevation'])
            return 0.0
        except Exception as e:
            print(f"Elevation Fetch Error (Defaulting to 0m): {e}")
            return 0.0

class NorwayMaplePhenology:
    """
    Predicts leaf color based on weather, land use, elevation, and photoperiodism.
    """
    def __init__(self, weather_df: pd.DataFrame, lat: float, lon: float, is_urban: bool = False, elevation: float = 0.0):
        self.weather_df = weather_df
        self.lat = lat
        self.lon = lon
        self.is_urban = is_urban
        self.elevation = elevation

        # Initialize Astral location info
        self.location = LocationInfo(latitude=lat, longitude=lon)

        # Ensure data is sorted
        if not self.weather_df.empty:
            self.weather_df = self.weather_df.sort_values(by="date")

    def get_day_length_hours(self, date_obj: datetime.date) -> float:
        """
        Calculates the length of daylight in hours using Astral.
        """
        try:
            s = sun(self.location.observer, date=date_obj)
            # Calculate duration between sunrise and sunset
            duration = s['sunset'] - s['sunrise']
            return duration.total_seconds() / 3600.0
        except Exception:
            return 12.0

    def interpolate_color(self, color1, color2, factor):
        """Linear interpolation between two RGB tuples."""
        factor = max(0.0, min(1.0, factor))
        return tuple(int(c1 + (c2 - c1) * factor) for c1, c2 in zip(color1, color2))

    def get_color(self, target_date: datetime.date, cultivar: str = 'standard') -> tuple[int, int, int]:
        """
        Determines color by analyzing weather history and photoperiod up to the target date.
        """
        if self.weather_df.empty:
            return (128, 128, 128) # Error Gray

        # Filter data up to target date (90 day context to catch summer drought)
        history = self.weather_df[self.weather_df['date'] <= target_date].tail(90)

        if history.empty:
            return (54, 124, 43) # Default Green

        # --- 1. Killing Frost & Lethality ---
        hard_freezes = history[history['min_temp'] < -3.0]
        if not hard_freezes.empty:
            days_since_freeze = (target_date - hard_freezes.iloc[-1]['date']).days
            if days_since_freeze < 14:
                return (101, 67, 33) # Dead Brown

        # --- 2. Soil Moisture Stress ---
        recent_14_days = history.tail(14)
        avg_soil_moisture = recent_14_days['soil_moisture'].mean()
        is_drought_stressed = avg_soil_moisture < 0.15
        if avg_soil_moisture < 0.08:
            return (160, 110, 60) # Scorched Brown

        # --- 3. Photoperiodic Trigger (The "Clock") ---
        # Find first date where day length < 12.0 hours
        senescence_start_date = None
        for d in history['date']:
            dl = self.get_day_length_hours(d)
            if dl < 12.0:
                senescence_start_date = d
                break

        if senescence_start_date is None or target_date < senescence_start_date:
             if cultivar == 'crimson_king':
                 return (70, 0, 30) # Deep Purple
             return (54, 124, 43) # Deep Green

        # --- 4. Accumulated Chill (Rate of Change) ---
        relevant_period = history[history['date'] >= senescence_start_date]
        cold_units = 0
        chill_threshold = 15.0

        for _, row in relevant_period.iterrows():
            if row['max_temp'] < chill_threshold:
                cold_units += (chill_threshold - row['max_temp'])

        # Apply Urban Penalty (Delay)
        if self.is_urban:
            cold_units *= 0.80

        # --- 5. Elevation/UV Logic (The "Sunscreen" Effect) ---
        # Higher elevation = clearer air = more UV = more anthocyanin (red).
        # We calculate a stress factor from 0.0 (sea level) to 1.0 (1000m+)
        uv_stress_factor = min(1.0, self.elevation / 1000.0)

        # --- Color Logic ---
        avg_sunshine_hours = (recent_14_days['sunshine'].mean()) / 3600
        is_sunny_fall = avg_sunshine_hours > 5.0

        if cultivar == 'crimson_king':
            if cold_units > 200:
                return (80, 50, 40) # Bronze
            return (80, 0, 30) # Purple

        # Standard Cultivar Targets
        green = (54, 124, 43)
        early_yellow = (180, 190, 40)

        # Base Peak: Vibrant Gold
        base_peak = (255, 215, 0)
        # High UV Peak: Shift towards Orange-Red (Anthocyanin mix)
        uv_peak = (230, 90, 30)

        # Blend Base Peak and UV Peak based on elevation
        peak_color = self.interpolate_color(base_peak, uv_peak, uv_stress_factor)

        muted_yellow = (200, 160, 40)
        brown = (120, 90, 50)

        target_peak = muted_yellow if (is_drought_stressed or not is_sunny_fall) else peak_color

        if cold_units < 50:
            return green
        elif 50 <= cold_units < 150:
            factor = (cold_units - 50) / 100
            return self.interpolate_color(green, early_yellow, factor)
        elif 150 <= cold_units < 300:
            factor = (cold_units - 150) / 150
            return self.interpolate_color(early_yellow, target_peak, factor)
        elif 300 <= cold_units < 450:
            factor = (cold_units - 300) / 150
            return self.interpolate_color(target_peak, brown, factor)
        else:
            return (101, 67, 33)

# --- Example Usage ---
if __name__ == "__main__":
    # Coordinates (Boulder, CO - High Elevation, Urban)
    lat, lon = 40.0150, -105.2705

    print(f"Analyzing location: {lat}, {lon}")

    # 1. Check Land Use
    land_fetcher = LandUseFetcher()
    is_urban = land_fetcher.is_urban_environment(lat, lon)
    print(f"Land Use: {'URBAN (High N, UHI)' if is_urban else 'RURAL/NATURAL'}")

    # 2. Check Elevation
    elev_fetcher = ElevationFetcher()
    elevation = elev_fetcher.get_elevation(lat, lon)
    print(f"Elevation: {elevation} meters (UV Stress Factor: {min(1.0, elevation/1000.0):.2f})")

    # 3. Fetch Weather
    weather_fetcher = WeatherFetcher()
    print("Fetching weather history...")
    df = weather_fetcher.get_weather_history(lat, lon, "2023-06-01", "2023-11-30")

    if not df.empty:
        # Initialize model
        model = NorwayMaplePhenology(df, lat, lon, is_urban=is_urban, elevation=elevation)

        check_dates = [
            datetime.date(2023, 9, 10),
            datetime.date(2023, 10, 15),
            datetime.date(2023, 10, 25),
            datetime.date(2023, 11, 20)
        ]

        print("\n--- Phenology Forecast ---")
        for d in check_dates:
            day_len = model.get_day_length_hours(d)
            color = model.get_color(d)
            print(f"Date: {d} | Day Length: {day_len:.2f}h | Color: {color}")
