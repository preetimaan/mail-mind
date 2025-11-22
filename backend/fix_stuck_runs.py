#!/usr/bin/env python3
"""
Script to fix analysis runs stuck in 'processing' status.

Usage:
    python3 fix_stuck_runs.py [--username USERNAME] [--account-id ACCOUNT_ID]
"""

import sys
import argparse
from datetime import datetime, timedelta
from app.database import SessionLocal, AnalysisRun

def fix_stuck_runs(username=None, account_id=None, older_than_minutes=5):
    """Mark runs stuck in processing as failed if they're older than threshold"""
    db = SessionLocal()
    try:
        query = db.query(AnalysisRun).filter(AnalysisRun.status == "processing")
        
        if username:
            from app.database import User
            user = db.query(User).filter(User.username == username).first()
            if user:
                query = query.filter(AnalysisRun.user_id == user.id)
        
        if account_id:
            query = query.filter(AnalysisRun.account_id == account_id)
        
        # Only fix runs older than threshold
        threshold = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        query = query.filter(AnalysisRun.created_at < threshold)
        
        stuck_runs = query.all()
        
        if not stuck_runs:
            print("No stuck runs found.")
            return
        
        print(f"Found {len(stuck_runs)} stuck run(s):")
        for run in stuck_runs:
            age = datetime.utcnow() - run.created_at
            print(f"  - Run ID {run.id}: Created {age.total_seconds()/60:.1f} minutes ago")
        
        response = input(f"\nMark {len(stuck_runs)} run(s) as 'failed'? (y/n): ")
        if response.lower() == 'y':
            for run in stuck_runs:
                run.status = "failed"
                run.completed_at = datetime.utcnow()
            db.commit()
            print(f"✅ Marked {len(stuck_runs)} run(s) as failed.")
        else:
            print("Cancelled.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description='Fix stuck analysis runs')
    parser.add_argument('--username', help='Filter by username')
    parser.add_argument('--account-id', type=int, help='Filter by account ID')
    parser.add_argument('--older-than', type=int, default=5, 
                       help='Only fix runs older than N minutes (default: 5)')
    
    args = parser.parse_args()
    fix_stuck_runs(args.username, args.account_id, args.older_than)

if __name__ == "__main__":
    main()

