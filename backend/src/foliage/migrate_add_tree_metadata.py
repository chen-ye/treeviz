"""Migration script to add per-tree metadata columns."""
from sqlalchemy import text
from .database import engine

def migrate_add_tree_metadata():
    print("Running schema migration: adding per-tree metadata...")
    with engine.connect() as conn:
        try:
            # Add elevation column
            print("Adding elevation column to trees table...")
            conn.execute(text("""
                ALTER TABLE trees
                ADD COLUMN IF NOT EXISTS elevation FLOAT;
            """))

            # Add is_urban column
            print("Adding is_urban column to trees table...")
            conn.execute(text("""
                ALTER TABLE trees
                ADD COLUMN IF NOT EXISTS is_urban BOOLEAN;
            """))

            conn.commit()
            print("Migration successful!")

        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate_add_tree_metadata()
