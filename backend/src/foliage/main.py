from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json

from .database import SessionLocal, Tree, SpeciesRef
from .weather_api import router as weather_router
from .phenology_api import router as phenology_router
from .phenology.compute import get_default_species_mapping

app = FastAPI()

app.include_router(phenology_router)
app.include_router(weather_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/metadata")
def get_metadata():
    """Returns species configuration."""
    return {
        "atlas_mapping": get_default_species_mapping(),
        "year": 2024,
    }

@app.get("/api/trees")
def get_trees(
    db: Session = Depends(get_db),
    min_lat: float = Query(None),
    max_lat: float = Query(None),
    min_lon: float = Query(None),
    max_lon: float = Query(None),
    limit: int = 10000
):
    """
    Returns trees with phenology adjustment metadata.
    """
    from sqlalchemy import text
    from .phenology.adjustments import calculate_adjustment_days

    stmt = text("""
        SELECT
            t.id,
            ST_X(t.geom) as lon,
            ST_Y(t.geom) as lat,
            t.usda_symbol,
            t.original_common_name,
            t.weather_grid_cell_id,
            t.elevation as tree_elevation,
            t.is_urban as tree_is_urban,
            g.elevation as grid_elevation,
            g.is_urban as grid_is_urban
        FROM trees t
        LEFT JOIN weather_grid_cells g ON t.weather_grid_cell_id = g.id
        LIMIT :limit
    """)

    results = db.execute(stmt, {"limit": limit}).fetchall()

    data = []
    for row in results:
        # Calculate adjustment days for this tree
        adjustment_days = 0
        if row.usda_symbol:
            adjustment_days = calculate_adjustment_days(
                species_symbol=row.usda_symbol,
                tree_elevation=row.tree_elevation,
                tree_is_urban=row.tree_is_urban,
                grid_elevation=row.grid_elevation,
                grid_is_urban=row.grid_is_urban
            )

        data.append({
            "id": row.id,
            "position": [row.lon, row.lat],
            "species": row.usda_symbol,
            "name": row.original_common_name,
            "grid_cell_id": row.weather_grid_cell_id,
            "elevation": row.tree_elevation,
            "is_urban": row.tree_is_urban,
            "adjustment_days": adjustment_days  # Frontend can use this to shift timeline
        })

    return data
