"""Fetch weather data for all grid cells for a specific year."""
import argparse
import time
from dotenv import load_dotenv
load_dotenv()

from .database import SessionLocal, WeatherGridCell
from .weather_fetch import WeatherFetcher, compute_phenology_variables, store_weather_data

def fetch_weather_year(year: int):
    print(f"Fetching weather data for year {year}...")

    db = SessionLocal()
    try:
        cells = db.query(WeatherGridCell).all()
        print(f"Found {len(cells)} grid cells.")

        fetcher = WeatherFetcher()

        for i, cell in enumerate(cells):
            print(f"Processing cell {i+1}/{len(cells)} (ID: {cell.id})...")

            # 1. Fetch
            df = fetcher.fetch_year(cell.lat, cell.lon, year)

            if df.empty:
                print(f"  Warning: No data found for cell {cell.id}")
                continue

            # 2. Compute
            print(f"  Computing phenology variables (Urban: {cell.is_urban})...")
            df_processed = compute_phenology_variables(df, cell.lat, cell.lon, is_urban=cell.is_urban)

            # 3. Store
            print(f"  Storing {len(df_processed)} daily records...")
            store_weather_data(db, cell, df_processed)

            # Sleep to respect API limits
            time.sleep(1.0)

        print("Weather data fetch complete!")

    except Exception as e:
        print(f"Error fetching weather: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch weather data for a specific year")
    parser.add_argument("--year", type=int, default=2024, help="Year to fetch (default: 2024)")
    args = parser.parse_args()

    fetch_weather_year(args.year)
