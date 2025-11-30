from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import logging
from app.database import ProcessedDateRange

logger = logging.getLogger(__name__)

class DateTracker:
    """Tracks processed date ranges to avoid re-analyzing emails"""
    
    def __init__(self, db: Session, account_id: int):
        self.db = db
        self.account_id = account_id
    
    def _normalize_datetime(self, dt: datetime) -> datetime:
        """Normalize datetime to timezone-naive UTC for comparison"""
        if dt is None:
            return dt
        if dt.tzinfo is not None:
            # Convert to UTC and remove timezone info
            # Use UTC timezone for conversion
            from dateutil import tz as dateutil_tz
            utc_dt = dt.astimezone(dateutil_tz.UTC)
            return utc_dt.replace(tzinfo=None)
        return dt
    
    def get_unprocessed_ranges(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """
        Get date ranges that haven't been processed yet
        Returns list of (start, end) tuples
        """
        # Normalize input dates
        start_date = self._normalize_datetime(start_date)
        end_date = self._normalize_datetime(end_date)
        
        # Get all processed ranges for this account
        processed = self.db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == self.account_id
        ).order_by(ProcessedDateRange.start_date).all()
        
        if not processed:
            # No processed ranges, return the full range
            return [(start_date, end_date)]
        
        unprocessed = []
        current_start = start_date
        
        for proc_range in processed:
            # Normalize processed range dates
            proc_start = self._normalize_datetime(proc_range.start_date)
            proc_end = self._normalize_datetime(proc_range.end_date)
            
            # If there's a gap before this processed range
            if current_start < proc_start:
                gap_end = min(proc_start, end_date)
                if gap_end > current_start:
                    unprocessed.append((current_start, gap_end))
            
            # Move current_start to after this processed range
            if proc_end > current_start:
                current_start = max(current_start, proc_end)
        
        # Check if there's remaining unprocessed range after last processed
        if current_start < end_date:
            unprocessed.append((current_start, end_date))
        
        return unprocessed
    
    def mark_range_processed(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        emails_count: int
    ):
        """Mark a date range as processed"""
        # Normalize input dates
        start_date = self._normalize_datetime(start_date)
        end_date = self._normalize_datetime(end_date)
        
        logger.info(f"mark_range_processed called: account_id={self.account_id}, start={start_date}, end={end_date}, count={emails_count}")
        print(f"[PRINT] mark_range_processed called: account_id={self.account_id}, start={start_date}, end={end_date}, count={emails_count}")
        
        # Check for overlaps and merge if needed
        overlapping = self.db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == self.account_id,
            ProcessedDateRange.start_date <= end_date,
            ProcessedDateRange.end_date >= start_date
        ).all()
        
        logger.info(f"Found {len(overlapping)} overlapping ranges")
        print(f"[PRINT] Found {len(overlapping)} overlapping ranges")
        
        if overlapping:
            # Merge overlapping ranges - normalize all dates before comparison
            normalized_overlapping = [
                (self._normalize_datetime(r.start_date), self._normalize_datetime(r.end_date))
                for r in overlapping
            ]
            min_start = min([r[0] for r in normalized_overlapping] + [start_date])
            max_end = max([r[1] for r in normalized_overlapping] + [end_date])
            total_count = sum(r.emails_count for r in overlapping) + emails_count
            
            logger.info(f"Merging ranges: {min_start} to {max_end}, total emails: {total_count}")
            
            # Delete old ranges
            for r in overlapping:
                self.db.delete(r)
            
            # Create merged range
            new_range = ProcessedDateRange(
                account_id=self.account_id,
                start_date=min_start,
                end_date=max_end,
                emails_count=total_count
            )
            self.db.add(new_range)
        else:
            # No overlap, create new range
            logger.info(f"Creating new range: {start_date} to {end_date}, emails: {emails_count}")
            new_range = ProcessedDateRange(
                account_id=self.account_id,
                start_date=start_date,
                end_date=end_date,
                emails_count=emails_count
            )
            self.db.add(new_range)
        
        try:
            self.db.commit()
            logger.info(f"Successfully committed ProcessedDateRange to database")
            print(f"[PRINT] Successfully committed ProcessedDateRange to database")
        except Exception as e:
            logger.error(f"ERROR committing ProcessedDateRange: {e}", exc_info=True)
            print(f"[PRINT] ERROR committing ProcessedDateRange: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            raise
    
    def get_processed_ranges(self) -> List[ProcessedDateRange]:
        """Get all processed date ranges for this account"""
        return self.db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == self.account_id
        ).order_by(ProcessedDateRange.start_date).all()
    
    def is_date_range_processed(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> bool:
        """Check if a date range is fully processed"""
        unprocessed = self.get_unprocessed_ranges(start_date, end_date)
        return len(unprocessed) == 0

