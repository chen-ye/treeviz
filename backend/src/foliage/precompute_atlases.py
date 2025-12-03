"""Pre-compute phenology atlases for all grid cells."""
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from .database import SessionLocal, WeatherGridCell
from .phenology.compute import compute_atlas_for_grid, get_default_species_mapping

def precompute_atlases(year: int):
    print(f"Pre-computing phenology atlases for year {year}...")

    db = SessionLocal()
    try:
        cells = db.query(WeatherGridCell).all()
        print(f"Found {len(cells)} grid cells.")

        mapping = get_default_species_mapping()

        for i, cell in enumerate(cells):
            print(f"Processing cell {i+1}/{len(cells)} (ID: {cell.id})...")

            try:
                # 1. Compute Atlas
                atlas_png = compute_atlas_for_grid(cell, year, db)

                # 2. Store in DB
                cell.phenology_atlas = atlas_png
                cell.phenology_year = year
                cell.species_mapping = mapping
                cell.atlas_computed_at = datetime.utcnow()

                db.commit()
                print(f"  Saved atlas ({len(atlas_png)} bytes)")

            except ValueError as e:
                print(f"  Skipping: {e}")
            except Exception as e:
                print(f"  Error: {e}")
                db.rollback()

        print("Atlas pre-computation complete!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-compute phenology atlases")
    parser.add_argument("--year", type=int, default=2024, help="Year to compute (default: 2024)")
    args = parser.parse_args()

    precompute_atlases(args.year)
