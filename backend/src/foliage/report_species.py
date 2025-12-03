from sqlalchemy import func
from .database import Tree, SessionLocal, SpeciesRef

def report_top_species():
    db = SessionLocal()
    try:
        results = db.query(
            Tree.usda_symbol,
            func.count(Tree.id).label('count')
        ).group_by(Tree.usda_symbol).order_by(func.count(Tree.id).desc()).limit(20).all()

        print(f"{'USDA Symbol':<12} | {'Count':<8} | {'Scientific Name (Ref)'}")
        print("-" * 50)

        for symbol, count in results:
            ref_name = "N/A"
            if symbol:
                ref = db.query(SpeciesRef).filter(SpeciesRef.symbol == symbol).first()
                if ref:
                    ref_name = ref.scientific_name

            print(f"{str(symbol):<12} | {count:<8} | {ref_name}")

    finally:
        db.close()

if __name__ == "__main__":
    report_top_species()
