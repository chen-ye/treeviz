"""Verify the full phenology backend implementation."""
from src.foliage.database import SessionLocal, Tree, WeatherGridCell, WeatherData
from src.foliage.phenology.factory import get_model_for_species
from src.foliage.phenology.compute import compute_atlas_for_grid
from sqlalchemy import func

def verify():
    print("Verifying implementation...")
    db = SessionLocal()
    try:
        # 1. Check Grid Cells
        cell_count = db.query(WeatherGridCell).count()
        print(f"Grid Cells: {cell_count}")
        if cell_count == 0:
            print("FAIL: No grid cells found.")
            return

        # 2. Check Trees Assigned
        tree_count = db.query(Tree).count()
        assigned_count = db.query(Tree).filter(Tree.weather_grid_cell_id.isnot(None)).count()
        print(f"Trees: {tree_count}")
        print(f"Trees Assigned to Grid: {assigned_count}")
        if assigned_count == 0:
            print("FAIL: No trees assigned to grid cells.")
            return

        # 3. Check Weather Data
        weather_count = db.query(WeatherData).count()
        print(f"Weather Records: {weather_count}")
        if weather_count == 0:
            print("FAIL: No weather data found.")
            return

        # 4. Check Atlases
        atlas_count = db.query(WeatherGridCell).filter(WeatherGridCell.phenology_atlas.isnot(None)).count()
        print(f"Grid Cells with Atlases: {atlas_count}")
        if atlas_count == 0:
            print("FAIL: No atlases pre-computed.")
            return

        # 5. Test Model Factory
        print("\nTesting Model Factory:")
        for symbol in ["ACPL", "PSME", "UNKNOWN"]:
            model = get_model_for_species(symbol)
            print(f"  {symbol} -> {model.__name__}")

        print("\nVerification Successful!")

    except Exception as e:
        print(f"Verification Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify()
