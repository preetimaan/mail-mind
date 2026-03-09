"""
Migration: Add chunk tracking columns to analysis_runs table

This migration adds current_chunk and total_chunks columns to support
chunked processing of large date ranges.

Run with: python migrations/add_chunk_tracking.py
"""

from app.database import SessionLocal, engine
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # Check if columns already exist
        result = db.execute(text("PRAGMA table_info(analysis_runs)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'current_chunk' not in columns:
            print("Adding current_chunk column...")
            db.execute(text("ALTER TABLE analysis_runs ADD COLUMN current_chunk INTEGER"))
            print("✓ Added current_chunk column")
        else:
            print("✓ current_chunk column already exists")
        
        if 'total_chunks' not in columns:
            print("Adding total_chunks column...")
            db.execute(text("ALTER TABLE analysis_runs ADD COLUMN total_chunks INTEGER"))
            print("✓ Added total_chunks column")
        else:
            print("✓ total_chunks column already exists")
        
        db.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Running migration: add_chunk_tracking")
    print("=" * 50)
    migrate()
