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
        
        # Get ALL processed ranges for this account (not just overlapping ones)
        # We need all ranges to properly calculate gaps, even if they're outside the requested range
        all_processed = self.db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == self.account_id
        ).order_by(ProcessedDateRange.start_date).all()
        
        if not all_processed:
            # No processed ranges, return the full range
            return [(start_date, end_date)]
        
        # Normalize and merge overlapping processed ranges
        normalized_ranges = []
        for proc_range in all_processed:
            proc_start = self._normalize_datetime(proc_range.start_date)
            proc_end = self._normalize_datetime(proc_range.end_date)
            normalized_ranges.append((proc_start, proc_end))
        
        # Merge overlapping ranges
        merged_ranges = []
        normalized_ranges.sort(key=lambda x: x[0])  # Sort by start date
        
        for proc_start, proc_end in normalized_ranges:
            if not merged_ranges:
                merged_ranges.append((proc_start, proc_end))
            else:
                last_start, last_end = merged_ranges[-1]
                # If this range overlaps or is adjacent to the last one, merge them
                if proc_start <= last_end:
                    # Overlapping or adjacent - merge
                    merged_ranges[-1] = (last_start, max(last_end, proc_end))
                else:
                    # No overlap - add as new range
                    merged_ranges.append((proc_start, proc_end))
        
        # Include all processed ranges that could affect gaps in the requested range
        # We need to include ranges that:
        # 1. Overlap with the requested range, OR
        # 2. End just before start_date (so we know where processed data ends before our range)
        # 3. Start just after end_date (so we know where processed data starts after our range)
        # Use a buffer to catch ranges near the boundaries
        from datetime import timedelta
        buffer = timedelta(days=365)  # 1 year buffer to catch nearby ranges
        relevant_ranges = [
            (ps, pe)
            for ps, pe in merged_ranges
            # Include if the range could affect gap calculation
            # Range is relevant if it's within buffer distance of the requested range
            if pe >= (start_date - buffer) and ps <= (end_date + buffer)
        ]
        
        logger.info(f"get_unprocessed_ranges: start={start_date}, end={end_date}, found {len(all_processed)} total ranges, {len(merged_ranges)} after merging, {len(relevant_ranges)} relevant to requested range")
        logger.info(f"Merged ranges: {[(str(ps.date()), str(pe.date())) for ps, pe in merged_ranges]}")
        logger.info(f"Relevant ranges: {[(str(ps.date()), str(pe.date())) for ps, pe in relevant_ranges]}")
        
        if not relevant_ranges:
            # No processed ranges that affect this period, return the full range
            return [(start_date, end_date)]
        
        unprocessed = []
        current_start = start_date
        
        for proc_start, proc_end in relevant_ranges:
            # Determine the effective range within the requested bounds
            # If range is completely before start_date, we still need to know where it ends
            # If range is completely after end_date, we still need to know where it starts
            # But for gap calculation, we only care about the part within [start_date, end_date]
            
            if proc_end < start_date:
                # Range is completely before start_date
                # This means data is processed up to proc_end, but we're only looking for gaps
                # within [start_date, end_date]. So we start from start_date.
                # Don't update current_start - we'll start gap detection from start_date
                continue
            
            if proc_start > end_date:
                # Range is completely after end_date - we've already passed it
                # No gap to add, but this shouldn't happen with our filter
                continue
            
            # Range overlaps with requested range - calculate gaps
            effective_start = max(proc_start, start_date)
            effective_end = min(proc_end, end_date)
            
            # If there's a gap before this processed range
            if current_start < effective_start:
                gap_end = min(effective_start, end_date)
                # Only add gap if it spans at least one full day (to avoid tiny gaps from timezone issues)
                # Use date comparison to ensure we're looking at full days, not just hours
                gap_start_date = current_start.date()
                gap_end_date = gap_end.date()
                # Check if gap spans at least one full day
                if gap_end_date > gap_start_date:
                    gap = (current_start, gap_end)
                    unprocessed.append(gap)
                    logger.info(f"Found gap: {gap[0]} to {gap[1]}")
            
            # Move current_start to after this processed range
            # Use effective_end to stay within bounds
            if effective_end > current_start:
                current_start = effective_end
        
        # Check if there's remaining unprocessed range after last processed
        if current_start < end_date:
            # Only add gap if it spans at least one full day
            gap_start_date = current_start.date()
            gap_end_date = end_date.date()
            if gap_end_date > gap_start_date:
                gap = (current_start, end_date)
                unprocessed.append(gap)
                logger.info(f"Found final gap: {gap[0]} to {gap[1]}")
        
        logger.info(f"Total gaps found: {len(unprocessed)}")
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
    
    def remove_ranges(self, ranges: List[Tuple[datetime, datetime]]) -> None:
        """
        Remove processed date ranges that overlap with the given ranges.
        This is used to rollback ranges that were marked as processed but the analysis failed.
        """
        if not ranges:
            return
        
        logger.info(f"Removing {len(ranges)} processed date ranges due to analysis failure")
        print(f"[PRINT] Removing {len(ranges)} processed date ranges due to analysis failure")
        
        for range_start, range_end in ranges:
            # Find ranges that overlap with this range
            # A range overlaps if: start <= range_end AND end >= range_start
            overlapping = self.db.query(ProcessedDateRange).filter(
                ProcessedDateRange.account_id == self.account_id,
                ProcessedDateRange.start_date <= range_end,
                ProcessedDateRange.end_date >= range_start
            ).all()
            
            if overlapping:
                logger.info(f"Found {len(overlapping)} overlapping ranges to remove for {range_start} to {range_end}")
                for r in overlapping:
                    self.db.delete(r)
        
        try:
            self.db.commit()
            logger.info(f"Successfully removed processed date ranges")
            print(f"[PRINT] Successfully removed processed date ranges")
        except Exception as e:
            logger.error(f"ERROR removing processed date ranges: {e}", exc_info=True)
            print(f"[PRINT] ERROR removing processed date ranges: {e}")
            self.db.rollback()
            # Don't raise - we don't want to fail the error handling itself
    
    def is_date_range_processed(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> bool:
        """Check if a date range is fully processed"""
        unprocessed = self.get_unprocessed_ranges(start_date, end_date)
        return len(unprocessed) == 0

