"""Base classes for phenology modeling."""
from abc import ABC, abstractmethod
import pandas as pd
from astral.sun import sun
from astral import LocationInfo

class TreePhenologyModel(ABC):
    """
    Base class for tree phenology models.

    Attributes:
        weather_df (pd.DataFrame): Daily weather data for the year.
        lat (float): Latitude of the tree/grid cell.
        lon (float): Longitude of the tree/grid cell.
        is_urban (bool): Whether the location is in an urban environment.
        elevation (float): Elevation in meters.
        timeline (pd.DataFrame): Computed phenology timeline.
    """
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
        """Linear interpolation between two RGB colors."""
        factor = max(0.0, min(1.0, factor))
        return tuple(int(a + (b - a) * factor) for a, b in zip(c1, c2))

    def _calculate_base_timeline(self) -> pd.DataFrame:
        """
        Calculate the base phenology timeline using weather data.
        This method computes derived variables (if not already present) and applies the species-specific color logic.
        """
        df = self.weather_df.copy()

        # Ensure required columns exist (they should be pre-computed, but safety check)
        required_cols = ['day_length', 'accumulated_gdd', 'accumulated_chill', 'is_fall_season']
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            # If variables weren't pre-computed, compute them now (fallback logic)
            # This allows the model to work with raw weather data too
            self._compute_derived_variables(df)

        # Apply stress factors (these are usually dynamic/derived)
        # 1. Freeze
        df['is_freeze_day'] = df['min_temp'] < -3.0
        df['recent_freeze'] = df['is_freeze_day'].rolling(window=14, min_periods=1).max().fillna(0).astype(bool)

        # 2. Drought
        if 'soil_moisture' in df.columns:
            df['rolling_moisture'] = df['soil_moisture'].rolling(window=14, min_periods=1).mean()
            df['is_drought'] = df['rolling_moisture'] < 0.15
            df['is_severe_drought'] = df['rolling_moisture'] < 0.08
        else:
            df['is_drought'] = False
            df['is_severe_drought'] = False

        # 3. UV/Elevation
        df['uv_stress_factor'] = min(1.0, self.elevation / 1000.0)

        # Apply Species Specific Color Logic
        df['color_rgb'] = df.apply(self._resolve_daily_color, axis=1)

        return df

    def _compute_derived_variables(self, df):
        """Compute phenology variables if missing from input."""
        # 1. Photoperiod
        def get_day_length(row):
            try:
                s = sun(self.location.observer, date=row['date'])
                return (s['sunset'] - s['sunrise']).total_seconds() / 3600.0
            except:
                return 12.0

        if 'day_length' not in df.columns:
            df['day_length'] = df.apply(get_day_length, axis=1)

        # 2. Seasons
        fall_mask = df['day_length'] < 12.0
        if fall_mask.any():
            fall_idx = fall_mask.idxmax()
            df['is_fall_season'] = df.index >= fall_idx
        else:
            df['is_fall_season'] = False

        # 3. GDD
        df['mean_temp'] = (df['max_temp'] + df['min_temp']) / 2
        df['daily_gdd'] = (df['mean_temp'] - 10.0).clip(lower=0)
        df['accumulated_gdd'] = df['daily_gdd'].cumsum()

        # 4. Chill
        df['daily_chill'] = (15.0 - df['max_temp']).clip(lower=0)
        df.loc[~df['is_fall_season'], 'daily_chill'] = 0
        df['accumulated_chill'] = df['daily_chill'].cumsum()

        if self.is_urban:
            df['accumulated_chill'] *= 0.80

    @abstractmethod
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        """
        Determine the tree's color for a specific day based on weather/environmental state.
        Must be implemented by subclasses.
        """
        pass

    def get_timeline(self) -> list[tuple[int, int, int]]:
        """Return the list of RGB colors for the year."""
        if self.timeline.empty:
            return []
        return self.timeline['color_rgb'].tolist()
