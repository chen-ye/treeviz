import requests
import requests_cache

# TODO: can we utilize tiled data to get elevation and urban status? Much faster than individual queries.
# Look into https://registry.opendata.aws/terrain-tiles/ for terrain tiles
# Look into https://tiles.openfreemap.org/planet for landuse tiles

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
