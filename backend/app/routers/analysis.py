from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
    force_reanalysis: Optional[bool] = False  # If True, re-analyze even if already processed

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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("BATCH ANALYSIS REQUEST RECEIVED")
    logger.info(f"Username: {request.username}")
    logger.info(f"Account ID: {request.account_id}")
    logger.info(f"Start Date: {request.start_date}")
    logger.info(f"End Date: {request.end_date}")
    logger.info(f"Force Reanalysis: {request.force_reanalysis}")
    logger.info("=" * 50)
    print("=" * 50)
    print("[PRINT] BATCH ANALYSIS REQUEST RECEIVED")
    print(f"[PRINT] Username: {request.username}, Account ID: {request.account_id}")
    print(f"[PRINT] Date range: {request.start_date} to {request.end_date}")
    print(f"[PRINT] Force Reanalysis: {request.force_reanalysis}")
    print("=" * 50)
    
    try:
        # Run database operations in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        
        def create_analysis_run_sync():
            # Verify user and account
            logger.info("Querying user...")
            print("[PRINT] Querying user...")
            user = db.query(User).filter(User.username == request.username).first()
            if not user:
                logger.warning(f"User not found: {request.username}")
                raise HTTPException(status_code=404, detail="User not found")
            logger.info(f"User found: {user.id}")
            print(f"[PRINT] User found: {user.id}")
            
            logger.info("Querying account...")
            print("[PRINT] Querying account...")
            account = db.query(EmailAccount).filter(
                EmailAccount.id == request.account_id,
                EmailAccount.user_id == user.id
            ).first()
            
            if not account:
                logger.warning(f"Account not found: {request.account_id}")
                raise HTTPException(status_code=404, detail="Account not found")
            logger.info(f"Account found: {account.id}")
            print(f"[PRINT] Account found: {account.id}")
            
            # Create analysis run
            logger.info("Creating analysis run...")
            print("[PRINT] Creating analysis run...")
            analysis_run = AnalysisRun(
                user_id=user.id,
                account_id=account.id,
                start_date=request.start_date,
                end_date=request.end_date,
                status="pending"
            )
            db.add(analysis_run)
            logger.info("Committing analysis run...")
            print("[PRINT] Committing analysis run...")
            db.commit()
            logger.info("Refreshing analysis run...")
            print("[PRINT] Refreshing analysis run...")
            db.refresh(analysis_run)
            logger.info(f"Analysis run created: {analysis_run.id}")
            print(f"[PRINT] Analysis run created: {analysis_run.id}")
            return analysis_run, user.id, account.id
        
        logger.info("Running database operations in thread pool...")
        print("[PRINT] Running database operations in thread pool...")
        analysis_run, user_id, account_id = await loop.run_in_executor(executor, create_analysis_run_sync)
        
        # Start background analysis (force_reanalysis deletion will happen in background task)
        logger.info(f"Adding background task for run_id={analysis_run.id}")
        print(f"[PRINT] Adding background task for run_id={analysis_run.id}")
        background_tasks.add_task(
            process_batch_analysis,
            analysis_run.id,
            user_id,
            account_id,
            request.start_date,
            request.end_date,
            request.force_reanalysis
        )
        logger.info(f"Background task added, returning response")
        print(f"[PRINT] Background task added, returning response")
        
        response = AnalysisResponse(
            run_id=analysis_run.id,
            status="pending",
            message="Analysis started in background"
        )
        logger.info(f"Returning response with run_id={response.run_id}")
        print(f"[PRINT] Returning response with run_id={response.run_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in start_batch_analysis: {e}", exc_info=True)
        print(f"[PRINT] ERROR in start_batch_analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

def process_batch_analysis(
    run_id: int,
    user_id: int,
    account_id: int,
    start_date: datetime,
    end_date: datetime,
    force_reanalysis: bool = False
):
    """Background task to process batch analysis (synchronous)"""
    import logging
    logger = logging.getLogger(__name__)
    
    from app.database import SessionLocal
    
    logger.info(f"Starting batch analysis: run_id={run_id}, account_id={account_id}, start={start_date}, end={end_date}")
    print(f"[PRINT] Starting batch analysis: run_id={run_id}, account_id={account_id}")
    db = SessionLocal()
    try:
        # Update status
        analysis_run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not analysis_run:
            return
        
        # Check if already cancelled
        if analysis_run.status == "cancelled":
            logger.info(f"Analysis run {run_id} was cancelled before processing started")
            print(f"[PRINT] Analysis run {run_id} was cancelled before processing started")
            return
        
        analysis_run.status = "processing"
        db.commit()
        
        # If force_reanalysis is True, remove processed date ranges for this range
        if force_reanalysis:
            logger.info(f"Force reanalysis requested - removing processed date ranges for {start_date} to {end_date}")
            print(f"[PRINT] Force reanalysis requested - removing processed date ranges for {start_date} to {end_date}")
            # Remove any processed ranges that overlap with the requested range
            from app.database import ProcessedDateRange
            overlapping_ranges = db.query(ProcessedDateRange).filter(
                ProcessedDateRange.account_id == account_id,
                ProcessedDateRange.start_date < end_date,
                ProcessedDateRange.end_date > start_date
            ).all()
            
            if overlapping_ranges:
                logger.info(f"Found {len(overlapping_ranges)} processed date ranges to remove for re-analysis:")
                print(f"[PRINT] Found {len(overlapping_ranges)} processed date ranges to remove:")
                for range_obj in overlapping_ranges:
                    logger.info(f"  - Removing range: {range_obj.start_date} to {range_obj.end_date} ({range_obj.emails_count} emails)")
                    print(f"[PRINT]   Removing range: {range_obj.start_date} to {range_obj.end_date} ({range_obj.emails_count} emails)")
                    db.delete(range_obj)
                db.commit()
                logger.info(f"Successfully removed {len(overlapping_ranges)} processed date ranges - will re-fetch and re-analyze")
                print(f"[PRINT] Successfully removed {len(overlapping_ranges)} processed date ranges - will re-fetch and re-analyze")
            else:
                logger.info(f"No processed date ranges found to remove (range may not have been processed yet)")
                print(f"[PRINT] No processed date ranges found to remove")
        
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
                # Handle different credential formats:
                # 1. {"app_password": "..."} - from /accounts/yahoo endpoint
                # 2. {"email": "...", "password": "..."} - from /accounts endpoint or add_account.py
                if 'app_password' in creds:
                    # Format 1: app_password stored separately, use account.email
                    connector = YahooConnector(account.email, creds['app_password'])
                elif 'email' in creds and 'password' in creds:
                    # Format 2: email and password both in credentials
                    connector = YahooConnector(creds['email'], creds['password'])
                else:
                    # Fallback: try using account.email and credentials as password (for test-connection format)
                    connector = YahooConnector(account.email, credentials_json)
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
        service = AnalysisService(db, user_id, account_id, run_id)
        logger.info(f"Calling analyze_date_range for run_id={analysis_run.id}")
        result = service.analyze_date_range(
            connector,
            start_date,
            end_date,
            run_id=analysis_run.id
        )
        
        # Check if cancelled during processing
        db.refresh(analysis_run)
        if analysis_run.status == "cancelled":
            logger.info(f"Analysis run {run_id} was cancelled during processing, reverting changes")
            print(f"[PRINT] Analysis run {run_id} was cancelled during processing, reverting changes")
            # Revert changes
            service.revert_run_changes()
            return
        
        logger.info(f"Analysis completed: {result}")
        
        # Update analysis run - refresh to get latest state
        db.refresh(analysis_run)
        if analysis_run.status != "cancelled":  # Only update if not cancelled
            analysis_run.status = "completed"
            analysis_run.emails_processed = result['emails_processed']
            analysis_run.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"Analysis run {analysis_run.id} marked as completed")
        
    except ValueError as e:
        # Check if cancelled first
        try:
            db.refresh(analysis_run)
            if analysis_run.status == "cancelled":
                logger.info(f"Analysis run {run_id} was cancelled, reverting changes")
                print(f"[PRINT] Analysis run {run_id} was cancelled, reverting changes")
                try:
                    service = AnalysisService(db, user_id, account_id, run_id)
                    service.revert_run_changes()
                except:
                    pass  # Ignore revert errors if service wasn't created
                return
        except:
            pass
        
        # Handle token expiration/revocation errors
        error_msg = str(e)
        logger.error(f"ValueError during analysis: {error_msg}")
        print(f"[PRINT] ValueError during analysis: {error_msg}")
        
        # Rollback any processed date ranges that were marked during this failed analysis
        # Note: We can't easily track ranges from ValueError since it happens before result is returned
        # But we'll try to get them from the service if possible
        try:
            # Try to get processed ranges from the service's date tracker
            from app.date_tracker import DateTracker
            date_tracker = DateTracker(db, account_id)
            # We can't easily determine which ranges were processed, so we'll skip rollback for ValueError
            # The ranges should be minimal since ValueError typically happens early
        except:
            pass
        
        if 'expired or revoked' in error_msg or 'invalid_grant' in error_msg:
            try:
                account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
                if account:
                    account.is_active = False
                analysis_run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
                if analysis_run:
                    analysis_run.status = "failed"
                    analysis_run.completed_at = datetime.utcnow()
                    if hasattr(analysis_run, 'error_message'):
                        analysis_run.error_message = "Email account credentials expired or revoked. Please reconnect your account."
                db.commit()
                logger.info(f"Account {account.email if account else 'unknown'} marked as inactive due to expired/revoked token")
                print(f"[PRINT] Account {account.email if account else 'unknown'} marked as inactive due to expired/revoked token")
            except Exception as update_error:
                logger.error(f"Failed to update account/run status: {update_error}")
                print(f"[PRINT] Failed to update account/run status: {update_error}")
                db.rollback()
        else:
            # Re-raise if it's a different ValueError
            raise
    except Exception as e:
        # Check if cancelled first
        try:
            db.refresh(analysis_run)
            if analysis_run.status == "cancelled":
                logger.info(f"Analysis run {run_id} was cancelled, reverting changes")
                print(f"[PRINT] Analysis run {run_id} was cancelled, reverting changes")
                try:
                    service = AnalysisService(db, user_id, account_id, run_id)
                    service.revert_run_changes()
                except:
                    pass  # Ignore revert errors if service wasn't created
                return
        except:
            pass
        
        error_msg = str(e)
        logger.error(f"Analysis error: {error_msg}", exc_info=True)
        print(f"[PRINT] Analysis error: {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Check for specific error types
        error_type = "unknown"
        if "expired" in error_msg.lower() or "revoked" in error_msg.lower() or "invalid_grant" in error_msg.lower():
            error_type = "token_expired"
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            error_type = "connection_error"
        elif "credentials" in error_msg.lower() or "authentication" in error_msg.lower():
            error_type = "auth_error"
        
        # Note: Processed date ranges are now rolled back automatically in the analysis service
        # if the analysis fails. The service tracks ranges and removes them on exception.
        
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
                
                # Store user-friendly error message
                if error_type == "token_expired":
                    analysis_run.error_message = "Email account credentials expired or revoked. Please reconnect your account."
                    account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
                    if account:
                        account.is_active = False
                        logger.info(f"Marking account {account.email} as inactive due to error")
                        print(f"[PRINT] Marking account {account.email} as inactive due to error")
                elif error_type == "connection_error":
                    analysis_run.error_message = "Connection error: Unable to connect to email service. Please check your network connection and try again."
                elif error_type == "auth_error":
                    analysis_run.error_message = "Authentication error: Invalid credentials. Please check your account settings."
                else:
                    # Store a sanitized version of the error (first 200 chars to avoid huge messages)
                    sanitized_error = error_msg[:200] if len(error_msg) > 200 else error_msg
                    analysis_run.error_message = f"Analysis failed: {sanitized_error}"
                
                db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update analysis run status: {update_error}")
            print(f"[PRINT] Failed to update analysis run status: {update_error}")
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
        "completed_at": analysis_run.completed_at.isoformat() if analysis_run.completed_at else None,
        "error_message": getattr(analysis_run, 'error_message', None)
    }

