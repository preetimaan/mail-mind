#!/usr/bin/env python3
"""
Migration script to add error_message column to analysis_runs table
"""
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/mailmind.db")

# Extract the database file path from SQLite URL
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not os.path.isabs(db_path):
        # Relative path, make it relative to this script
        db_path = os.path.join(os.path.dirname(__file__), db_path)
else:
    print(f"Unsupported database URL: {DATABASE_URL}")
    exit(1)

if not os.path.exists(db_path):
    print(f"Database file not found: {db_path}")
    exit(1)

print(f"Adding error_message column to analysis_runs table in {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(analysis_runs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'error_message' in columns:
        print("Column 'error_message' already exists. No migration needed.")
    else:
        # Add the column
        cursor.execute("ALTER TABLE analysis_runs ADD COLUMN error_message TEXT")
        conn.commit()
        print("Successfully added error_message column to analysis_runs table.")
    
    conn.close()
    print("Migration completed successfully!")
    
except Exception as e:
    print(f"Error during migration: {e}")
    exit(1)

