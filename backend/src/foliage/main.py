from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json

from .database import SessionLocal, Tree, SpeciesRef
from .phenology import load_traits, get_color_for_tree
from .weather import weather_service
from .phenology_api import router as phenology_router, get_atlas_mapping

app = FastAPI()

app.include_router(phenology_router)

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
    """Returns species traits and configuration."""
    return {
        "species_traits": load_traits(),
        "atlas_mapping": get_atlas_mapping(),
        "year": 2024,
        # In real app, weather history would go here
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
    Returns trees. Optionally filtered by bounding box.
    Returns GeoJSON-like structure or efficient binary format?
    For Deck.gl, JSON array of objects is fine for <100k points.
    """
    query = db.query(Tree)

    if min_lat and max_lat and min_lon and max_lon:
        # Simple bounding box on Lat/Lon columns if we had them indexed separate from Geom.
        # But we have PostGIS `geom`.
        # Using geoalchemy2 functions is better, but for speed in prototype,
        # let's assume we fetch all or limit.
        pass

    trees = query.limit(limit).all()

    # Format for Deck.gl (ScatterplotLayer)
    # [position, color, radius, ...]

    result = []
    for t in trees:
        # Get coordinates from WKBElement?
        # GeoAlchemy2 shapes needs parsing.
        # Efficient way: Use ST_AsGeoJSON in query, or Shapely.
        from shapely import wkb
        import binascii

        # t.geom is WKBElement
        # We can use shapely.wkb.loads(bytes(t.geom.data))
        # But `t.geom` might already be castable.

        # Faster: Use ST_X, ST_Y in select.
        pass

    # Optimized Query
    from sqlalchemy import text
    stmt = text("""
        SELECT
            id,
            ST_X(geom) as lon,
            ST_Y(geom) as lat,
            usda_symbol,
            original_common_name
        FROM trees
        LIMIT :limit
    """)

    results = db.execute(stmt, {"limit": limit}).fetchall()

    data = []
    for row in results:
        data.append({
            "id": row.id,
            "position": [row.lon, row.lat],
            "species": row.usda_symbol,
            "name": row.original_common_name
        })

    return data

@app.get("/api/weather_factor")
def get_weather_factor(doy: int, year: int = 2024):
    return {"factor": weather_service.calculate_weather_factor(year, doy)}
