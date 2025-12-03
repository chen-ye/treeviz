import requests
import requests_cache
from PIL import Image
from io import BytesIO
import math
import mercantile
import mapbox_vector_tile
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.strtree import STRtree
from shapely.ops import unary_union

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


class OpenFreeMapLandUseFetcher:
    """
    Fetch landuse/landcover vector tiles from tiles.openfreemap.org and classify
    points as urban/non-urban using vector polygons.

    Notes:
    - Caches vector tiles using `requests_cache`.
    - Decodes Mapbox Vector Tile (MVT/PBF) using `mapbox_vector_tile`.
    - Converts tile coordinates to WGS84 using the tile bbox and the MVT extent.
    - Falls back to `LandUseFetcher` (Overpass) when tiles are missing or no match.
    """

    URBAN_TAGS = {
        "residential",
        "commercial",
        "retail",
        "industrial",
        "brownfield",
        "construction",
        "quarry",
        "urban",
    }

    NON_URBAN_TAGS = {
        "park",
        "grass",
        "forest",
        "meadow",
        "farmland",
        "orchard",
    }

    def __init__(self, zoom=14, cache_name=".ofm_tiles_cache", cache_expire=604800):
        self.zoom = zoom
        self.tilejson_url = "https://tiles.openfreemap.org/planet"
        self.tile_url = None
        self.session = requests_cache.CachedSession(cache_name, expire_after=cache_expire)
        # try to fetch TileJSON template now, fall back to a sane default on error
        try:
            tjr = self.session.get(self.tilejson_url, timeout=10)
            tjr.raise_for_status()
            tj = tjr.json()
            tiles = tj.get("tiles") or []
            if tiles:
                # use the first template
                self.tile_url = tiles[0]
        except Exception:
            # leave tile_url as None; _fetch_tile will fallback to guessed path
            self.tile_url = None
        # Default MVT extent is typically 4096
        self.extent = 4096
        # Prefer the Overpass-based `LandUseFetcher` as a fallback (more specific than the simple distance heuristic)
        self.fallback = LandUseFetcher()

    def _tile_coords(self, lat, lon):
        t = mercantile.tile(lon, lat, self.zoom)
        return t.x, t.y, t.z

    def _fetch_tile(self, x, y, z):
        # prefer the TileJSON-provided template if available
        if self.tile_url:
            url = self.tile_url.format(z=z, x=x, y=y)
        else:
            url = f"https://tiles.openfreemap.org/planet/{z}/{x}/{y}.pbf"
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            return r.content
        except Exception:
            return None

    def _tile_pixel_coords(self, lat, lon, tile_x, tile_y, z):
        """Return (px, py) in 0..extent for a lat/lon within a tile."""
        bounds = mercantile.bounds(tile_x, tile_y, z)
        west, south, east, north = bounds.west, bounds.south, bounds.east, bounds.north
        # normalize into tile coordinate space (0..extent)
        x = (lon - west) / (east - west) * self.extent
        y = (north - lat) / (north - south) * self.extent
        return x, y

    def _neighbor_keys_for_point(self, lat, lon, tile_x, tile_y, z, margin_px=64):
        """
        Return list of tile keys (x,y,z) to fetch for a point.
        If the point is within `margin_px` of a tile edge (in tile pixels), include neighbors.
        """
        px, py = self._tile_pixel_coords(lat, lon, tile_x, tile_y, z)
        keys = {(tile_x, tile_y, z)}
        # include neighbors if within margin of any edge
        if px < margin_px:
            keys.add(((tile_x - 1), tile_y, z))
        if px > (self.extent - margin_px):
            keys.add(((tile_x + 1), tile_y, z))
        if py < margin_px:
            keys.add((tile_x, (tile_y - 1), z))
        if py > (self.extent - margin_px):
            keys.add((tile_x, (tile_y + 1), z))
        # diagonals
        if px < margin_px and py < margin_px:
            keys.add(((tile_x - 1), (tile_y - 1), z))
        if px < margin_px and py > (self.extent - margin_px):
            keys.add(((tile_x - 1), (tile_y + 1), z))
        if px > (self.extent - margin_px) and py < margin_px:
            keys.add(((tile_x + 1), (tile_y - 1), z))
        if px > (self.extent - margin_px) and py > (self.extent - margin_px):
            keys.add(((tile_x + 1), (tile_y + 1), z))

        # clamp x to valid range [0, 2^z - 1]; clamp y to [0, 2^z - 1]
        max_idx = (2 ** z) - 1
        clamped = set()
        for tx, ty, tz in keys:
            if tx < 0 or tx > max_idx or ty < 0 or ty > max_idx:
                continue
            clamped.add((tx, ty, tz))
        return clamped

    def _decode_tile(self, tile_content):
        try:
            return mapbox_vector_tile.decode(tile_content)
        except Exception:
            return None

    def _tile_geom_to_lonlat(self, geom, tile_x, tile_y, z):
        """
        Convert geometry coordinates from tile space (0..extent) to lon/lat.
        Accepts GeoJSON-like coordinate sequences and returns transformed sequences.
        """
        bounds = mercantile.bounds(tile_x, tile_y, z)
        west, south, east, north = bounds.west, bounds.south, bounds.east, bounds.north

        def conv_coord(pt):
            # pt is (x, y) in tile coordinates (origin top-left)
            x, y = pt
            lon = west + (x / self.extent) * (east - west)
            lat = north - (y / self.extent) * (north - south)
            return (lon, lat)

        def conv_coords(coords):
            return [conv_coord(tuple(c)) for c in coords]

        # geom can be nested (Polygon -> list of rings), MultiPolygon -> list of polygons
        if isinstance(geom[0][0], (list, tuple)):
            # Polygon or MultiPolygon
            if isinstance(geom[0][0][0], (list, tuple)):
                # MultiPolygon: list of polygons where each polygon is list of rings
                return [[conv_coords(ring) for ring in poly] for poly in geom]
            else:
                # Polygon: list of rings
                return [conv_coords(ring) for ring in geom]
        else:
            # LineString or single ring
            return conv_coords(geom)

    def _extract_polygons(self, decoded, tile_x, tile_y, z):
        """Return list of tuples (shapely_geom, properties)"""
        polygons = []
        if not decoded:
            return polygons

        for layer_name, layer in decoded.items():
            # `mapbox_vector_tile.decode` can return either:
            # - layer -> {'features': [ ... ]} or
            # - layer -> [ feature, feature, ... ]
            # Normalize to a features list and guard against unexpected types.
            features = []
            if isinstance(layer, dict):
                if "features" in layer and isinstance(layer["features"], list):
                    features = layer["features"]
                else:
                    # Some decoders may produce a dict of id->feature or other nested structures.
                    # Try these fallbacks in order:
                    # 1. a dict value that is a list (e.g., nested 'features').
                    # 2. dict values that look like feature dicts (have 'geometry' or 'properties').
                    candidates = [v for v in layer.values() if isinstance(v, list)]
                    if candidates:
                        features = candidates[0]
                    else:
                        dict_feature_vals = [v for v in layer.values() if isinstance(v, dict) and ("geometry" in v or "properties" in v)]
                        if dict_feature_vals:
                            features = dict_feature_vals
            elif isinstance(layer, list):
                features = layer

            for feat in features:
                if not isinstance(feat, dict):
                    # skip unexpected entries
                    continue
                props = feat.get("properties", {})
                geom = feat.get("geometry")
                if geom is None:
                    continue

                # If the geometry appears to already be lon/lat, try to build directly
                try:
                    first_coord = None
                    if geom:
                        # drill down to first numeric coordinate
                        if isinstance(geom[0][0], (int, float)):
                            first_coord = geom[0]
                        else:
                            # polygon/multipolygon
                            iter0 = geom
                            while iter0 and isinstance(iter0[0], list):
                                iter0 = iter0[0]
                            if iter0 and isinstance(iter0[0], (int, float)):
                                first_coord = iter0
                    lonlat_mode = False
                    if first_coord is not None:
                        # If coordinates look like lon/lat values
                        if -180.0 <= first_coord[0] <= 180.0 and -90.0 <= first_coord[1] <= 90.0:
                            lonlat_mode = True
                except Exception:
                    lonlat_mode = False

                try:
                    if lonlat_mode:
                        geom_shape = shape({"type": feat.get("type", "Polygon"), "coordinates": geom})
                    else:
                        # convert tile coords to lon/lat
                        conv = self._tile_geom_to_lonlat(geom, tile_x, tile_y, z)
                        geom_shape = shape({"type": feat.get("type", "Polygon"), "coordinates": conv})

                    # keep only polygonal geometries
                    if isinstance(geom_shape, (Polygon, MultiPolygon)):
                        polygons.append((geom_shape, props))
                except Exception:
                    # decoding/geometry construction failed for this feature
                    continue

        return polygons

    def _properties_indicate_urban(self, props):
        # check common keys for landuse/class tags
        for key in ("landuse", "class", "type", "kind", "natural"):
            val = props.get(key)
            if not val:
                continue
            v = str(val).lower()
            if v in self.URBAN_TAGS:
                return True
            if v in self.NON_URBAN_TAGS:
                return False

        # buildings imply urban
        if props.get("building"):
            return True

        return None

    def is_urban_environment(self, lat, lon):
        x, y, z = self._tile_coords(lat, lon)
        tile_content = self._fetch_tile(x, y, z)
        if not tile_content:
            return self.fallback.is_urban_environment(lat, lon)

        decoded = self._decode_tile(tile_content)
        polygons = self._extract_polygons(decoded, x, y, z)

        pt = Point(lon, lat)
        # check polygons
        for geom, props in polygons:
            try:
                if geom.contains(pt) or geom.touches(pt):
                    hit = self._properties_indicate_urban(props)
                    if hit is not None:
                        return hit
                    # if properties inconclusive, prefer treating buildings as urban
                    if props.get("building"):
                        return True
            except Exception:
                continue

        # no decisive polygon found; fallback to Overpass-based LandUseFetcher
        return self.fallback.is_urban_environment(lat, lon)

    def is_urban_batch(self, points):
        """Classify a list of (lat, lon) -> True/False. Groups by tile to reduce requests."""
        results = [None] * len(points)
        tiles = {}
        groups = {}
        for i, (lat, lon) in enumerate(points):
            t = mercantile.tile(lon, lat, self.zoom)
            key = (t.x, t.y, t.z)
            groups.setdefault(key, []).append((i, lat, lon))

        total_points = len(points)
        points_done = 0
        for (tx, ty, tz), pts in groups.items():
            print(f"Processing tile {tz}/{tx}/{ty} for {len(pts)} points... ({points_done + len(pts)}/{total_points} total)")
            tile_content = self._fetch_tile(tx, ty, tz)
            if tile_content:
                try:
                    print(f"  fetched tile {tz}/{tx}/{ty} ({len(tile_content)} bytes)")
                except Exception:
                    print(f"  fetched tile {tz}/{tx}/{ty}")
            else:
                print(f"  tile {tz}/{tx}/{ty} not available; will fallback for contained points")
            decoded = self._decode_tile(tile_content) if tile_content else None
            polygons = self._extract_polygons(decoded, tx, ty, tz)

            # Build STRtree for spatial index (if polygons exist)
            if polygons:
                geoms = [geom for geom, _ in polygons]
                strtree = STRtree(geoms)
            else:
                strtree = None

            for i, lat, lon in pts:
                pt = Point(lon, lat)
                matched = None
                candidates = []
                if strtree:
                    # Query spatial index for candidate polygons
                    candidates = strtree.query(pt)
                else:
                    candidates = []

                print(f"    Point ({lat:.5f}, {lon:.5f}) has {len(candidates)} candidate polygons")

                # Find the first candidate polygon that contains/touches the point and has a decisive tag
                for geom in candidates:
                    # Find the associated properties
                    idx = geoms.index(geom)
                    props = polygons[idx][1]
                    try:
                        if geom.contains(pt) or geom.touches(pt):
                            hit = self._properties_indicate_urban(props)
                            if hit is not None:
                                matched = hit
                                break
                            if props.get("building"):
                                matched = True
                                break
                    except Exception:
                        continue

                if matched is None:
                    matched = self.fallback.is_urban_environment(lat, lon)
                results[i] = matched

        return results
