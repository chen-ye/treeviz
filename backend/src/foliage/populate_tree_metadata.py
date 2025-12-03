"""Script to populate per-tree elevation and urban status metadata."""
from dotenv import load_dotenv
load_dotenv()

from .database import SessionLocal, Tree
from .fetchers import ElevationFetcher, LandUseFetcher
from sqlalchemy import text
import time

def populate_tree_metadata(batch_size: int = 100):
    """Fetch and store elevation and urban status for each tree."""
    print("Populating per-tree metadata...")

    db = SessionLocal()
    try:
        # Count trees needing metadata
        result = db.execute(text("""
            SELECT COUNT(*)
            FROM trees
            WHERE elevation IS NULL OR is_urban IS NULL
        """)).scalar()

        print(f"Found {result} trees needing metadata.")

        if result == 0:
            print("All trees already have metadata!")
            return

        # Initialize fetchers
        elev_fetcher = ElevationFetcher()
        land_fetcher = LandUseFetcher()

        # Fetch trees in batches
        offset = 0
        processed = 0

        while True:
            # Get batch of trees
            stmt = text("""
                SELECT id, ST_X(geom) as lon, ST_Y(geom) as lat
                FROM trees
                WHERE elevation IS NULL OR is_urban IS NULL
                LIMIT :batch_size OFFSET :offset
            """)

            trees = db.execute(stmt, {"batch_size": batch_size, "offset": offset}).fetchall()

            if not trees:
                break

            print(f"Processing batch {offset//batch_size + 1} ({len(trees)} trees)...")

            for tree in trees:
                # Fetch metadata
                elevation = elev_fetcher.get_elevation(tree.lat, tree.lon)
                is_urban = land_fetcher.is_urban_environment(tree.lat, tree.lon)

                # Update tree
                update_stmt = text("""
                    UPDATE trees
                    SET elevation = :elevation, is_urban = :is_urban
                    WHERE id = :tree_id
                """)

                db.execute(update_stmt, {
                    "elevation": elevation,
                    "is_urban": is_urban,
                    "tree_id": tree.id
                })

                processed += 1

                # Rate limit (be nice to APIs)
                time.sleep(0.1)

                if processed % 50 == 0:
                    print(f"  Processed {processed}/{result} trees...")
                    db.commit()  # Commit periodically

            db.commit()
            offset += batch_size

        print(f"✓ Successfully populated metadata for {processed} trees!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_tree_metadata()
