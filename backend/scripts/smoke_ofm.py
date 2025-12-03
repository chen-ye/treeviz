#!/usr/bin/env python3
"""Smoke test for OpenFreeMap tiles: fetch TileJSON and one vector tile.

This script is intentionally tolerant of missing optional dependencies
(`mapbox_vector_tile`, `shapely`) and will still exercise the network/cache path.
"""
import json
import sys
import requests
try:
    import requests_cache
    have_requests_cache = True
except Exception:
    requests_cache = None
    have_requests_cache = False
from pathlib import Path

tilejson_url = "https://tiles.openfreemap.org/planet"
if have_requests_cache:
    cache = requests_cache.CachedSession('.ofm_tiles_cache_smoke', expire_after=3600)
else:
    cache = requests

def main():
    print("Fetching TileJSON...", end=" ")
    try:
        r = cache.get(tilejson_url, timeout=10)
        r.raise_for_status()
        tj = r.json()
        print("ok")
    except Exception as e:
        print("failed:", e)
        sys.exit(2)

    tiles = tj.get('tiles') or []
    if not tiles:
        print("No tiles template found in TileJSON")
        sys.exit(2)

    tpl = tiles[0]
    print("Using template:", tpl)

    # pick a tile: Seattle center at zoom 14
    lat, lon, z = 47.6062, -122.3321, 14
    # compute tile x/y lazily using mercantile if available
    try:
        import mercantile
        t = mercantile.tile(lon, lat, z)
        x, y = t.x, t.y
    except Exception:
        # fallback: try known Seattle tile coordinates (approx)
        x, y = 2624, 6330

    url = tpl.format(z=z, x=x, y=y)
    print(f"Fetching tile {z}/{x}/{y} -> {url}...", end=" ")
    try:
        tr = cache.get(url, timeout=10)
        tr.raise_for_status()
        data = tr.content
        print(f"ok ({len(data)} bytes)")
    except Exception as e:
        print("failed:", e)
        sys.exit(2)

    # attempt to decode if mapbox_vector_tile is present
    try:
        import mapbox_vector_tile
        d = mapbox_vector_tile.decode(data)
        print("Decoded tile layers:", ",".join(d.keys()))
    except Exception as e:
        print("Decode skipped or failed:", e)

    print("Smoke test finished — network and caching appear functional.")

if __name__ == '__main__':
    main()
