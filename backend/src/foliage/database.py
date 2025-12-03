from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Index, Date, Boolean, LargeBinary, DateTime, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from geoalchemy2 import Geometry
from datetime import datetime

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

    # Weather Grid Reference
    weather_grid_cell_id = Column(Integer, ForeignKey('weather_grid_cells.id'), nullable=True)

    # species = relationship("SpeciesRef")

class WeatherGridCell(Base):
    """Stores weather data and phenology atlas for a geographic grid cell."""
    __tablename__ = 'weather_grid_cells'

    id = Column(Integer, primary_key=True)
    # Grid cell center point (9km resolution)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    # Metadata
    elevation = Column(Float, nullable=True)
    is_urban = Column(Boolean, default=False)
    # Spatial index
    geom = Column(Geometry('POINT', srid=4326), nullable=False)

    # Phenology Texture Atlas (width=365 days, height=N species)
    # This stores a PNG bitmap with lossless compression
    # Each row represents one species (ordered by species_mapping JSON)
    # Each column represents one day of year (1-365)
    phenology_atlas = Column(LargeBinary, nullable=True)  # PNG bytes
    phenology_year = Column(Integer, nullable=True)  # Year of cached data

    # Species index mapping: {usda_symbol: row_index}
    # Used to look up which row in the atlas corresponds to each species
    species_mapping = Column(JSON, nullable=True)

    # Cache metadata
    atlas_computed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_weather_grid_geom', 'geom', postgresql_using='gist'),
    )

class WeatherData(Base):
    """Daily weather measurements for a grid cell."""
    __tablename__ = 'weather_data'

    id = Column(Integer, primary_key=True)
    grid_cell_id = Column(Integer, ForeignKey('weather_grid_cells.id'), nullable=False)
    date = Column(Date, nullable=False, index=True)

    # Weather variables from OpenMeteo
    max_temp = Column(Float)  # °C
    min_temp = Column(Float)  # °C
    sunshine_duration = Column(Float)  # seconds
    precipitation_sum = Column(Float)  # mm
    soil_moisture = Column(Float)  # m³/m³

    # Computed phenology variables (pre-computed for efficiency)
    day_length = Column(Float)  # hours
    accumulated_gdd = Column(Float)  # Growing degree days
    accumulated_chill = Column(Float)  # Chill units

    __table_args__ = (
        Index('idx_weather_grid_date', 'grid_cell_id', 'date'),
    )

# Database Connection
import os

DB_USER = os.getenv("PGUSER", "postgres")
DB_PASSWORD = os.getenv("PGPASSWORD", "postgres")
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5432")
DB_NAME = os.getenv("PGDATABASE", "foliage_db")
DB_SSLMODE = os.getenv("PGSSLMODE", "prefer")

print(DB_HOST)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSLMODE}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
