"""Utilities for managing weather grid cells."""
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from .database import SessionLocal, WeatherGridCell, Tree
from geoalchemy2.functions import ST_MakePoint, ST_Distance
import math

def get_tree_extents():
    """Query the bounding box of all trees."""
    db = SessionLocal()
    try:
        query = text("""
            SELECT
                ST_XMin(extent) as min_lon,
                ST_YMin(extent) as min_lat,
                ST_XMax(extent) as max_lon,
                ST_YMax(extent) as max_lat
            FROM (
                SELECT ST_Extent(geom) as extent
                FROM trees
            ) as subquery;
        """)

        result = db.execute(query).fetchone()
        if result:
            return {
                "min_lon": result.min_lon,
                "min_lat": result.min_lat,
                "max_lon": result.max_lon,
                "max_lat": result.max_lat
            }
        return None
    finally:
        db.close()

def create_grid_for_region(grid_km: float = 9.0):
    """
    Create a grid of cells covering the tree data extent.

    Args:
        grid_km: Grid cell size in kilometers (default 9km for ECMWF IFS)

    Returns:
        List of WeatherGridCell objects (not yet persisted)
    """
    bounds = get_tree_extents()
    if not bounds:
        print("No tree data found")
        return []

    # Calculate grid dimensions
    # At 47.6°N: 1° lat ≈ 111 km, 1° lon ≈ 75 km
    lat_per_km = 1.0 / 111.0
    lon_per_km = 1.0 / 75.0

    lat_step = grid_km * lat_per_km
    lon_step = grid_km * lon_per_km

    # Calculate number of cells needed
    width_deg = bounds["max_lon"] - bounds["min_lon"]
    height_deg = bounds["max_lat"] - bounds["min_lat"]

    num_lon_cells = math.ceil(width_deg / lon_step)
    num_lat_cells = math.ceil(height_deg / lat_step)

    print(f"Creating {num_lon_cells}×{num_lat_cells} = {num_lon_cells * num_lat_cells} grid cells")
    print(f"Grid size: {grid_km}km ({lat_step:.4f}° lat × {lon_step:.4f}° lon)")

    cells = []
    for i in range(num_lon_cells):
        for j in range(num_lat_cells):
            # Cell center point
            lon = bounds["min_lon"] + (i + 0.5) * lon_step
            lat = bounds["min_lat"] + (j + 0.5) * lat_step

            cell = WeatherGridCell(
                lat=lat,
                lon=lon,
                geom=f'SRID=4326;POINT({lon} {lat})'
            )
            cells.append(cell)

    return cells

def assign_trees_to_grid():
    """Assign each tree to its nearest weather grid cell using PostGIS."""
    db = SessionLocal()
    try:
        # Use PostGIS to find nearest grid cell for each tree
        query = text("""
            WITH tree_grid AS (
                SELECT
                    t.id as tree_id,
                    (
                        SELECT g.id
                        FROM weather_grid_cells g
                        ORDER BY ST_Distance(t.geom, g.geom)
                        LIMIT 1
                    ) as grid_id
                FROM trees t
            )
            UPDATE trees
            SET weather_grid_cell_id = tree_grid.grid_id
            FROM tree_grid
            WHERE trees.id = tree_grid.tree_id;
        """)

        result = db.execute(query)
        db.commit()

        rows_updated = result.rowcount
        print(f"Assigned {rows_updated} trees to grid cells")

        # Show distribution
        query = text("""
            SELECT
                g.id,
                g.lat,
                g.lon,
                COUNT(t.id) as tree_count
            FROM weather_grid_cells g
            LEFT JOIN trees t ON t.weather_grid_cell_id = g.id
            GROUP BY g.id, g.lat, g.lon
            ORDER BY g.id;
        """)

        results = db.execute(query).fetchall()
        print("\nTree distribution across grid cells:")
        for row in results:
            print(f"  Cell {row.id} ({row.lat:.4f}, {row.lon:.4f}): {row.tree_count} trees")

    finally:
        db.close()

def get_grid_cell_for_point(lat: float, lon: float):
    """Find the nearest weather grid cell for a given point."""
    db = SessionLocal()
    try:
        query = text("""
            SELECT id, lat, lon,
                   ST_Distance(geom, ST_MakePoint(:lon, :lat)::geography) as distance
            FROM weather_grid_cells
            ORDER BY distance
            LIMIT 1;
        """)

        result = db.execute(query, {"lat": lat, "lon": lon}).fetchone()
        if result:
            return {
                "id": result.id,
                "lat": result.lat,
                "lon": result.lon,
                "distance_m": result.distance
            }
        return None
    finally:
        db.close()
