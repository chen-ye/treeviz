import openmeteo_requests
import requests_cache
import pandas as pd
import numpy as np
import requests
from retry_requests import retry
import datetime
from abc import ABC, abstractmethod

try:
    from astral.sun import sun
    from astral import LocationInfo
except ImportError:
    print("Error: 'astral' library not found. Please run: pip install astral")
    exit(1)

# --- Data Fetching Layer (Shared) ---

class WeatherFetcher:
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
        except Exception:
            return False

class ElevationFetcher:
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
        except Exception:
            return 0.0

# --- Base Phenology Logic ---

class TreePhenologyModel(ABC):
    def __init__(self, weather_df: pd.DataFrame, lat: float, lon: float, is_urban: bool = False, elevation: float = 0.0):
        self.weather_df = weather_df.copy()
        self.lat = lat
        self.lon = lon
        self.is_urban = is_urban
        self.elevation = elevation
        self.location = LocationInfo(latitude=lat, longitude=lon)

        if not self.weather_df.empty:
            self.timeline = self._calculate_base_timeline()
        else:
            self.timeline = pd.DataFrame()

    def _interp(self, c1, c2, factor):
        factor = max(0.0, min(1.0, factor))
        return tuple(int(a + (b - a) * factor) for a, b in zip(c1, c2))

    def _calculate_base_timeline(self) -> pd.DataFrame:
        df = self.weather_df.copy()

        # 1. Photoperiod
        def get_day_length(row):
            try:
                s = sun(self.location.observer, date=row['date'])
                return (s['sunset'] - s['sunrise']).total_seconds() / 3600.0
            except:
                return 12.0
        df['day_length'] = df.apply(get_day_length, axis=1)

        # 2. Seasons (Trigger based)
        # Fall Trigger: Day length < 12h
        fall_mask = df['day_length'] < 12.0
        if fall_mask.any():
            fall_idx = fall_mask.idxmax()
            df['is_fall_season'] = df.index >= fall_idx
        else:
            df['is_fall_season'] = False

        # 3. Growing Degree Days (GDD) for Spring
        # Base temp 10C (common for trees)
        df['mean_temp'] = (df['max_temp'] + df['min_temp']) / 2
        df['daily_gdd'] = (df['mean_temp'] - 10.0).clip(lower=0)
        df['accumulated_gdd'] = df['daily_gdd'].cumsum()

        # 4. Chill Units for Fall
        # Threshold 15C
        df['daily_chill'] = (15.0 - df['max_temp']).clip(lower=0)
        df.loc[~df['is_fall_season'], 'daily_chill'] = 0
        df['accumulated_chill'] = df['daily_chill'].cumsum()

        if self.is_urban:
            df['accumulated_chill'] *= 0.80

        # 5. Stress Factors
        df['is_freeze_day'] = df['min_temp'] < -3.0
        df['recent_freeze'] = df['is_freeze_day'].rolling(window=14, min_periods=1).max().fillna(0).astype(bool)

        df['rolling_moisture'] = df['soil_moisture'].rolling(window=14, min_periods=1).mean()
        df['is_drought'] = df['rolling_moisture'] < 0.15
        df['is_severe_drought'] = df['rolling_moisture'] < 0.08

        df['uv_stress_factor'] = min(1.0, self.elevation / 1000.0)

        # 6. Apply Species Specific Color Logic
        df['color_rgb'] = df.apply(self._resolve_daily_color, axis=1)

        return df

    @abstractmethod
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        pass

    def get_full_year_table(self):
        return self.timeline

# --- Species Implementations ---

class CherryPlum(TreePhenologyModel):
    """
    Early spring flowering, dark purple foliage variant (Prunus cerasifera 'Nigra').
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Colors
        dormant = (100, 80, 80)      # Dark Brown/Grey
        bloom = (255, 192, 203)      # Pink
        foliage = (80, 20, 40)       # Deep Purple
        faded_fall = (100, 60, 40)   # Dull Bronze

        # Spring Logic (GDD)
        # Blooms early: ~150 GDD
        if row['accumulated_gdd'] < 100:
            return dormant
        elif 100 <= row['accumulated_gdd'] < 250:
            # Flowering Phase
            return bloom
        elif not row['is_fall_season']:
            # Summer Foliage
            return foliage

        # Fall Logic
        if row['recent_freeze']: return (60, 40, 30) # Dead

        chill = row['accumulated_chill']
        if chill < 100:
            return foliage
        else:
            # Fades to bronze then drops
            return self._interp(foliage, faded_fall, (chill - 100)/200)

class NorwayMaple(TreePhenologyModel):
    """
    Standard green to yellow/gold fall color.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        green = (54, 124, 43)
        yellow = (255, 215, 0)
        brown = (101, 67, 33)

        if row['accumulated_gdd'] < 200:
            return (110, 100, 90) # Dormant/Buds

        if not row['is_fall_season']:
            return green

        if row['recent_freeze']: return brown
        if row['is_severe_drought']: return (160, 110, 60)

        chill = row['accumulated_chill']

        # UV/Elevation can add orange tints
        peak_color = yellow
        if row['uv_stress_factor'] > 0.3:
            peak_color = self._interp(yellow, (255, 140, 0), row['uv_stress_factor'])

        if chill < 100: return green
        elif 100 <= chill < 300:
            return self._interp(green, peak_color, (chill-100)/200)
        elif 300 <= chill < 450:
            return self._interp(peak_color, brown, (chill-300)/150)
        else:
            return brown

