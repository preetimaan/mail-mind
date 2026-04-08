from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import logging
from app.database import ProcessedDateRange

logger = logging.getLogger(__name__)

# ProcessedDateRange and all analysis windows use half-open intervals:
# [start_date, end_date) — start inclusive at midnight, end exclusive at midnight.
# Example: [2010-01-01, 2016-01-01) includes mail through 2015-12-31, not 2016-01-01.


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
        Get sub-ranges of [start_date, end_date) (half-open) that are not covered by processed ranges.
        Processed ranges are stored as [proc_start, proc_end) half-open.
        Returns list of (gap_start, gap_end) tuples, each half-open.
        """
        start_date = self._normalize_datetime(start_date)
        end_date = self._normalize_datetime(end_date)
        
        if end_date <= start_date:
            return []
        
        all_processed = self.db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == self.account_id
        ).order_by(ProcessedDateRange.start_date).all()
        
        if not all_processed:
            return [(start_date, end_date)]
        
        normalized_ranges = []
        for proc_range in all_processed:
            proc_start = self._normalize_datetime(proc_range.start_date)
            proc_end = self._normalize_datetime(proc_range.end_date)
            normalized_ranges.append((proc_start, proc_end))
        
        # Merge touching/overlapping half-open ranges: [a,b) and [b,c) share boundary b → merge
        merged_ranges = []
        normalized_ranges.sort(key=lambda x: x[0])

        for proc_start, proc_end in normalized_ranges:
            if proc_end <= proc_start:
                continue
            if not merged_ranges:
                merged_ranges.append((proc_start, proc_end))
            else:
                last_start, last_end = merged_ranges[-1]
                # Overlap or touch: new start < last exclusive end (strict half-open touch: ps == le)
                if proc_start < last_end:
                    merged_ranges[-1] = (last_start, max(last_end, proc_end))
                elif proc_start == last_end:
                    merged_ranges[-1] = (last_start, proc_end)
                else:
                    merged_ranges.append((proc_start, proc_end))
        
        buffer = timedelta(days=365)
        relevant_ranges = [
            (ps, pe)
            for ps, pe in merged_ranges
            if pe > (start_date - buffer) and ps < (end_date + buffer)
        ]
        
        logger.info(
            f"get_unprocessed_ranges: window=[{start_date}, {end_date}), "
            f"merged={len(merged_ranges)}, relevant={len(relevant_ranges)}"
        )
        
        if not relevant_ranges:
            return [(start_date, end_date)]
        
        unprocessed = []
        current_start = start_date
        
        for proc_start, proc_end in relevant_ranges:
            if proc_end <= start_date:
                continue
            if proc_start >= end_date:
                continue
            
            clip_ps = max(proc_start, start_date)
            clip_pe = min(proc_end, end_date)
            
            if current_start < clip_ps:
                unprocessed.append((current_start, clip_ps))
            
            if clip_pe > current_start:
                current_start = max(current_start, clip_pe)
        
        if current_start < end_date:
            unprocessed.append((current_start, end_date))
        
        logger.info(f"Total gaps found: {len(unprocessed)}")
        return unprocessed
    
    def mark_range_processed(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        emails_count: int
    ):
        """
        Mark [start_date, end_date) as processed (half-open).
        end_date is exclusive (first instant not covered).
        """
        start_date = self._normalize_datetime(start_date)
        end_date = self._normalize_datetime(end_date)
        
        if end_date <= start_date:
            logger.warning(
                "mark_range_processed called with empty/invalid half-open range; skipping: "
                f"{start_date} .. {end_date}"
            )
            return
        
        logger.info(
            f"mark_range_processed: account_id={self.account_id}, "
            f"[{start_date}, {end_date}), count={emails_count}"
        )
        print(f"[PRINT] mark_range_processed: [{start_date}, {end_date}), count={emails_count}")
        
        all_ranges = self.db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == self.account_id
        ).all()
        
        overlapping = []
        for r in all_ranges:
            r_start = self._normalize_datetime(r.start_date)
            r_end = self._normalize_datetime(r.end_date)
            if r_start < end_date and r_end > start_date:
                overlapping.append(r)
                logger.info(f"Overlapping/touching stored range: [{r_start}, {r_end})")
        
        logger.info(f"Found {len(overlapping)} ranges to merge with new [{start_date}, {end_date})")
        print(f"[PRINT] Merging with {len(overlapping)} existing ranges")
        
        if overlapping:
            normalized_overlapping = [
                (self._normalize_datetime(r.start_date), self._normalize_datetime(r.end_date))
                for r in overlapping
            ]
            min_start = min([r[0] for r in normalized_overlapping] + [start_date])
            max_end = max([r[1] for r in normalized_overlapping] + [end_date])
            total_count = sum(r.emails_count for r in overlapping) + emails_count
            
            logger.info(f"Merged half-open range: [{min_start}, {max_end}), total emails: {total_count}")
            print(f"[PRINT] Merged into [{min_start}, {max_end})")
            
            for r in overlapping:
                self.db.delete(r)
            
            new_range = ProcessedDateRange(
                account_id=self.account_id,
                start_date=min_start,
                end_date=max_end,
                emails_count=total_count
            )
            self.db.add(new_range)
        else:
            logger.info(f"Creating new range [{start_date}, {end_date}), emails: {emails_count}")
            new_range = ProcessedDateRange(
                account_id=self.account_id,
                start_date=start_date,
                end_date=end_date,
                emails_count=emails_count
            )
            self.db.add(new_range)
        
        try:
            self.db.commit()
            logger.info("Committed ProcessedDateRange")
            print(f"[PRINT] Successfully committed ProcessedDateRange")
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
        """Remove processed rows overlapping any given half-open [start, end)."""
        if not ranges:
            return
        
        logger.info(f"Removing processed ranges overlapping {len(ranges)} half-open window(s)")
        print(f"[PRINT] Removing ranges for rollback")
        
        for range_start, range_end in ranges:
            overlapping = self.db.query(ProcessedDateRange).filter(
                ProcessedDateRange.account_id == self.account_id,
                ProcessedDateRange.start_date < range_end,
                ProcessedDateRange.end_date > range_start
            ).all()
            
            if overlapping:
                logger.info(f"Deleting {len(overlapping)} rows overlapping [{range_start}, {range_end})")
                for r in overlapping:
                    self.db.delete(r)
        
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"ERROR removing processed date ranges: {e}", exc_info=True)
            self.db.rollback()
    
    def is_date_range_processed(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> bool:
        """True if [start_date, end_date) has no unprocessed gaps."""
        unprocessed = self.get_unprocessed_ranges(start_date, end_date)
        return len(unprocessed) == 0
