"""Weather data fetching and processing."""
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import date, timedelta
from astral.sun import sun
from astral import LocationInfo
from sqlalchemy.orm import Session
from .database import WeatherGridCell, WeatherData

class WeatherFetcher:
    def __init__(self):
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)
        self.url = "https://archive-api.open-meteo.com/v1/archive"

    def fetch_year(self, lat: float, lon: float, year: int) -> pd.DataFrame:
        """Fetch daily weather data for a full year."""
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

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

            # Process Daily Data
            daily = response.Daily()
            daily_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                    end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=daily.Interval()),
                    inclusive="left"
                ).date,
                "max_temp": daily.Variables(0).ValuesAsNumpy(),
                "min_temp": daily.Variables(1).ValuesAsNumpy(),
                "sunshine_duration": daily.Variables(2).ValuesAsNumpy(),
                "precipitation_sum": daily.Variables(3).ValuesAsNumpy()
            }
            df_daily = pd.DataFrame(data=daily_data)

            # Process Hourly Data (for soil moisture aggregation)
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

            # Aggregate hourly soil moisture to daily mean
            daily_soil = df_hourly.groupby('date')['soil_moisture'].mean().reset_index()

            # Merge
            df_final = pd.merge(df_daily, daily_soil, on='date', how='left')
            return df_final.sort_values(by="date").reset_index(drop=True)

        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return pd.DataFrame()

def compute_phenology_variables(df: pd.DataFrame, lat: float, lon: float, is_urban: bool = False) -> pd.DataFrame:
    """Compute GDD, Chill Units, and Day Length."""
    df = df.copy()
    location = LocationInfo(latitude=lat, longitude=lon)

    # 1. Photoperiod (Day Length)
    def get_day_length(row):
        try:
            s = sun(location.observer, date=row['date'])
            return (s['sunset'] - s['sunrise']).total_seconds() / 3600.0
        except:
            return 12.0
    df['day_length'] = df.apply(get_day_length, axis=1)

    # 2. Seasons (Trigger based) - needed for Chill accumulation logic
    # Fall Trigger: Day length < 12h
    fall_mask = df['day_length'] < 12.0
    if fall_mask.any():
        fall_idx = fall_mask.idxmax()
        df['is_fall_season'] = df.index >= fall_idx
    else:
        df['is_fall_season'] = False

    # 3. Growing Degree Days (GDD)
    # Base temp 10C
    df['mean_temp'] = (df['max_temp'] + df['min_temp']) / 2
    df['daily_gdd'] = (df['mean_temp'] - 10.0).clip(lower=0)
    df['accumulated_gdd'] = df['daily_gdd'].cumsum()

    # 4. Chill Units
    # Threshold 15C, only accumulates in fall/winter
    df['daily_chill'] = (15.0 - df['max_temp']).clip(lower=0)
    # Only accumulate chill if it's fall season (or late year)
    # Simplified logic: zero out chill before fall start
    df.loc[~df['is_fall_season'], 'daily_chill'] = 0
    df['accumulated_chill'] = df['daily_chill'].cumsum()

    if is_urban:
        # Urban heat island effect reduces chill accumulation
        df['accumulated_chill'] *= 0.80

    return df

def store_weather_data(db: Session, grid_cell: WeatherGridCell, df: pd.DataFrame):
    """Store processed weather data in the database."""
    # Clear existing data for this cell/year range to avoid duplicates
    # (Simplified: assuming we fetch full years)
    start_date = df['date'].min()
    end_date = df['date'].max()

    db.query(WeatherData).filter(
        WeatherData.grid_cell_id == grid_cell.id,
        WeatherData.date >= start_date,
        WeatherData.date <= end_date
    ).delete()

    # Bulk insert
    weather_objects = []
    for _, row in df.iterrows():
        obj = WeatherData(
            grid_cell_id=grid_cell.id,
            date=row['date'],
            max_temp=row['max_temp'],
            min_temp=row['min_temp'],
            sunshine_duration=row['sunshine_duration'],
            precipitation_sum=row['precipitation_sum'],
            soil_moisture=row['soil_moisture'],
            day_length=row['day_length'],
            accumulated_gdd=row['accumulated_gdd'],
            accumulated_chill=row['accumulated_chill']
        )
        weather_objects.append(obj)

    db.bulk_save_objects(weather_objects)
    db.commit()
