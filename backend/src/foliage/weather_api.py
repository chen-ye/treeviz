"""API endpoints for weather grid management."""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func
from .database import SessionLocal, WeatherGridCell, WeatherData
from .weather_grid import get_grid_cell_for_point

router = APIRouter()

@router.get("/api/weather/grid")
def list_grid_cells():
    """List all weather grid cells with metadata."""
    db = SessionLocal()
    try:
        cells = db.query(WeatherGridCell).all()
        return [
            {
                "id": c.id,
                "lat": c.lat,
                "lon": c.lon,
                "elevation": c.elevation,
                "is_urban": c.is_urban,
                "has_atlas": c.phenology_atlas is not None,
                "atlas_year": c.phenology_year
            }
            for c in cells
        ]
    finally:
        db.close()

@router.get("/api/weather/grid/{cell_id}/status")
def get_grid_cell_status(cell_id: int):
    """Check data availability for a specific grid cell."""
    db = SessionLocal()
    try:
        cell = db.query(WeatherGridCell).filter_by(id=cell_id).first()
        if not cell:
            raise HTTPException(status_code=404, detail="Grid cell not found")

        # Count weather records
        weather_count = db.query(func.count(WeatherData.id)).filter_by(grid_cell_id=cell_id).scalar()

        # Get date range
        min_date = db.query(func.min(WeatherData.date)).filter_by(grid_cell_id=cell_id).scalar()
        max_date = db.query(func.max(WeatherData.date)).filter_by(grid_cell_id=cell_id).scalar()

        return {
            "id": cell.id,
            "weather_records": weather_count,
            "date_range": {
                "start": min_date,
                "end": max_date
            },
            "has_atlas": cell.phenology_atlas is not None,
            "atlas_computed_at": cell.atlas_computed_at
        }
    finally:
        db.close()

@router.get("/api/weather/grid/nearest")
def find_nearest_grid_cell(lat: float = Query(...), lon: float = Query(...)):
    """Find the nearest grid cell to the given coordinates."""
    result = get_grid_cell_for_point(lat, lon)
    if not result:
        raise HTTPException(status_code=404, detail="No grid cell found nearby")
    return result