@router.get("/runs")
async def list_analysis_runs(
    username: str,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List analysis runs for a user"""
    import logging
    logger = logging.getLogger(__name__)
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"User {username} not found when listing analysis runs")
        return []
    
    query = db.query(AnalysisRun).filter(AnalysisRun.user_id == user.id)
    if account_id:
        query = query.filter(AnalysisRun.account_id == account_id)
        logger.info(f"Filtering analysis runs for user {username}, account_id {account_id}")
    else:
        logger.info(f"Listing all analysis runs for user {username} (no account filter)")
    
    runs = query.order_by(AnalysisRun.created_at.desc()).limit(50).all()
    logger.info(f"Found {len(runs)} analysis runs for user {username}")
    
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

@router.post("/runs/{run_id}/retry", response_model=AnalysisResponse)
async def retry_analysis_run(
    run_id: int,
    username: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry a failed analysis run with the same parameters"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Verify user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get the original failed run
    original_run = db.query(AnalysisRun).filter(
        AnalysisRun.id == run_id,
        AnalysisRun.user_id == user.id
    ).first()
    
    if not original_run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    
    # Only allow retry for failed runs
    if original_run.status != "failed":
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot retry analysis run with status '{original_run.status}'. Only failed runs can be retried."
        )
    
    # Verify account still exists and is accessible
    account = db.query(EmailAccount).filter(
        EmailAccount.id == original_run.account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    logger.info(f"Retrying analysis run {run_id} for user {username}")
    print(f"[PRINT] Retrying analysis run {run_id} for user {username}")
    
    # Create new analysis run with same parameters
    new_run = AnalysisRun(
        user_id=user.id,
        account_id=original_run.account_id,
        start_date=original_run.start_date,
        end_date=original_run.end_date,
        status="pending"
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)
    
    # Start background analysis
    logger.info(f"Adding background task for retry run_id={new_run.id}")
    print(f"[PRINT] Adding background task for retry run_id={new_run.id}")
    background_tasks.add_task(
        process_batch_analysis,
        new_run.id,
        user.id,
        account.id,
        original_run.start_date,
        original_run.end_date
    )
    
    return AnalysisResponse(
        run_id=new_run.id,
        status="pending",
        message="Analysis retry started in background"
    )

@router.post("/runs/{run_id}/stop")
async def stop_analysis_run(
    run_id: int,
    username: str,
    db: Session = Depends(get_db)
):
    """Stop a running analysis and revert changes"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Verify user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get the analysis run
    analysis_run = db.query(AnalysisRun).filter(
        AnalysisRun.id == run_id,
        AnalysisRun.user_id == user.id
    ).first()
    
    if not analysis_run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    
    # Only allow stopping runs that are pending or processing
    if analysis_run.status not in ["pending", "processing"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop analysis run with status '{analysis_run.status}'. Only pending or processing runs can be stopped."
        )
    
    logger.info(f"Stopping analysis run {run_id} for user {username}")
    print(f"[PRINT] Stopping analysis run {run_id} for user {username}")
    
    # Mark as cancelled - the background task will check this and revert
    analysis_run.status = "cancelled"
    db.commit()
    
    # Revert changes made by this run
    try:
        # Delete analysis results created by this run
        analysis_results = db.query(AnalysisResult).filter(
            AnalysisResult.analysis_run_id == run_id
        ).all()
        
        # Get email IDs that were only analyzed by this run
        email_ids_to_check = [ar.email_id for ar in analysis_results]
        
        # Delete analysis results
        for ar in analysis_results:
            db.delete(ar)
        
        # Delete emails that were created during this run
        # We'll identify them by checking if they have no other analysis results
        if email_ids_to_check:
            emails_to_delete = db.query(EmailMetadata).filter(
                EmailMetadata.id.in_(email_ids_to_check),
                EmailMetadata.account_id == analysis_run.account_id
            ).all()
            
            for email in emails_to_delete:
                # Check if this email has any other analysis results
                other_results = db.query(AnalysisResult).filter(
                    AnalysisResult.email_id == email.id,
                    AnalysisResult.analysis_run_id != run_id
                ).count()
                
                if other_results == 0:
                    # This email was only analyzed by this run, delete it
                    db.delete(email)
        
        # Revert processed date ranges that were created during this run
        # We need to track which ranges were processed by this run
        # For now, we'll remove ranges that were processed after the run was created
        # and overlap with the run's date range
        from app.database import ProcessedDateRange
        from datetime import timedelta
        
        # Remove ranges that were processed during this run's timeframe
        # We'll be conservative and only remove ranges created very recently
        # (within the last hour) that overlap with this run's date range
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        overlapping_ranges = db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == analysis_run.account_id,
            ProcessedDateRange.start_date < analysis_run.end_date,
            ProcessedDateRange.end_date > analysis_run.start_date,
            ProcessedDateRange.processed_at >= analysis_run.created_at
        ).all()
        
        for range_obj in overlapping_ranges:
            db.delete(range_obj)
        
        db.commit()
        logger.info(f"Successfully reverted changes for cancelled run {run_id}")
        print(f"[PRINT] Successfully reverted changes for cancelled run {run_id}")
        
    except Exception as e:
        logger.error(f"Error reverting changes for run {run_id}: {e}", exc_info=True)
        print(f"[PRINT] Error reverting changes for run {run_id}: {e}")
        db.rollback()
        # Still mark as cancelled even if revert fails
        analysis_run.status = "cancelled"
        db.commit()
    
    return {
        "run_id": run_id,
        "status": "cancelled",
        "message": "Analysis stopped and changes reverted"
    }

