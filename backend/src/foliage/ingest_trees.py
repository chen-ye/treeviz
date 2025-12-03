import requests
import json
import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Tree, SpeciesRef, SessionLocal, engine
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEATTLE_ARCGIS_URL = "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/Combined_Tree_Point/FeatureServer/0/query"

def clean_scientific_name(name):
    if not name:
        return None
    # Remove backticks, single quotes, double quotes
    name = name.replace('`', '').replace("'", "").replace('"', "")
    # Remove cv. or var. and cultivar names for now to find the base species
    # Example: "Fraxinus angustifolia Raywood" -> "Fraxinus angustifolia"
    # Or "Acer rubrum 'October Glory'" -> "Acer rubrum"

    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}".lower()
    return name.lower()

def resolve_usda_symbol(db: Session, scientific_name: str, common_name: str = None):
    # Try 1: Exact match on scientific name (first 2 words)
    cleaned = clean_scientific_name(scientific_name)
    if not cleaned:
        return None

    match = db.query(SpeciesRef).filter(SpeciesRef.scientific_name == cleaned).first()
    if match:
        return match.symbol

    # Try 2: Try finding by common name (fuzzy or direct) - SKIPPED for now to be deterministic

    return None

def ingest_seattle_data(db: Session, limit=2000):
    offset = 0
    total_inserted = 0

    while True:
        logger.info(f"Fetching batch offset={offset}, limit={limit}...")
        params = {
            "where": "1=1",
            "outFields": "*",
            "resultRecordCount": limit,
            "resultOffset": offset,
            "f": "json",
            "outSR": "4326"
        }

        try:
            response = requests.get(SEATTLE_ARCGIS_URL, params=params)
            if response.status_code != 200:
                logger.error(f"Failed to fetch: {response.text}")
                break

            data = response.json()
            features = data.get("features", [])

            if not features:
                logger.info("No more features found.")
                break

            batch = []
            for feat in features:
                attrs = feat["attributes"]
                geom = feat.get("geometry")

                if not geom or not attrs.get("GLOBALID"):
                    continue

                # Deduplicate check (basic)
                if db.query(Tree).filter(Tree.external_id == attrs["GLOBALID"]).first():
                    continue

                sci_name = attrs.get("SCIENTIFIC_NAME")
                common_name = attrs.get("COMMON_NAME")

                symbol = resolve_usda_symbol(db, sci_name, common_name)

                tree = Tree(
                    external_id=attrs["GLOBALID"],
                    source_dataset="Seattle",
                    original_scientific_name=sci_name,
                    original_common_name=common_name,
                    usda_symbol=symbol,
                    dbh=attrs.get("DBH"),
                    geom=from_shape(Point(geom["x"], geom["y"]), srid=4326)
                )
                batch.append(tree)

            if batch:
                db.add_all(batch)
                db.commit()
                total_inserted += len(batch)
                logger.info(f"Inserted {len(batch)} trees. Total: {total_inserted}")

            if len(features) < limit:
                break

            offset += limit

            # Safety break for this sandbox session to avoid filling disk or taking too long
            if total_inserted >= 2000:
                logger.info("Reached sandbox safety limit of 2k trees.")
                break

        except Exception as e:
            logger.error(f"Ingestion error: {e}")
            break

if __name__ == "__main__":
    db = SessionLocal()
    ingest_seattle_data(db)
    db.close()
