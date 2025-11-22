from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from app.database import ProcessedDateRange

class DateTracker:
    """Tracks processed date ranges to avoid re-analyzing emails"""
    
    def __init__(self, db: Session, account_id: int):
        self.db = db
        self.account_id = account_id
    
    def get_unprocessed_ranges(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """
        Get date ranges that haven't been processed yet
        Returns list of (start, end) tuples
        """
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
            # If there's a gap before this processed range
            if current_start < proc_range.start_date:
                gap_end = min(proc_range.start_date, end_date)
                if gap_end > current_start:
                    unprocessed.append((current_start, gap_end))
            
            # Move current_start to after this processed range
            if proc_range.end_date > current_start:
                current_start = max(current_start, proc_range.end_date)
        
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
        # Check for overlaps and merge if needed
        overlapping = self.db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == self.account_id,
            ProcessedDateRange.start_date <= end_date,
            ProcessedDateRange.end_date >= start_date
        ).all()
        
        if overlapping:
            # Merge overlapping ranges
            min_start = min([r.start_date for r in overlapping] + [start_date])
            max_end = max([r.end_date for r in overlapping] + [end_date])
            total_count = sum(r.emails_count for r in overlapping) + emails_count
            
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
            new_range = ProcessedDateRange(
                account_id=self.account_id,
                start_date=start_date,
                end_date=end_date,
                emails_count=emails_count
            )
            self.db.add(new_range)
        
        self.db.commit()
    
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

