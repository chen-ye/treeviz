"""Compute phenology atlases."""
import pandas as pd
import numpy as np
from io import BytesIO
from PIL import Image
from sqlalchemy.orm import Session
from ..database import WeatherGridCell, WeatherData
from .factory import get_model_for_species

# Top 50 species list (consistent order for atlas rows)
# This should match the frontend's expected mapping
TOP_50_SPECIES = [
    "ACPL", "ACRU", "LIST2", "QURU", "PSME", "PRCE",
    # New Batch
    "CRLA80", "PYCA80", "BEPE3", "ACPA2", "TICO2",
    "PRSE3", "GLTR", "CABE8", "COFL2", "FRLA",
    # Add more as needed
]

def get_default_species_mapping():
    """Return the standard {symbol: row_index} mapping."""
    return {symbol: i for i, symbol in enumerate(TOP_50_SPECIES)}

def compute_atlas_for_grid(grid_cell: WeatherGridCell, year: int, db: Session) -> bytes:
    """
    Generate a PNG texture atlas for the grid cell and year.
    Returns PNG bytes.
    """
    # 1. Fetch Weather Data
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    weather_records = db.query(WeatherData).filter(
        WeatherData.grid_cell_id == grid_cell.id,
        WeatherData.date >= start_date,
        WeatherData.date <= end_date
    ).order_by(WeatherData.date).all()

    if not weather_records:
        raise ValueError(f"No weather data found for grid {grid_cell.id} year {year}")

    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'date': w.date,
            'max_temp': w.max_temp,
            'min_temp': w.min_temp,
            'day_length': w.day_length,
            'accumulated_gdd': w.accumulated_gdd,
            'accumulated_chill': w.accumulated_chill,
            'soil_moisture': w.soil_moisture,
            # Add other fields if needed by models
        }
        for w in weather_records
    ])

    # 2. Compute Timelines
    atlas_data = []
    mapping = get_default_species_mapping()

    # Sort by index to ensure correct row order
    sorted_species = sorted(mapping.keys(), key=lambda k: mapping[k])

    for symbol in sorted_species:
        model_cls = get_model_for_species(symbol)
        model = model_cls(df, grid_cell.lat, grid_cell.lon, grid_cell.is_urban, grid_cell.elevation or 0.0)

        timeline = model.get_timeline()

        # Ensure we have 365 (or 366) days
        # If missing days, pad with last color or default
        if not timeline:
            timeline = [(0, 0, 0)] * len(df) # Black if failed

        atlas_data.extend(timeline)

    # 3. Create Image
    width = len(df) # 365 or 366
    height = len(sorted_species)

    # Flatten data: [(r,g,b), ...] -> [r,g,b, r,g,b, ...]
    flat_data = [c for rgb in atlas_data for c in rgb]

    # Create Pillow Image
    img = Image.frombytes('RGB', (width, height), bytes(flat_data))

    # Save to bytes
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()
