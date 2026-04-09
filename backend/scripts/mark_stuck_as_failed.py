#!/usr/bin/env python3
"""
Script to mark stuck analysis runs as failed (non-interactive)
"""
from datetime import datetime
from app.database import SessionLocal, AnalysisRun, User

def mark_stuck_as_failed(username=None, account_id=None):
    """Mark all runs stuck in processing as failed"""
    db = SessionLocal()
    try:
        query = db.query(AnalysisRun).filter(AnalysisRun.status == "processing")
        
        if username:
            user = db.query(User).filter(User.username == username).first()
            if user:
                query = query.filter(AnalysisRun.user_id == user.id)
            else:
                print(f"User '{username}' not found.")
                return
        
        if account_id:
            query = query.filter(AnalysisRun.account_id == account_id)
        
        stuck_runs = query.all()
        
        if not stuck_runs:
            print("No stuck runs found.")
            return
        
        print(f"Found {len(stuck_runs)} stuck run(s):")
        for run in stuck_runs:
            age = datetime.utcnow() - run.created_at
            print(f"  - Run ID {run.id}: Created {age.total_seconds()/60:.1f} minutes ago")
        
        # Mark as failed
        for run in stuck_runs:
            run.status = "failed"
            run.completed_at = datetime.utcnow()
            if hasattr(run, 'error_message'):
                run.error_message = "Analysis run was stuck in processing status and has been marked as failed."
        
        db.commit()
        print(f"✅ Marked {len(stuck_runs)} run(s) as failed.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else None
    account_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    mark_stuck_as_failed(username, account_id)