class Sweetgum(TreePhenologyModel):
    """
    Liquidambar styraciflua. Late fall color, highly variable vibrant mix (Red/Purple/Yellow).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        summer_green = (34, 139, 34)
        vibrant_red = (220, 20, 60)
        deep_purple = (75, 0, 130)
        brown = (101, 67, 33)

        if row['accumulated_gdd'] < 250: return (100, 90, 80) # Late waker
        if not row['is_fall_season']: return summer_green
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']

        # Sweetgum needs MORE chill to start turning than maple
        if chill < 200:
            return summer_green
        elif 200 <= chill < 500:
            # Mix of red and purple based on UV/Sun
            target = vibrant_red if row['uv_stress_factor'] > 0.2 else deep_purple
            return self._interp(summer_green, target, (chill-200)/300)
        else:
            return brown

class NorthernRedOak(TreePhenologyModel):
    """
    Quercus rubra. Late russet color. Marcescent (holds brown leaves).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        green = (50, 100, 40)
        russet = (165, 42, 42) # Reddish Brown
        dry_brown = (139, 69, 19)

        if row['accumulated_gdd'] < 300: return (90, 80, 70) # Very late spring
        if not row['is_fall_season']: return green

        chill = row['accumulated_chill']

        # Oaks turn very late
        if chill < 300:
            return green
        elif 300 <= chill < 600:
            return self._interp(green, russet, (chill-300)/300)
        else:
            # Marcescence: They hold the brown leaves all winter
            # Unlike others which might go "bare" (handled by UI usually),
            # we explicitly return brown leaf color here.
            return dry_brown

class DouglasFir(TreePhenologyModel):
    """
    Pseudotsuga menziesii. Evergreen. Spring flush logic.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        old_growth = (1, 68, 33)    # Dark Green
        new_growth = (100, 200, 50) # Lime Green tips

        # Spring Flush Logic (GDD)
        # Flush happens mid-spring
        if 250 <= row['accumulated_gdd'] < 450:
            # The "Flush" period where tips are bright
            # We interpolate back to dark as they harden off
            progress = (row['accumulated_gdd'] - 250) / 200
            # 0.0 = Peak Lime -> 1.0 = Hardened Dark
            return self._interp(new_growth, old_growth, progress)

        return old_growth


# --- Factory & Usage ---

def get_tree_model(species: str, weather_df, lat, lon, urban=False, elev=0.0):
    species_map = {
        'cherry_plum': CherryPlum,
        'norway_maple': NorwayMaple,
        'sweetgum': Sweetgum,
        'red_oak': NorthernRedOak,
        'douglas_fir': DouglasFir
    }

    cls = species_map.get(species.lower().replace(" ", "_"))
    if cls:
        return cls(weather_df, lat, lon, urban, elev)
    else:
        raise ValueError(f"Unknown species: {species}")

if __name__ == "__main__":
    lat, lon = 40.0150, -105.2705 # Boulder, CO

    # 1. Fetch Environment
    land = LandUseFetcher()
    is_urban = land.is_urban_environment(lat, lon)
    elev = ElevationFetcher().get_elevation(lat, lon)

    # 2. Fetch Weather
    weather = WeatherFetcher()
    print("Fetching weather data...")
    df = weather.get_weather_history(lat, lon, "2023-01-01", "2023-12-31")

    if not df.empty:
        species_list = ['cherry_plum', 'norway_maple', 'sweetgum', 'red_oak', 'douglas_fir']

        print(f"\nAnalysis for Boulder, CO (Elev: {elev}m, Urban: {is_urban})")
        print("-" * 60)

        for sp in species_list:
            model = get_tree_model(sp, df, lat, lon, is_urban, elev)
            table = model.get_full_year_table()

            # Sample critical dates
            print(f"\nSpecies: {sp.replace('_', ' ').title()}")

            # Find Spring Bloom/Flush (approximate by color change from dormant/old)
            # Find Fall Peak

            s_date = datetime.date(2023, 4, 15)
            f_date = datetime.date(2023, 10, 20)

            s_col = model.timeline.loc[model.timeline['date'] == s_date].iloc[0]['color_rgb']
            f_col = model.timeline.loc[model.timeline['date'] == f_date].iloc[0]['color_rgb']

            print(f"  Spring ({s_date}): {s_col}")
            print(f"  Fall   ({f_date}): {f_col}")
