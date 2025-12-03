from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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
    
    def __init__(self, db: Session, user_id: int, account_id: int):
        self.db = db
        self.user_id = user_id
        self.account_id = account_id
        self.enc_manager = EncryptionManager(user_id)
        self.nlp_analyzer = NLPAnalyzer()
        self.date_tracker = DateTracker(db, account_id)
    
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
        
        total_emails = 0
        
        # Process each unprocessed range
        for range_start, range_end in unprocessed_ranges:
            logger.info(f"Processing range: {range_start} to {range_end}")
            print(f"[PRINT] Processing range: {range_start} to {range_end}")
            # Fetch emails with timeout handling
            try:
                emails = connector.fetch_emails_by_date_range(range_start, range_end)
                logger.info(f"Fetched {len(emails)} emails for this range")
                print(f"[PRINT] Fetched {len(emails)} emails for this range")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error fetching emails for range {range_start} to {range_end}: {error_msg}")
                print(f"[PRINT] Error fetching emails: {error_msg}")
                
                # Check if it's a timeout error
                if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
                    raise Exception(f"Request timed out while fetching emails from {range_start.date()} to {range_end.date()}. "
                                  f"The date range may be too large. Try analyzing a smaller date range (e.g., 1-3 months at a time).")
                else:
                    raise Exception(f"Failed to fetch emails: {error_msg}")
            
            if not emails:
                logger.info(f"No emails in range {range_start} to {range_end}, marking as processed anyway")
                print(f"[PRINT] No emails in range, marking as processed anyway")
                # Mark range as processed even if no emails (to prevent gaps from getting stuck)
                self.date_tracker.mark_range_processed(range_start, range_end, 0)
                continue
            
            # Store email metadata
            stored_emails = []
            for email_data in emails:
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
            
            # Commit with error handling for race conditions
            try:
                self.db.commit()
            except IntegrityError as e:
                # Handle race condition: another process may have inserted the same email
                logger.warning(f"IntegrityError during email commit (likely race condition): {e}")
                print(f"[PRINT] IntegrityError during email commit (likely race condition): {e}")
                self.db.rollback()
                
                # Re-fetch existing emails that may have been inserted by another process
                stored_emails = []
                for email_data in emails:
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
            
            # Analyze batch
            analysis_data = self.nlp_analyzer.analyze_batch(emails)
            
            # Store analysis results
            for email_meta, email_data in zip(stored_emails, emails):
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
            
            self.db.commit()
            total_emails += len(emails)
            
            # Mark range as processed
            try:
                logger.info(f"Marking range as processed: {range_start} to {range_end}, emails: {len(emails)}")
                print(f"[PRINT] Marking range as processed: {range_start} to {range_end}, emails: {len(emails)}")
                self.date_tracker.mark_range_processed(range_start, range_end, len(emails))
                logger.info(f"Successfully marked range as processed")
                print(f"[PRINT] Successfully marked range as processed")
            except Exception as e:
                logger.error(f"ERROR: Failed to mark range as processed: {e}", exc_info=True)
                print(f"[PRINT] ERROR: Failed to mark range as processed: {e}")
                import traceback
                traceback.print_exc()
                # Don't fail the whole analysis if marking fails, but log it
        
        return {
            'emails_processed': total_emails,
            'ranges_processed': len(unprocessed_ranges)
        }
    
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

