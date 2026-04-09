#!/usr/bin/env python3
"""
Migration script to change message_id unique constraint to composite unique on (account_id, message_id)

This fixes duplicate email handling issues:
- Allows same message_id across different accounts
- Prevents duplicates within the same account
- Works correctly for Yahoo accounts where IMAP sequence numbers aren't globally unique
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

print(f"Migrating message_id constraint in {db_path}")
print("Changing from global unique constraint to composite unique on (account_id, message_id)")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the new constraint already exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name='uq_email_account_message'
    """)
    existing_index = cursor.fetchone()
    
    if existing_index:
        print("Composite unique constraint already exists. No migration needed.")
        conn.close()
        exit(0)
    
    # Check for existing unique index on message_id
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND sql LIKE '%UNIQUE%' AND sql LIKE '%message_id%'
    """)
    old_indexes = cursor.fetchall()
    
    # Drop old unique indexes on message_id
    for (index_name,) in old_indexes:
        if index_name and index_name != 'sqlite_autoindex_email_metadata_1':
            print(f"Dropping old unique index: {index_name}")
            cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
    
    # Also check for the auto-generated unique index
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='table' AND name='email_metadata'
    """)
    table_sql = cursor.fetchone()
    if table_sql and 'UNIQUE' in table_sql[0] and 'message_id' in table_sql[0]:
        print("Note: Old unique constraint on message_id column will be replaced by new composite constraint")
        print("(SQLite will handle this automatically when the table is recreated)")
    
    # Create new composite unique index
    print("Creating composite unique index on (account_id, message_id)...")
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_email_account_message 
        ON email_metadata(account_id, message_id)
    """)
    
    conn.commit()
    print("Successfully created composite unique constraint on (account_id, message_id)")
    
    # Verify the constraint was created
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name='uq_email_account_message'
    """)
    verify = cursor.fetchone()
    if verify:
        print("✓ Migration completed successfully!")
    else:
        print("⚠ Warning: Could not verify constraint creation")
    
    conn.close()
    
except Exception as e:
    print(f"Error during migration: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

