"""Migration script to update database schema."""
from sqlalchemy import text
from .database import engine

def migrate_schema():
    print("Running schema migration...")
    with engine.connect() as conn:
        try:
            # Add weather_grid_cell_id to trees table
            print("Adding weather_grid_cell_id column to trees table...")
            conn.execute(text("""
                ALTER TABLE trees
                ADD COLUMN IF NOT EXISTS weather_grid_cell_id INTEGER
                REFERENCES weather_grid_cells(id);
            """))

            # Create index for the new column
            print("Creating index for weather_grid_cell_id...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_trees_weather_grid_cell_id
                ON trees(weather_grid_cell_id);
            """))

            conn.commit()
            print("Migration successful!")

        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate_schema()
