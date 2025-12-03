import csv
import logging
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from .database import SpeciesRef, SessionLocal, engine, Base
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_usda_checklist(filepath: str, db: Session):
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for line in f)

    logger.info(f"Loading {total_lines} species from {filepath}...")

    count = 0
    batch_size = 5000
    batch = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader) # Skip header

        for row in reader:
            if len(row) < 5:
                continue

            symbol = row[0]
            synonym = row[1]
            scientific_name_raw = row[2] # Full name with Author
            common_name = row[3]
            family = row[4]

            # Simple scientific name for matching
            simple_scientific = " ".join(scientific_name_raw.split()[:2]).lower()

            # Use dictionary for bulk insert mappings
            species_dict = {
                "symbol": symbol,
                "synonym_symbol": synonym if synonym else None,
                "scientific_name": simple_scientific,
                "full_scientific_name": scientific_name_raw,
                "common_name": common_name,
                "family": family
            }
            batch.append(species_dict)

            if len(batch) >= batch_size:
                stmt = insert(SpeciesRef).values(batch)
                stmt = stmt.on_conflict_do_nothing(index_elements=['full_scientific_name'])
                db.execute(stmt)
                db.commit()
                batch = []
                count += batch_size
                logger.info(f"Processed {count} records...")

        if batch:
            stmt = insert(SpeciesRef).values(batch)
            stmt = stmt.on_conflict_do_nothing(index_elements=['full_scientific_name'])
            db.execute(stmt)
            db.commit()

    logger.info("USDA Checklist loaded successfully.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Check relative to CWD first, then try backend/data/
        path = "data/plantlst.txt"
        if not os.path.exists(path):
            path = "backend/data/plantlst.txt"

        load_usda_checklist(path, db)
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        db.close()
