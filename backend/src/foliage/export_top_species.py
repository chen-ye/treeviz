import json
import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import func
from .database import Tree, SessionLocal, SpeciesRef

def export_top_species(output_file="top_50_species.json"):
    db = SessionLocal()
    try:
        # Query top 50 species by count
        results = db.query(
            Tree.usda_symbol,
            func.count(Tree.id).label('count')
        ).group_by(Tree.usda_symbol).order_by(func.count(Tree.id).desc()).limit(50).all()

        output_data = []
        for i, (symbol, count) in enumerate(results):
            ref_name = "N/A"
            common_name = "N/A"

            if symbol:
                ref = db.query(SpeciesRef).filter(SpeciesRef.symbol == symbol).first()
                if ref:
                    ref_name = ref.scientific_name
                    common_name = ref.common_name

            output_data.append({
                "rank": i + 1,
                "symbol": symbol,
                "count": count,
                "scientific_name": ref_name,
                "common_name": common_name
            })

        # Write to JSON file
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Successfully exported top 50 species to {output_file}")

    finally:
        db.close()

if __name__ == "__main__":
    export_top_species()
