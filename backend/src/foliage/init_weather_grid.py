"""Initialize the weather grid for the region."""
from dotenv import load_dotenv
load_dotenv()

from .database import SessionLocal, init_db, WeatherGridCell
from .weather_grid import create_grid_for_region, assign_trees_to_grid
from .fetchers import ElevationFetcher, LandUseFetcher
import time

def init_weather_grid():
    print("Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        # Check if grid already exists
        count = db.query(WeatherGridCell).count()
        if count > 0:
            print(f"Grid already initialized with {count} cells.")
            response = input("Do you want to recreate the grid? (y/N): ")
            if response.lower() != 'y':
                print("Skipping grid creation.")
                return

            print("Clearing existing grid...")
            db.query(WeatherGridCell).delete()
            db.commit()

        print("Generating grid cells...")
        cells = create_grid_for_region(grid_km=9.0)

        if not cells:
            print("No cells generated. Check tree data.")
            return

        print(f"Fetching metadata for {len(cells)} cells...")
        elev_fetcher = ElevationFetcher()
        land_fetcher = LandUseFetcher()

        for i, cell in enumerate(cells):
            print(f"Processing cell {i+1}/{len(cells)} at ({cell.lat:.4f}, {cell.lon:.4f})...")

            # Fetch metadata
            cell.elevation = elev_fetcher.get_elevation(cell.lat, cell.lon)
            cell.is_urban = land_fetcher.is_urban_environment(cell.lat, cell.lon)

            print(f"  Elevation: {cell.elevation}m, Urban: {cell.is_urban}")

            db.add(cell)
            # Sleep briefly to be nice to APIs
            time.sleep(0.5)

        db.commit()
        print("Grid cells saved to database.")

        print("Assigning trees to grid cells...")
        assign_trees_to_grid()

        print("Weather grid initialization complete!")

    except Exception as e:
        print(f"Error initializing grid: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_weather_grid()
