import requests
from PIL import Image
from io import BytesIO
import math

# TODO: can we utilize tiled data to get elevation and urban status? Much faster than individual queries.
# Look into https://registry.opendata.aws/terrain-tiles/ for terrain tiles
# Look into https://tiles.openfreemap.org/planet for landuse tiles

class TiledElevationFetcher:
    """
    Fetch elevation data from AWS Terrain Tiles (Terrarium format).

    This is orders of magnitude faster than individual API calls:
    - Individual API: 2000 trees = 2000 requests = 15+ minutes
    - Tiled approach: 2000 trees = ~6 tiles = 5-10 seconds

    Tile format: https://registry.opendata.aws/terrain-tiles/
    Encoding: (R * 256 + G + B / 256) - 32768 meters
    """

    def __init__(self, zoom=14):
        """
        Args:
            zoom: Tile zoom level. Higher = more detail but more tiles.
                  14 = ~30m resolution (good for tree-level data)
                  13 = ~60m resolution (faster, fewer tiles)
        """
        self.zoom = zoom
        self.tile_cache = {}
        self.base_url = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium"

    def lat_lon_to_tile(self, lat, lon, zoom):
        """Convert lat/lon to tile coordinates (x, y, z)."""
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (x, y, zoom)

    def get_tile(self, x, y, z):
        """Fetch and cache a terrain tile."""
        key = (x, y, z)
        if key in self.tile_cache:
            return self.tile_cache[key]

        url = f"{self.base_url}/{z}/{x}/{y}.png"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            tile = Image.open(BytesIO(response.content))
            self.tile_cache[key] = tile
            return tile
        except Exception as e:
            print(f"Warning: Failed to fetch tile {x},{y}@{z}: {e}")
            return None

    def get_elevation(self, lat, lon):
        """
        Get elevation for a lat/lon point.

        Returns:
            Elevation in meters, or None if unavailable.
        """
        x, y, z = self.lat_lon_to_tile(lat, lon, self.zoom)
        tile = self.get_tile(x, y, z)

        if tile is None:
            return None

        # Calculate pixel position within tile (256x256)
        n = 2.0 ** z
        lat_rad = math.radians(lat)
        x_tile = ((lon + 180.0) / 360.0 * n)
        y_tile = ((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)

        px = int((x_tile - x) * 256)
        py = int((y_tile - y) * 256)

        # Clamp to tile bounds
        px = max(0, min(255, px))
        py = max(0, min(255, py))

        # Decode elevation from RGB (Terrarium encoding)
        try:
            r, g, b = tile.getpixel((px, py))[:3]
            elevation = (r * 256 + g + b / 256) - 32768
            return elevation
        except Exception as e:
            print(f"Warning: Failed to decode elevation at {lat},{lon}: {e}")
            return None


class SimpleLandUseFetcher:
    """
    Simplified land use fetcher using heuristic-based classification.

    For now, uses a simple distance-to-city-center heuristic.
    Future: Could be upgraded to use OpenStreetMap vector tiles for precise data.

    Seattle city center: 47.6062, -122.3321
    Urban radius: ~10km for dense urban, ~20km for suburban
    """

    def __init__(self):
        # Seattle city center
        self.city_center = (47.6062, -122.3321)
        self.urban_radius_km = 8.0  # Dense urban core

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance in km between two lat/lon points."""
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def is_urban_environment(self, lat, lon):
        """
        Determine if location is urban.

        Simplified heuristic: distance from city center.
        Returns True if within urban radius.
        """
        distance = self.haversine_distance(lat, lon, *self.city_center)
        return distance < self.urban_radius_km


# Legacy classes for backward compatibility (deprecated)
class LandUseFetcher:
    """Deprecated: Use SimpleLandUseFetcher instead (much faster)."""
    def __init__(self):
        self.overpass_url = "http://overpass-api.de/api/interpreter"

    def is_urban_environment(self, lat, lon, radius_m=100):
        """DEPRECATED: Very slow, makes individual API calls."""
        print("WARNING: Using deprecated LandUseFetcher. Switch to SimpleLandUseFetcher.")
        # Fallback to simple heuristic
        fetcher = SimpleLandUseFetcher()
        return fetcher.is_urban_environment(lat, lon)


class ElevationFetcher:
    """Deprecated: Use TiledElevationFetcher instead (100-1000x faster)."""
    def __init__(self):
        self.api_url = "https://api.open-elevation.com/api/v1/lookup"

    def get_elevation(self, lat, lon):
        """DEPRECATED: Very slow, makes individual API calls."""
        print("WARNING: Using deprecated ElevationFetcher. Switch to TiledElevationFetcher.")
        # Fallback to tiled fetcher
        fetcher = TiledElevationFetcher()
        return fetcher.get_elevation(lat, lon)
