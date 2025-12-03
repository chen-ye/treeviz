import openmeteo_requests
import requests_cache
import pandas as pd
import numpy as np
import requests
from retry_requests import retry
import datetime
import time

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
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)
        self.url = "https://archive-api.open-meteo.com/v1/archive"

    def get_weather_history(self, lat: float, lon: float, start_date: str, end_date: str) -> pd.DataFrame:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": ["temperature_2m_max", "temperature_2m_min", "sunshine_duration", "precipitation_sum"],
            "hourly": ["soil_moisture_7_to_28cm"],
            "timezone": "auto"
        }

        try:
            responses = self.openmeteo.weather_api(self.url, params=params)
            response = responses[0]

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
                "sunshine": daily.Variables(2).ValuesAsNumpy(),
                "precip": daily.Variables(3).ValuesAsNumpy()
            }
            df_daily = pd.DataFrame(data=daily_data)

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

            daily_soil = df_hourly.groupby('date')['soil_moisture'].mean().reset_index()
            df_final = pd.merge(df_daily, daily_soil, on='date', how='left')
            return df_final.sort_values(by="date").reset_index(drop=True)

        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return pd.DataFrame()

class LandUseFetcher:
    """
    Determines if a location is Urban or Rural using OpenStreetMap (Overpass API).
    """
    def __init__(self):
        self.overpass_url = "http://overpass-api.de/api/interpreter"
        self.session = requests_cache.CachedSession('.osm_cache', expire_after=86400)

    def is_urban_environment(self, lat: float, lon: float) -> bool:
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
    """
    def __init__(self):
        self.url = "https://api.open-elevation.com/api/v1/lookup"
        self.session = requests_cache.CachedSession('.elevation_cache', expire_after=604800)

    def get_elevation(self, lat: float, lon: float) -> float:
        params = {"locations": f"{lat},{lon}"}
        try:
            response = self.session.get(self.url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    return float(data['results'][0]['elevation'])
            return 0.0
        except Exception as e:
            print(f"Elevation Fetch Error (Defaulting to 0m): {e}")
            return 0.0

class NorwayMaplePhenology:
    """
    Predicts leaf color efficiently for the entire dataset using vectorized operations.
    """
    def __init__(self, weather_df: pd.DataFrame, lat: float, lon: float, is_urban: bool = False, elevation: float = 0.0, cultivar: str = 'standard'):
        self.weather_df = weather_df.copy()
        self.lat = lat
        self.lon = lon
        self.is_urban = is_urban
        self.elevation = elevation
        self.cultivar = cultivar
        self.location = LocationInfo(latitude=lat, longitude=lon)

        # Pre-calculate the entire timeline on init
        if not self.weather_df.empty:
            self.timeline = self._calculate_timeline()
        else:
            self.timeline = pd.DataFrame()

    def _calculate_timeline(self) -> pd.DataFrame:
        """
        Generates the phenology state and color for every day in the dataset.
        """
        df = self.weather_df.copy()

        # 1. Vectorized Photoperiod Calculation
        # We define a helper and apply it. (Apply is slower than pure vector, but astral requires object context)
        def get_day_length(row):
            try:
                s = sun(self.location.observer, date=row['date'])
                return (s['sunset'] - s['sunrise']).total_seconds() / 3600.0
            except:
                return 12.0

        df['day_length'] = df.apply(get_day_length, axis=1)

        # 2. Identify Senescence Trigger (First day where length < 12h)
        # We create a boolean mask for the "Fall Season"
        trigger_mask = df['day_length'] < 12.0

        # Find the index of the first True value. If none, fall season never starts.
        if trigger_mask.any():
            trigger_idx = trigger_mask.idxmax()
            # 0: Summer (Before trigger), 1: Fall (After trigger)
            df['is_fall_season'] = df.index >= trigger_idx
        else:
            df['is_fall_season'] = False

        # 3. Vectorized Cold Accumulation
        chill_threshold = 15.0
        # Calculate raw chill units for every day: max(0, 15 - max_temp)
        df['daily_chill'] = (chill_threshold - df['max_temp']).clip(lower=0)

        # Zero out chill units that happened *before* the trigger (Summer cool days don't count)
        df.loc[~df['is_fall_season'], 'daily_chill'] = 0

        # Cumulative Sum
        df['accumulated_chill'] = df['daily_chill'].cumsum()

        # Urban Penalty
        if self.is_urban:
            df['accumulated_chill'] *= 0.80

        # 4. Stress Factors (Rolling Windows)
        # Recent Freeze: Has min_temp < -3.0 occurred in the last 14 days?
        df['is_freeze_day'] = df['min_temp'] < -3.0
        df['recent_freeze'] = df['is_freeze_day'].rolling(window=14, min_periods=1).max().fillna(0).astype(bool)

        # Drought Stress: 14-day rolling average of soil moisture
        df['rolling_moisture'] = df['soil_moisture'].rolling(window=14, min_periods=1).mean()
        df['is_drought'] = df['rolling_moisture'] < 0.15
        df['is_severe_drought'] = df['rolling_moisture'] < 0.08

        # Sunshine: 14-day rolling average
        df['rolling_sunshine_hours'] = df['sunshine'].rolling(window=14, min_periods=1).mean() / 3600.0
        df['is_sunny_fall'] = df['rolling_sunshine_hours'] > 5.0

        # 5. Calculate Color (Row-wise Mapping)
        # We use a vectorized apply for the color logic since it involves tuple construction
        # and conditional logic that is hard to purely vectorize without clutter.

        # Pre-calc UV factor
        uv_stress_factor = min(1.0, self.elevation / 1000.0)

        def map_row_color(row):
            # Immediate Lethality Checks
            if row['recent_freeze']:
                return (101, 67, 33) # Dead Brown
            if row['is_severe_drought']:
                return (160, 110, 60) # Scorched Brown

            # Cultivar Logic
            if self.cultivar == 'crimson_king':
                if not row['is_fall_season']:
                     return (70, 0, 30) # Summer Purple
                if row['accumulated_chill'] > 200:
                    return (80, 50, 40) # Bronze
                return (80, 0, 30) # Fall Purple

            # Standard Logic
            if not row['is_fall_season']:
                return (54, 124, 43) # Summer Green

            cold_units = row['accumulated_chill']

            # Target Colors
            green = (54, 124, 43)
            early_yellow = (180, 190, 40)
            muted_yellow = (200, 160, 40)
            brown = (120, 90, 50)

            # Determine Peak based on UV and Sunshine
            base_peak = (255, 215, 0) # Gold
            uv_peak = (230, 90, 30)   # Orange/Red

            # Interpolate peak based on UV
            peak_r = int(base_peak[0] + (uv_peak[0] - base_peak[0]) * uv_stress_factor)
            peak_g = int(base_peak[1] + (uv_peak[1] - base_peak[1]) * uv_stress_factor)
            peak_b = int(base_peak[2] + (uv_peak[2] - base_peak[2]) * uv_stress_factor)
            peak_color = (peak_r, peak_g, peak_b)

            target_peak = muted_yellow if (row['is_drought'] or not row['is_sunny_fall']) else peak_color

            # State Interpolation
            if cold_units < 50:
                return green
            elif 50 <= cold_units < 150:
                factor = (cold_units - 50) / 100
                return self._interp(green, early_yellow, factor)
            elif 150 <= cold_units < 300:
                factor = (cold_units - 150) / 150
                return self._interp(early_yellow, target_peak, factor)
            elif 300 <= cold_units < 450:
                factor = (cold_units - 300) / 150
                return self._interp(target_peak, brown, factor)
            else:
                return (101, 67, 33) # Late Brown

        df['color_rgb'] = df.apply(map_row_color, axis=1)
        return df

    def _interp(self, c1, c2, factor):
        factor = max(0.0, min(1.0, factor))
        return tuple(int(a + (b - a) * factor) for a, b in zip(c1, c2))

    def get_color(self, target_date: datetime.date) -> tuple[int, int, int]:
        """
        Look up the pre-calculated color for a specific date.
        """
        row = self.timeline.loc[self.timeline['date'] == target_date]
        if not row.empty:
            return row.iloc[0]['color_rgb']
        return (128, 128, 128) # Not in range

    def get_full_year_table(self):
        """Returns the full computed dataframe."""
        return self.timeline[['date', 'day_length', 'accumulated_chill', 'is_drought', 'color_rgb']]

# --- Example Usage ---
if __name__ == "__main__":
    lat, lon = 40.0150, -105.2705 # Boulder, CO

    print(f"Initializing Model for {lat}, {lon}")

    # 1. Fetch Context Data
    land_fetcher = LandUseFetcher()
    is_urban = land_fetcher.is_urban_environment(lat, lon)

    elev_fetcher = ElevationFetcher()
    elevation = elev_fetcher.get_elevation(lat, lon)

    # 2. Fetch Full Year Weather
    weather_fetcher = WeatherFetcher()
    print("Fetching full year weather data...")
    df = weather_fetcher.get_weather_history(lat, lon, "2023-01-01", "2023-12-31")

    if not df.empty:
        # 3. Vectorized Calculation triggers here
        model = NorwayMaplePhenology(df, lat, lon, is_urban, elevation, cultivar='standard')

        # 4. Access the table directly
        table = model.get_full_year_table()

        # Filter for interesting fall dates
        fall_view = table[ (table['date'] >= datetime.date(2023, 9, 1)) & (table['date'] <= datetime.date(2023, 11, 30)) ]

        print("\n--- Fall Color Table (Sample) ---")
        print(fall_view[['date', 'accumulated_chill', 'color_rgb']].iloc[::5]) # Print every 5th day
