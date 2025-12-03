"""Query the spatial extents of tree data to determine bounding box."""
# from dotenv import load_dotenv
# load_dotenv()

from sqlalchemy import text
from .database import SessionLocal

def query_tree_extents():
    """Query the bounding box of all trees in the database."""
    db = SessionLocal()
    try:
        # Use PostGIS ST_Extent to get bounding box
        query = text("""
            SELECT
                ST_XMin(extent) as min_lon,
                ST_YMin(extent) as min_lat,
                ST_XMax(extent) as max_lon,
                ST_YMax(extent) as max_lat,
                ST_X(ST_Centroid(extent)) as center_lon,
                ST_Y(ST_Centroid(extent)) as center_lat
            FROM (
                SELECT ST_Extent(geom) as extent
                FROM trees
            ) as subquery;
        """)

        result = db.execute(query).fetchone()

        if result:
            bounds = {
                "min_lon": result.min_lon,
                "min_lat": result.min_lat,
                "max_lon": result.max_lon,
                "max_lat": result.max_lat,
                "center_lon": result.center_lon,
                "center_lat": result.center_lat
            }

            # Calculate approximate area
            # At 47.6°N latitude: 1° lat ≈ 111 km, 1° lon ≈ 75 km
            width_km = abs(bounds["max_lon"] - bounds["min_lon"]) * 75
            height_km = abs(bounds["max_lat"] - bounds["min_lat"]) * 111
            area_km2 = width_km * height_km

            # Calculate number of 9km grid cells needed
            # Use ceiling division to ensure full coverage
            import math
            grid_width = math.ceil(width_km / 9)
            grid_height = math.ceil(height_km / 9)
            grid_cells = grid_width * grid_height

            print("Tree Data Extents:")
            print(f"  Latitude:  {bounds['min_lat']:.4f} to {bounds['max_lat']:.4f}")
            print(f"  Longitude: {bounds['min_lon']:.4f} to {bounds['max_lon']:.4f}")
            print(f"  Center:    {bounds['center_lat']:.4f}, {bounds['center_lon']:.4f}")
            print(f"\nApproximate Coverage:")
            print(f"  Width:  {width_km:.1f} km")
            print(f"  Height: {height_km:.1f} km")
            print(f"  Area:   {area_km2:.1f} km²")
            print(f"\nGrid Requirements (9km resolution):")
            print(f"  Grid dimensions: {grid_width} × {grid_height}")
            print(f"  Total cells: {grid_cells}")
            print(f"\nNote: Using {grid_cells} cells minimizes API calls while covering all tree data.")

            return bounds
        else:
            print("No trees found in database.")
            return None

    finally:
        db.close()

if __name__ == "__main__":
    query_tree_extents()
