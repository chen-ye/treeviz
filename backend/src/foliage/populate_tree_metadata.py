"""Script to populate per-tree elevation and urban status metadata."""
from dotenv import load_dotenv
load_dotenv()

from .database import SessionLocal, Tree
from .fetchers import TiledElevationFetcher, OpenFreeMapLandUseFetcher
from sqlalchemy import text
import time
import argparse

def populate_tree_metadata_fast(overwrite: bool = False):
    """
    Fast batch population using tiled data sources.

    Performance: ~5-10 seconds for 2000 trees (vs 15+ minutes with individual API calls)
    """
    print("Populating per-tree metadata using tiled data sources...")
    if overwrite:
        print("Overwrite mode: existing elevation/is_urban values will be replaced.")

    db = SessionLocal()
    try:
        # Get all trees needing metadata
        if overwrite:
            stmt = text("""
                SELECT id, ST_X(geom) as lon, ST_Y(geom) as lat
                FROM trees
            """)
        else:
            stmt = text("""
                SELECT id, ST_X(geom) as lon, ST_Y(geom) as lat
                FROM trees
                WHERE elevation IS NULL OR is_urban IS NULL
            """)

        trees = db.execute(stmt).fetchall()
        total = len(trees)

        if total == 0:
            print("All trees already have metadata!")
            return

        print(f"Found {total} trees needing metadata.")
        print("Initializing tiled data fetchers...")

        # Initialize fetchers (these cache tiles). Use OpenFreeMap vector tiles for landuse.
        elev_fetcher = TiledElevationFetcher(zoom=14)  # ~30m resolution
        land_fetcher = OpenFreeMapLandUseFetcher(zoom=14)

        print("Fetching data...")
        # Prepare batch landuse lookup to reduce tile requests
        points = [(t.lat, t.lon) for t in trees]
        urban_results = land_fetcher.is_urban_batch(points)

        start_time = time.time()

        # Process all trees — use batch landuse results and per-tree elevation
        update_stmt = text("""
            UPDATE trees
            SET elevation = :elevation, is_urban = :is_urban
            WHERE id = :tree_id
        """)

        for i, tree in enumerate(trees):
            # Fetch elevation (tile-cached)
            elevation = elev_fetcher.get_elevation(tree.lat, tree.lon)
            is_urban = urban_results[i]

            # Update tree
            db.execute(update_stmt, {
                "elevation": elevation,
                "is_urban": is_urban,
                "tree_id": tree.id
            })

            # Progress update every 100 trees
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (total - i - 1) / rate if rate > 0 else 0
                print(f"  Processed {i+1}/{total} trees ({rate:.1f} trees/sec, ~{remaining:.0f}s remaining)")
                db.commit()  # Commit periodically

        db.commit()

        elapsed = time.time() - start_time
        print(f"\n✓ Successfully populated metadata for {total} trees in {elapsed:.1f} seconds!")
        print(f"  Average: {total/elapsed:.1f} trees/second")

        # Show tile cache stats
        print(f"\nTile cache stats:")
        print(f"  Elevation tiles cached: {len(elev_fetcher.tile_cache)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate per-tree elevation and urban metadata (fast tiled mode).")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing elevation/is_urban values for all trees")
    args = parser.parse_args()

    populate_tree_metadata_fast(overwrite=args.overwrite)
