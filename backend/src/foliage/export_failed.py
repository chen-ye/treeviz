import json
from sqlalchemy import func
from .database import Tree, SessionLocal

def export_failed_matches():
    db = SessionLocal()
    try:
        results = db.query(
            Tree.original_scientific_name,
            func.count(Tree.id).label('count')
        ).filter(Tree.usda_symbol.is_(None)).group_by(Tree.original_scientific_name).order_by(func.count(Tree.id).desc()).all()

        failed = [
            {"name": name, "count": count}
            for name, count in results
        ]

        path = "failed_matches.json"
        with open(path, "w") as f:
            json.dump(failed, f, indent=2)

        print(f"Exported {len(failed)} failed species to {path}")

    finally:
        db.close()

if __name__ == "__main__":
    export_failed_matches()
