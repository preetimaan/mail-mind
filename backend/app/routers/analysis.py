from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json

from app.database import get_db, User, EmailAccount, AnalysisRun, EmailMetadata, AnalysisResult
from app.encryption import EncryptionManager
from app.email_connectors import GmailConnector, YahooConnector
from app.nlp_analyzer import NLPAnalyzer
from app.date_tracker import DateTracker
from app.services.analysis_service import AnalysisService

router = APIRouter()

class AnalysisRequest(BaseModel):
    username: str
    account_id: int
    start_date: datetime
    end_date: datetime

class AnalysisResponse(BaseModel):
    run_id: int
    status: str
    message: str

@router.post("/batch", response_model=AnalysisResponse)
async def start_batch_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start batch analysis for a date range"""
    # Verify user and account
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = db.query(EmailAccount).filter(
        EmailAccount.id == request.account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Create analysis run
    analysis_run = AnalysisRun(
        user_id=user.id,
        account_id=account.id,
        start_date=request.start_date,
        end_date=request.end_date,
        status="pending"
    )
    db.add(analysis_run)
    db.commit()
    db.refresh(analysis_run)
    
    # Start background analysis
    background_tasks.add_task(
        process_batch_analysis,
        analysis_run.id,
        user.id,
        account.id,
        request.start_date,
        request.end_date
    )
    
    return AnalysisResponse(
        run_id=analysis_run.id,
        status="pending",
        message="Analysis started in background"
    )

async def process_batch_analysis(
    run_id: int,
    user_id: int,
    account_id: int,
    start_date: datetime,
    end_date: datetime
):
    """Background task to process batch analysis"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Update status
        analysis_run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not analysis_run:
            return
        
        analysis_run.status = "processing"
        db.commit()
        
        # Get account
        account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not account:
            analysis_run.status = "failed"
            db.commit()
            return
        
        # Decrypt credentials
        enc_manager = EncryptionManager(user_id)
        credentials_json = enc_manager.decrypt(account.encrypted_credentials)
        
        # Initialize connector
        try:
            if account.provider == 'gmail':
                connector = GmailConnector(credentials_json)
            elif account.provider == 'yahoo':
                creds = json.loads(credentials_json)
                connector = YahooConnector(creds['email'], creds['password'])
            else:
                analysis_run.status = "failed"
                db.commit()
                return
        except ValueError as e:
            # Token expired/revoked error from GmailConnector
            error_msg = str(e)
            if 'expired or revoked' in error_msg or 'invalid_grant' in error_msg:
                # Mark account as inactive
                account.is_active = False
                analysis_run.status = "failed"
                db.commit()
                print(f"Account {account.email} marked as inactive due to expired/revoked token")
                return
            raise
        
        # Use analysis service
        service = AnalysisService(db, user_id, account_id)
        result = service.analyze_date_range(
            connector,
            start_date,
            end_date,
            run_id=analysis_run.id
        )
        
        # Update analysis run - refresh to get latest state
        db.refresh(analysis_run)
        analysis_run.status = "completed"
        analysis_run.emails_processed = result['emails_processed']
        analysis_run.completed_at = datetime.utcnow()
        db.commit()
        
    except ValueError as e:
        # Handle token expiration/revocation errors
        error_msg = str(e)
        if 'expired or revoked' in error_msg or 'invalid_grant' in error_msg:
            try:
                account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
                if account:
                    account.is_active = False
                analysis_run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
                if analysis_run:
                    analysis_run.status = "failed"
                    analysis_run.completed_at = datetime.utcnow()
                db.commit()
                print(f"Account {account.email if account else 'unknown'} marked as inactive due to expired/revoked token")
            except Exception as update_error:
                print(f"Failed to update account/run status: {update_error}")
                db.rollback()
        else:
            # Re-raise if it's a different ValueError
            raise
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        # Rollback any pending transaction
        try:
            db.rollback()
        except:
            pass  # Ignore rollback errors
        
        # Get analysis run and mark as failed
        try:
            # Refresh the session to get a clean state
            analysis_run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
            if analysis_run:
                analysis_run.status = "failed"
                analysis_run.completed_at = datetime.utcnow()
                db.commit()
        except Exception as update_error:
            print(f"Failed to update analysis run status: {update_error}")
            db.rollback()
    finally:
        try:
            db.close()
        except:
            pass

@router.get("/runs/{run_id}")
async def get_analysis_run(
    run_id: int,
    username: str,
    db: Session = Depends(get_db)
):
    """Get analysis run status"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    analysis_run = db.query(AnalysisRun).filter(
        AnalysisRun.id == run_id,
        AnalysisRun.user_id == user.id
    ).first()
    
    if not analysis_run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    
    return {
        "id": analysis_run.id,
        "status": analysis_run.status,
        "emails_processed": analysis_run.emails_processed,
        "start_date": analysis_run.start_date.isoformat(),
        "end_date": analysis_run.end_date.isoformat(),
        "created_at": analysis_run.created_at.isoformat(),
        "completed_at": analysis_run.completed_at.isoformat() if analysis_run.completed_at else None
    }

@router.get("/runs")
async def list_analysis_runs(
    username: str,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List analysis runs for a user"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return []
    
    query = db.query(AnalysisRun).filter(AnalysisRun.user_id == user.id)
    if account_id:
        query = query.filter(AnalysisRun.account_id == account_id)
    
    runs = query.order_by(AnalysisRun.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": run.id,
            "account_id": run.account_id,
            "status": run.status,
            "emails_processed": run.emails_processed,
            "start_date": run.start_date.isoformat(),
            "end_date": run.end_date.isoformat(),
            "created_at": run.created_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None
        }
        for run in runs
    ]

