from fastapi import APIRouter, Response, HTTPException
from .database import SessionLocal, WeatherGridCell
from .phenology.compute import get_default_species_mapping, compute_atlas_for_grid
from datetime import datetime

router = APIRouter()

@router.get("/api/phenology/atlas.png")
def get_phenology_atlas(grid_cell_id: int = None, year: int = 2024):
    """
    Returns the phenology texture atlas for a specific grid cell.
    Width = 365 days, Height = N species (ordered by species_mapping).
    If grid_cell_id not provided, use default/central cell.
    """
    db = SessionLocal()
    try:
        # 1. Get grid cell
        if grid_cell_id:
            grid_cell = db.query(WeatherGridCell).filter_by(id=grid_cell_id).first()
        else:
            # Get default cell (center of region or most common)
            # For Seattle, we can pick one with trees
            grid_cell = db.query(WeatherGridCell).first()

        if not grid_cell:
            raise HTTPException(status_code=404, detail="Grid cell not found")

        # 2. Check if atlas exists and is current
        if grid_cell.phenology_atlas and grid_cell.phenology_year == year:
            # Return cached atlas
            return Response(content=grid_cell.phenology_atlas, media_type="image/png")

        # 3. Compute atlas if missing (fallback)
        # Note: This might be slow for a web request, ideally pre-computed
        print(f"Cache miss for grid {grid_cell.id} year {year}. Computing on-the-fly...")
        try:
            atlas_png = compute_atlas_for_grid(grid_cell, year, db)

            # Cache in database
            grid_cell.phenology_atlas = atlas_png
            grid_cell.phenology_year = year
            grid_cell.species_mapping = get_default_species_mapping()
            grid_cell.atlas_computed_at = datetime.utcnow()
            db.commit()

            return Response(content=atlas_png, media_type="image/png")
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            print(f"Error computing atlas: {e}")
            raise HTTPException(status_code=500, detail="Error generating atlas")

    finally:
        db.close()

@router.get("/api/phenology/atlas/mapping")
def get_atlas_mapping(grid_cell_id: int = None):
    """
    Returns the species-to-row mapping for the atlas.
    Frontend uses this to know which row corresponds to which species.
    Returns: {"ACPL": 0, "ACRU": 1, ...}
    """
    db = SessionLocal()
    try:
        if grid_cell_id:
            grid_cell = db.query(WeatherGridCell).filter_by(id=grid_cell_id).first()
        else:
            grid_cell = db.query(WeatherGridCell).first()

        if not grid_cell or not grid_cell.species_mapping:
            # Return default mapping
            return get_default_species_mapping()

        return grid_cell.species_mapping

    finally:
        db.close()
