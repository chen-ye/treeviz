from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from geoalchemy2 import Geometry

Base = declarative_base()

class SpeciesRef(Base):
    __tablename__ = 'species_ref'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    synonym_symbol = Column(String, nullable=True)
    scientific_name = Column(String, nullable=False, index=True) # Normalized (lowercase, no author)
    full_scientific_name = Column(String, nullable=False, unique=True) # Full from USDA (with Author)
    common_name = Column(String, nullable=True)
    family = Column(String, nullable=True)

class Tree(Base):
    __tablename__ = 'trees'

    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True) # e.g. OBJECTID or UnitID
    source_dataset = Column(String, nullable=False) # e.g. "Seattle"

    # Normalized Species Reference
    usda_symbol = Column(String, nullable=True, index=True)

    # Original Data (for debugging/fallback)
    original_scientific_name = Column(String, nullable=True)
    original_common_name = Column(String, nullable=True)

    # Attributes
    dbh = Column(Float, nullable=True) # Diameter at Breast Height

    # Geometry (Point)
    geom = Column(Geometry('POINT', srid=4326))

    # species = relationship("SpeciesRef")

# Database Connection
import os

DB_USER = os.getenv("PGUSER", "postgres")
DB_PASSWORD = os.getenv("PGPASSWORD", "postgres")
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5432")
DB_NAME = os.getenv("PGDATABASE", "foliage_db")
DB_SSLMODE = os.getenv("PGSSLMODE", "prefer")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSLMODE}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
