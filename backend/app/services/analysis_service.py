from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from datetime import datetime
from typing import Dict, List
import json
import logging

from app.database import EmailMetadata, AnalysisResult, AnalysisRun
from app.encryption import EncryptionManager
from app.nlp_analyzer import NLPAnalyzer
from app.date_tracker import DateTracker

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for batch email analysis"""
    
    def __init__(self, db: Session, user_id: int, account_id: int, run_id: int = None):
        self.db = db
        self.user_id = user_id
        self.account_id = account_id
        self.run_id = run_id
        self.enc_manager = EncryptionManager(user_id)
        self.nlp_analyzer = NLPAnalyzer()
        self.date_tracker = DateTracker(db, account_id)
        self.processed_ranges = []  # Track ranges processed in this run for revert
        self.processed_email_ids = []  # Track email IDs processed in this run
    
    def analyze_date_range(
        self,
        connector,
        start_date: datetime,
        end_date: datetime,
        run_id: int = None
    ) -> Dict:
        """
        Analyze emails in date range, skipping already processed dates
        """
        # Use self.run_id if available, otherwise use parameter
        if self.run_id:
            run_id = self.run_id
        if run_id is None:
            raise ValueError("run_id is required for analysis results")
        # Get unprocessed date ranges
        unprocessed_ranges = self.date_tracker.get_unprocessed_ranges(start_date, end_date)
        
        logger.info(f"Found {len(unprocessed_ranges)} unprocessed ranges to analyze")
        print(f"[PRINT] Found {len(unprocessed_ranges)} unprocessed ranges to analyze")
        
        if not unprocessed_ranges:
            logger.info("All dates in range already processed")
            print("[PRINT] All dates in range already processed")
            return {
                'emails_processed': 0,
                'message': 'All dates in range already processed'
            }
        
        # Get the analysis run to update progress incrementally
        analysis_run = self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        
        # Calculate total emails count before processing (if method exists)
        total_emails_expected = None
        if analysis_run and hasattr(connector, 'get_email_count_by_date_range'):
            try:
                logger.info("Calculating total email count for progress tracking...")
                print("[PRINT] Calculating total email count...")
                total_count = 0
                for range_start, range_end in unprocessed_ranges:
                    try:
                        count = connector.get_email_count_by_date_range(range_start, range_end)
                        total_count += count
                        logger.info(f"Range {range_start} to {range_end}: {count} emails")
                    except Exception as e:
                        logger.warning(f"Failed to get count for range {range_start} to {range_end}: {e}")
                        # If we can't get count for one range, set total to None
                        total_count = None
                        break
                
                if total_count is not None:
                    total_emails_expected = total_count
                    analysis_run.total_emails = total_emails_expected
                    self.db.commit()
                    logger.info(f"Total emails to process: {total_emails_expected}")
                    print(f"[PRINT] Total emails to process: {total_emails_expected}")
            except Exception as e:
                logger.warning(f"Failed to calculate total email count: {e}, continuing without total")
                print(f"[PRINT] Failed to calculate total email count: {e}")
        
        total_emails = 0
        # Track ranges that have been marked as processed in this analysis
        # If analysis fails, we'll need to remove these to prevent premature marking
        processed_ranges_in_this_run = []
        
        try:
            # Process each unprocessed range
            for range_start, range_end in unprocessed_ranges:
                # Check if run was cancelled
                if self.run_id:
                    analysis_run = self.db.query(AnalysisRun).filter(AnalysisRun.id == self.run_id).first()
                    if analysis_run and analysis_run.status == "cancelled":
                        logger.info(f"Analysis run {self.run_id} was cancelled, stopping processing")
                        print(f"[PRINT] Analysis run {self.run_id} was cancelled, stopping processing")
                        break
                
                logger.info(f"Processing range: {range_start} to {range_end}")
                print(f"[PRINT] Processing range: {range_start} to {range_end}")
                
                # Create progress callback to update database during fetching
                def update_fetch_progress(fetched_count, total_count):
                    if run_id:
                        try:
                            import sqlite3
                            import os
                            db_url = os.getenv("DATABASE_URL", "sqlite:///./data/mailmind.db")
                            db_path = db_url.replace("sqlite:///", "")
                            if not os.path.isabs(db_path):
                                db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), db_path)
                            
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            # Update emails_processed to show fetching progress
                            cursor.execute(
                                "UPDATE analysis_runs SET emails_processed = ? WHERE id = ?",
                                (total_emails + fetched_count, run_id)
                            )
                            conn.commit()
                            conn.close()
                            logger.info(f"Fetch progress: {fetched_count}/{total_count} emails fetched (run_id={run_id})")
                            print(f"[PRINT] Fetch progress: {fetched_count}/{total_count} emails fetched (run_id={run_id})")
                        except Exception as e:
                            logger.warning(f"Failed to update fetch progress: {e}")
                
                # Fetch emails with progress callback
                emails = connector.fetch_emails_by_date_range(range_start, range_end, progress_callback=update_fetch_progress)
                logger.info(f"Fetched {len(emails)} emails for this range")
                print(f"[PRINT] Fetched {len(emails)} emails for this range")
                
                if not emails:
                    logger.info(f"No emails in range {range_start} to {range_end}, marking as processed anyway")
                    print(f"[PRINT] No emails in range, marking as processed anyway")
                    # Mark range as processed even if no emails (to prevent gaps from getting stuck)
                    self.date_tracker.mark_range_processed(range_start, range_end, 0)
                    processed_ranges_in_this_run.append((range_start, range_end))
                    # Still update progress (total_emails stays the same, but ensure DB is synced)
                    if run_id:
                        try:
                            result = self.db.execute(
                                text("UPDATE analysis_runs SET emails_processed = :count WHERE id = :run_id"),
                                {"count": total_emails, "run_id": run_id}
                            )
                            self.db.commit()
                            logger.info(f"Updated progress after empty range: {total_emails} emails (run_id={run_id})")
                        except Exception as e:
                            logger.warning(f"Failed to update progress after empty range: {e}")
                    continue
                
                # Process emails in chunks to update progress incrementally
                # This allows the frontend to see progress updates during processing
                chunk_size = 50  # Process 50 emails at a time
                all_stored_emails = []
                
                for chunk_start in range(0, len(emails), chunk_size):
                    chunk_end = min(chunk_start + chunk_size, len(emails))
                    email_chunk = emails[chunk_start:chunk_end]
                    
                    # Store email metadata for this chunk
                    stored_emails = []
                    for email_data in email_chunk:
                        # Check if email already exists
                        existing = self.db.query(EmailMetadata).filter(
                            EmailMetadata.message_id == email_data['message_id'],
                            EmailMetadata.account_id == self.account_id
                        ).first()
                        
                        if existing:
                            stored_emails.append(existing)
                            continue
                        
                        # Create new metadata
                        email_meta = EmailMetadata(
                            account_id=self.account_id,
                            message_id=email_data['message_id'],
                            sender_email=email_data['sender_email'],
                            sender_name=email_data.get('sender_name'),
                            subject=email_data.get('subject', ''),
                            date_received=email_data['date_received']
                        )
                        self.db.add(email_meta)
                        stored_emails.append(email_meta)
                    
                    # Commit this chunk with error handling for race conditions
                    try:
                        self.db.commit()
                        logger.info(f"Committed chunk {chunk_start//chunk_size + 1}: {len(stored_emails)} email metadata records")
                        print(f"[PRINT] Committed chunk {chunk_start//chunk_size + 1}: {len(stored_emails)} emails")
                    except IntegrityError as e:
                        # Handle race condition: another process may have inserted the same email
                        logger.warning(f"IntegrityError during email commit (likely race condition): {e}")
                        print(f"[PRINT] IntegrityError during email commit (likely race condition): {e}")
                        self.db.rollback()
                        
                        # Re-fetch existing emails that may have been inserted by another process
                        stored_emails = []
                        for email_data in email_chunk:
                            existing = self.db.query(EmailMetadata).filter(
                                EmailMetadata.message_id == email_data['message_id'],
                                EmailMetadata.account_id == self.account_id
                            ).first()
                            
                            if existing:
                                stored_emails.append(existing)
                            else:
                                # Try to insert again (shouldn't happen, but handle gracefully)
                                logger.warning(f"Email {email_data['message_id']} not found after rollback, skipping")
                                print(f"[PRINT] Email {email_data['message_id']} not found after rollback, skipping")
                    
                    # Refresh to get IDs
                    for email_meta in stored_emails:
                        self.db.refresh(email_meta)
                    
                    all_stored_emails.extend(stored_emails)
                    
                    # Track total emails processed (don't update DB here - chunk storage is fast,
                    # and updating would reset the fetch progress which confuses the UI)
                    total_emails += len(email_chunk)
                    logger.info(f"Stored chunk: {total_emails}/{len(emails)} emails (run_id={run_id})")
                    print(f"[PRINT] Stored chunk: {total_emails}/{len(emails)} emails (run_id={run_id})")
                
                # Analyze all emails together (analysis is more efficient on larger batches)
                analysis_data = self.nlp_analyzer.analyze_batch(emails)
                
                # Store analysis results
                for email_meta, email_data in zip(all_stored_emails, emails):
                    # Determine clusters
                    sender_cluster = self._get_sender_cluster(
                        email_data['sender_email'],
                        analysis_data['sender_patterns']
                    )
                    subject_cluster = self._get_subject_cluster(
                        email_data.get('subject', ''),
                        analysis_data['subject_clusters']
                    )
                    category = self._get_category(email_data, analysis_data['categories'])
                    
                    # Encrypt full analysis
                    encrypted_analysis = self.enc_manager.encrypt({
                        'sender_email': email_data['sender_email'],
                        'sender_name': email_data.get('sender_name'),
                        'subject': email_data.get('subject', ''),
                        'snippet': email_data.get('snippet', ''),
                        'date_received': email_data['date_received'].isoformat(),
                        'analysis': analysis_data
                    })
                    
                    analysis_result = AnalysisResult(
                        email_id=email_meta.id,
                        analysis_run_id=run_id,
                        encrypted_analysis=encrypted_analysis,
                        sender_cluster=sender_cluster,
                        subject_cluster=subject_cluster,
                        category=category
                    )
                    self.db.add(analysis_result)
                    # Track email IDs for potential revert
                    self.processed_email_ids.append(email_meta.id)
                
                self.db.commit()
                logger.info(f"Committed analysis results for {len(emails)} emails")
                print(f"[PRINT] Committed analysis results for {len(emails)} emails")
                
                # Note: total_emails was already updated after storing emails, before analysis
                # So we don't need to update it again here
                
                # Mark range as processed
                try:
                    logger.info(f"Marking range as processed: {range_start} to {range_end}, emails: {len(emails)}")
                    print(f"[PRINT] Marking range as processed: {range_start} to {range_end}, emails: {len(emails)}")
                    self.date_tracker.mark_range_processed(range_start, range_end, len(emails))
                    processed_ranges_in_this_run.append((range_start, range_end))
                    logger.info(f"Successfully marked range as processed")
                    print(f"[PRINT] Successfully marked range as processed")
                except Exception as e:
                    logger.error(f"ERROR: Failed to mark range as processed: {e}", exc_info=True)
                    print(f"[PRINT] ERROR: Failed to mark range as processed: {e}")
                    import traceback
                    traceback.print_exc()
                    # Don't fail the whole analysis if marking fails, but log it
                    # If marking fails, we can't track it, so we'll leave it as is
            
            return {
                'emails_processed': total_emails,
                'ranges_processed': len(unprocessed_ranges),
                'processed_ranges': processed_ranges_in_this_run  # Return for cleanup if needed
            }
        except Exception as e:
            # If analysis fails, rollback any processed ranges that were marked
            if processed_ranges_in_this_run:
                logger.error(f"Analysis failed, rolling back {len(processed_ranges_in_this_run)} processed date ranges")
                print(f"[PRINT] Analysis failed, rolling back {len(processed_ranges_in_this_run)} processed date ranges")
                try:
                    self.date_tracker.remove_ranges(processed_ranges_in_this_run)
                    logger.info("Successfully rolled back processed date ranges.")
                    print("Successfully rolled back processed date ranges.")
                except Exception as rollback_e:
                    logger.error(f"ERROR: Failed to rollback processed date ranges: {rollback_e}", exc_info=True)
                    print(f"ERROR: Failed to rollback processed date ranges: {rollback_e}")
            raise  # Re-raise the original exception
    
    def _get_sender_cluster(self, sender_email: str, sender_patterns: Dict) -> str:
        """Get sender cluster identifier"""
        top_senders = sender_patterns.get('top_senders', [])
        for idx, sender_info in enumerate(top_senders[:10]):
            if sender_info['email'] == sender_email:
                return f"sender_top_{idx + 1}"
        return "sender_other"
    
    def _get_subject_cluster(self, subject: str, subject_clusters: List[Dict]) -> str:
        """Get subject cluster identifier"""
        for cluster in subject_clusters:
            if subject in cluster.get('subjects', []):
                return f"subject_cluster_{cluster['cluster_id']}"
        return "subject_unclustered"
    
    def _get_category(self, email_data: Dict, categories: Dict) -> str:
        """Get email category"""
        # This matches the categorization logic from NLP analyzer
        subject = (email_data.get('subject', '') or '').lower()
        sender = (email_data.get('sender_email', '') or '').lower()
        
        if any(kw in subject for kw in ['notification', 'alert', 'reminder']):
            return 'notifications'
        elif any(kw in subject or kw in sender for kw in ['newsletter', 'digest', 'unsubscribe']):
            return 'newsletters'
        elif any(kw in sender for kw in ['facebook', 'twitter', 'linkedin']):
            return 'social'
        elif any(kw in subject or kw in sender for kw in ['order', 'purchase', 'shipping']):
            return 'shopping'
        elif any(kw in subject for kw in ['meeting', 'calendar', 'team']):
            return 'work'
        elif '@' in sender and not any(kw in sender for kw in ['noreply', 'no-reply']):
            return 'personal'
        return 'other'
    
    def revert_run_changes(self):
        """Revert changes made by this analysis run"""
        if not self.run_id:
            return
        
        logger.info(f"Reverting changes for run {self.run_id}")
        print(f"[PRINT] Reverting changes for run {self.run_id}")
        
        try:
            # Delete analysis results created by this run
            analysis_results = self.db.query(AnalysisResult).filter(
                AnalysisResult.analysis_run_id == self.run_id
            ).all()
            
            email_ids_with_results = set()
            for ar in analysis_results:
                email_ids_with_results.add(ar.email_id)
                self.db.delete(ar)
            
            # Delete emails that were created during this run and have no other analysis results
            if self.processed_email_ids:
                for email_id in self.processed_email_ids:
                    if email_id in email_ids_with_results:
                        # Check if this email has any other analysis results
                        other_results = self.db.query(AnalysisResult).filter(
                            AnalysisResult.email_id == email_id,
                            AnalysisResult.analysis_run_id != self.run_id
                        ).count()
                        
                        if other_results == 0:
                            # This email was only analyzed by this run, delete it
                            email = self.db.query(EmailMetadata).filter(
                                EmailMetadata.id == email_id
                            ).first()
                            if email:
                                self.db.delete(email)
            
            # Revert processed date ranges
            if self.processed_ranges:
                self.date_tracker.remove_ranges(self.processed_ranges)
            
            self.db.commit()
            logger.info(f"Successfully reverted changes for run {self.run_id}")
            print(f"[PRINT] Successfully reverted changes for run {self.run_id}")
            
        except Exception as e:
            logger.error(f"Error reverting changes for run {self.run_id}: {e}", exc_info=True)
            print(f"[PRINT] Error reverting changes for run {self.run_id}: {e}")
            self.db.rollback()
            raise

