"""Base classes for phenology modeling."""
from abc import ABC, abstractmethod
import colorsys
import math
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

        # Pre-calculate modifiers
        self._calculate_modifiers()

        if not self.weather_df.empty:
            self.timeline = self._calculate_base_timeline()
        else:
            self.timeline = pd.DataFrame()

    def _calculate_modifiers(self):
        """Calculate environment modifiers based on static location data."""
        # 1. Urban Heat Island
        # Urban areas are warmer.
        # Effect: Accelerates GDD accumulation (Spring), Delays Chill accumulation (Fall/Winter).
        self.urban_gdd_mod = 0.9 if self.is_urban else 1.0 # Requires LESS global GDD to reach target
        self.urban_chill_mod = 1.1 if self.is_urban else 1.0 # Requires MORE global Chill (harder to get chill)

        # 2. Elevation
        # Higher elevation is colder.
        # Lapse rate approx 6.5C per 1000m.
        # Effect: Delays GDD (Spring), Accelerates Chill (Fall/Winter).
        # We simplify this to threshold modifiers.
        elevation_km = self.elevation / 1000.0
        # For GDD: It's colder, so we accumulate GDD slower locally.
        # To match local reality with global data, we need MORE global GDD to simulate the delay.
        self.elevation_gdd_mod = 1.0 + (0.15 * elevation_km)
        # For Chill: It's colder, so we accumulate Chill faster locally.
        # We need LESS global Chill to reach target.
        self.elevation_chill_mod = max(0.5, 1.0 - (0.15 * elevation_km))

    def get_adjusted_threshold(self, threshold: float, metric: str) -> float:
        """
        Adjust a threshold based on local microclimate.

        Args:
            threshold: The base biological threshold.
            metric: 'gdd', 'chill', or 'day_length' (usually not modified but kept for consistency)
        """
        if metric == 'gdd':
            # Urban -> Lower threshold (happens sooner)
            # Elevation -> Higher threshold (happens later)
            return threshold * self.urban_gdd_mod * self.elevation_gdd_mod
        elif metric == 'chill':
            # Urban -> Higher threshold (happens later/harder)
            # Elevation -> Lower threshold (happens sooner)
            return threshold * self.urban_chill_mod * self.elevation_chill_mod

        return threshold

    def _calc_progress(self, value: float, start: float, end: float) -> float:
        """Calculate progress float (0.0 to 1.0) within a window."""
        if start == end:
            return 1.0 if value >= start else 0.0

        progress = (value - start) / (end - start)
        return max(0.0, min(1.0, progress))

    def _interp_hsl(self, c1: tuple[int, int, int], c2: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        """
        Interpolate between two RGB colors using HSL space.
        This produces more natural biological transitions (e.g. Green -> Red passes through Yellow/Orange).
        """
        factor = max(0.0, min(1.0, factor))

        # Convert RGB (0-255) to RGB (0-1)
        r1, g1, b1 = c1[0]/255.0, c1[1]/255.0, c1[2]/255.0
        r2, g2, b2 = c2[0]/255.0, c2[1]/255.0, c2[2]/255.0

        # Convert to HLS
        h1, l1, s1 = colorsys.rgb_to_hls(r1, g1, b1)
        h2, l2, s2 = colorsys.rgb_to_hls(r2, g2, b2)

        # Handle Hue wrapping (shortest path)
        # If difference is > 0.5, wrap around
        if abs(h1 - h2) > 0.5:
            if h1 > h2:
                h2 += 1.0
            else:
                h1 += 1.0

        # Interpolate
        h = h1 + (h2 - h1) * factor
        l = l1 + (l2 - l1) * factor
        s = s1 + (s2 - s1) * factor

        # Unwrap Hue
        if h > 1.0: h -= 1.0

        # Convert back to RGB
        r, g, b = colorsys.hls_to_rgb(h, l, s)

        return (int(r*255), int(g*255), int(b*255))

    def _interp(self, c1, c2, factor):
        """Legacy RGB Interpolation (kept for backward compat if needed, but prefer HSL)."""
        return self._interp_hsl(c1, c2, factor)

    def _calculate_base_timeline(self) -> pd.DataFrame:
        """
        Calculate the base phenology timeline using weather data.
        """
        df = self.weather_df.copy()

        # Ensure required columns exist
        required_cols = ['day_length', 'accumulated_gdd', 'accumulated_chill', 'is_fall_season']
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            self._compute_derived_variables(df)

        # Apply stress factors
        # 1. Freeze
        df['is_freeze_day'] = df['min_temp'] < -3.0
        df['recent_freeze'] = df['is_freeze_day'].rolling(window=14, min_periods=1).max().fillna(0).astype(bool)

        # 2. Drought
        if 'soil_moisture' in df.columns:
            df['rolling_moisture'] = df['soil_moisture'].rolling(window=14, min_periods=1).mean()
            # Drought stress might accelerate fall color or cause leaf drop
            # We provide a 0-1 stress factor
            # Assuming soil moisture 0.3-0.4 is capacity, <0.15 is stress
            df['drought_stress'] = (0.15 - df['rolling_moisture']).clip(lower=0) / 0.15
        else:
            df['drought_stress'] = 0.0

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

        # 2. Seasons (Based on Day Length Trend)
        # Fall starts when day length drops below threshold?
        # Or better: when day length is decreasing and below X?
        # Simple approximation: After Summer Solstice (~June 21)
        # But here we just use day length < 12 as a marker for equinox.
        # We need to distinguish Spring (<12 increasing) vs Fall (<12 decreasing).

        # Determine day of year
        df['doy'] = pd.to_datetime(df['date']).dt.dayofyear

        # Approx Northern Hemisphere: Fall is after ~June 21 (DOY 172)
        # Actually "Fall Season" for phenology usually starts late summer.
        # Let's say DOY > 200 (July 19) is potentially fall season context
        df['is_fall_season'] = df['doy'] > 200

        # 3. GDD
        df['mean_temp'] = (df['max_temp'] + df['min_temp']) / 2
        df['daily_gdd'] = (df['mean_temp'] - 10.0).clip(lower=0)
        df['accumulated_gdd'] = df['daily_gdd'].cumsum()

        # 4. Chill
        # Chill accumulation usually starts when temp drops below threshold (e.g. 7C or 15C)
        # And usually resets or matters for next year.
        # For fall color, sometimes cold accumulates.
        # Simplification: Cumulative cold stress
        df['daily_chill'] = (15.0 - df['max_temp']).clip(lower=0)
        # Only accumulate chill in fall/winter?
        # Existing logic masked it for non-fall season.
        df.loc[~df['is_fall_season'], 'daily_chill'] = 0
        df['accumulated_chill'] = df['daily_chill'].cumsum()

        # Note: We do NOT apply urban modifier here anymore, because we apply it to thresholds.

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
