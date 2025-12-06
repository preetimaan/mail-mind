from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import Optional
from datetime import datetime, timedelta
from collections import Counter

from app.database import get_db, User, EmailAccount, EmailMetadata, AnalysisResult, ProcessedDateRange
from app.encryption import EncryptionManager

router = APIRouter()

@router.get("/summary")
async def get_summary(
    username: str,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get summary insights for user"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Return empty summary instead of 404 - user-friendly for new users
        return {
            'total_accounts': 0,
            'total_emails': 0,
            'total_senders': 0,
            'accounts': []
        }
    
    query = db.query(EmailAccount).filter(EmailAccount.user_id == user.id)
    if account_id:
        query = query.filter(EmailAccount.id == account_id)
    
    accounts = query.all()
    
    summary = {
        'total_accounts': len(accounts),
        'total_emails': 0,
        'total_senders': 0,
        'accounts': []
    }
    
    for account in accounts:
        email_count = db.query(EmailMetadata).filter(
            EmailMetadata.account_id == account.id
        ).count()
        
        sender_count = db.query(EmailMetadata.sender_email).filter(
            EmailMetadata.account_id == account.id
        ).distinct().count()
        
        # Get processed date ranges
        processed_ranges = db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == account.id
        ).all()
        
        account_summary = {
            'id': account.id,
            'email': account.email,
            'provider': account.provider,
            'email_count': email_count,
            'sender_count': sender_count,
            'processed_ranges': len(processed_ranges)
        }
        
        summary['accounts'].append(account_summary)
        summary['total_emails'] += email_count
    
    # Get unique senders across all accounts
    if account_id:
        summary['total_senders'] = db.query(EmailMetadata.sender_email).filter(
            EmailMetadata.account_id == account_id
        ).distinct().count()
    else:
        account_ids = [a.id for a in accounts]
        if account_ids:
            summary['total_senders'] = db.query(EmailMetadata.sender_email).filter(
                EmailMetadata.account_id.in_(account_ids)
            ).distinct().count()
    
    return summary

@router.get("/senders")
async def get_sender_insights(
    username: str,
    account_id: int,
    limit: Optional[int] = 20,
    db: Session = Depends(get_db)
):
    """Get top senders and patterns
    
    Args:
        limit: Maximum number of senders to return. If None or 0, returns all senders.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get sender counts - includes ALL emails for this account
    # Note: Groups by both sender_email and sender_name, so same email with different names
    # will appear as separate entries (this is correct behavior)
    query = db.query(
        EmailMetadata.sender_email,
        EmailMetadata.sender_name,
        func.count(EmailMetadata.id).label('count')
    ).filter(
        EmailMetadata.account_id == account_id
    ).group_by(
        EmailMetadata.sender_email,
        EmailMetadata.sender_name
    ).order_by(
        func.count(EmailMetadata.id).desc()
    )
    
    # Apply limit only if specified and > 0
    if limit and limit > 0:
        query = query.limit(limit)
    
    sender_counts = query.all()
    
    # Get total email count for this account (includes all emails, no filters)
    total_emails = db.query(EmailMetadata).filter(
        EmailMetadata.account_id == account_id
    ).count()
    
    senders = [
        {
            'email': sender,
            'name': name,
            'count': count,
            'percentage': round(count / total_emails * 100, 2) if total_emails > 0 else 0
        }
        for sender, name, count in sender_counts
    ]
    
    # Domain analysis
    domain_counts = Counter()
    for sender, _, count in sender_counts:
        if '@' in sender:
            domain = sender.split('@')[1]
            domain_counts[domain] += count
    
    return {
        'top_senders': senders,
        'top_domains': [
            {'domain': domain, 'count': count}
            for domain, count in domain_counts.most_common(10)
        ],
        'total_emails': total_emails
    }

@router.get("/categories")
async def get_category_insights(
    username: str,
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get email category distribution"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    category_counts = db.query(
        AnalysisResult.category,
        func.count(AnalysisResult.id).label('count')
    ).join(
        EmailMetadata
    ).filter(
        EmailMetadata.account_id == account_id
    ).group_by(
        AnalysisResult.category
    ).all()
    
    total = sum(count for _, count in category_counts)
    
    return {
        'categories': [
            {'category': cat, 'count': count, 'percentage': round(count / total * 100, 2) if total > 0 else 0}
            for cat, count in category_counts
        ],
        'total': total
    }

@router.get("/frequency")
async def get_frequency_insights(
    username: str,
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get email frequency patterns"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get emails with dates
    emails = db.query(EmailMetadata.date_received).filter(
        EmailMetadata.account_id == account_id
    ).all()
    
    if not emails:
        return {
            'daily_average': 0,
            'hourly_distribution': {},
            'weekday_distribution': {}
        }
    
    dates = [e[0] for e in emails if e[0]]
    
    # Daily average
    unique_days = len(set(d.date() for d in dates))
    daily_avg = len(dates) / max(unique_days, 1)
    
    # Hourly distribution
    hourly_counts = Counter(d.hour for d in dates)
    
    # Weekday distribution (ordered Monday through Sunday)
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_counts = Counter(weekday_names[d.weekday()] for d in dates)
    # Ensure weekday distribution is ordered (Monday through Sunday)
    ordered_weekday_dist = {day: weekday_counts.get(day, 0) for day in weekday_names}
    
    return {
        'daily_average': round(daily_avg, 2),
        'total_emails': len(dates),
        'unique_days': unique_days,
        'peak_hour': max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None,
        'hourly_distribution': dict(hourly_counts),
        'weekday_distribution': ordered_weekday_dist
    }

@router.get("/frequency/yearly")
async def get_yearly_frequency_insights(
    username: str,
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get yearly frequency patterns and year-over-year comparison"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get emails with dates
    emails = db.query(EmailMetadata.date_received).filter(
        EmailMetadata.account_id == account_id
    ).all()
    
    if not emails:
        return {
            'years': [],
            'yearly_totals': {},
            'yearly_averages': {},
            'year_over_year': []
        }
    
    dates = [e[0] for e in emails if e[0]]
    
    # Group by year
    yearly_counts = Counter(d.year for d in dates)
    yearly_dates = {}
    for d in dates:
        year = d.year
        if year not in yearly_dates:
            yearly_dates[year] = []
        yearly_dates[year].append(d)
    
    # Calculate yearly statistics
    yearly_stats = {}
    for year, year_dates in yearly_dates.items():
        unique_days = len(set(d.date() for d in year_dates))
        total_emails = len(year_dates)
        daily_avg = total_emails / max(unique_days, 1)
        
        # Monthly distribution
        monthly_counts = Counter(d.month for d in year_dates)
        monthly_dist = {month: monthly_counts.get(month, 0) for month in range(1, 13)}
        
        # Peak month
        peak_month = max(monthly_counts.items(), key=lambda x: x[1])[0] if monthly_counts else None
        
        yearly_stats[year] = {
            'total_emails': total_emails,
            'unique_days': unique_days,
            'daily_average': round(daily_avg, 2),
            'monthly_distribution': monthly_dist,
            'peak_month': peak_month,
            'months_with_data': len([m for m in monthly_dist.values() if m > 0])
        }
    
    # Year-over-year comparison
    years = sorted(yearly_counts.keys())
    year_over_year = []
    for i, year in enumerate(years):
        prev_year = years[i - 1] if i > 0 else None
        change = None
        change_percent = None
        if prev_year and prev_year in yearly_stats:
            current_total = yearly_stats[year]['total_emails']
            prev_total = yearly_stats[prev_year]['total_emails']
            change = current_total - prev_total
            change_percent = round((change / prev_total * 100), 2) if prev_total > 0 else None
        
        year_over_year.append({
            'year': year,
            'total_emails': yearly_stats[year]['total_emails'],
            'daily_average': yearly_stats[year]['daily_average'],
            'change_from_previous': change,
            'change_percent': change_percent
        })
    
    return {
        'years': years,
        'yearly_totals': {year: stats['total_emails'] for year, stats in yearly_stats.items()},
        'yearly_averages': {year: stats['daily_average'] for year, stats in yearly_stats.items()},
        'yearly_stats': yearly_stats,
        'year_over_year': year_over_year
    }

@router.get("/processed-ranges")
async def get_processed_ranges(
    username: str,
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get processed date ranges for an account"""
    import logging
    logger = logging.getLogger(__name__)
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    ranges = db.query(ProcessedDateRange).filter(
        ProcessedDateRange.account_id == account_id
    ).order_by(ProcessedDateRange.start_date).all()
    
    logger.info(f"Found {len(ranges)} processed date ranges for account {account_id} (username: {username})")
    print(f"[PRINT] Found {len(ranges)} processed date ranges for account {account_id} (username: {username})")
    if ranges:
        for r in ranges[:5]:  # Log first 5 ranges
            logger.info(f"  Range: {r.start_date.date()} to {r.end_date.date()}, {r.emails_count} emails")
            print(f"[PRINT]   Range: {r.start_date.date()} to {r.end_date.date()}, {r.emails_count} emails")
    
    result = [
        {
            'start_date': r.start_date.isoformat(),
            'end_date': r.end_date.isoformat(),
            'emails_count': r.emails_count,
            'processed_at': r.processed_at.isoformat()
        }
        for r in ranges
    ]
    
    # If no ranges exist but emails do, try to reconstruct from email metadata
    if len(ranges) == 0:
        email_count = db.query(EmailMetadata).filter(
            EmailMetadata.account_id == account_id
        ).count()
        
        if email_count > 0:
            logger.info(f"No processed ranges found, but {email_count} emails exist. Attempting to reconstruct ranges from email metadata.")
            print(f"[PRINT] No processed ranges found, but {email_count} emails exist. Attempting to reconstruct ranges from email metadata.")
            
            # Get min and max dates from emails
            min_max = db.query(
                func.min(EmailMetadata.date_received).label('min_date'),
                func.max(EmailMetadata.date_received).label('max_date')
            ).filter(
                EmailMetadata.account_id == account_id
            ).first()
            
            if min_max and min_max.min_date and min_max.max_date:
                # Create a single range covering all emails
                # Round to start of day for min, end of day for max
                min_date = min_max.min_date.replace(hour=0, minute=0, second=0, microsecond=0)
                max_date = min_max.max_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # Check if range already exists (shouldn't, but just in case)
                existing = db.query(ProcessedDateRange).filter(
                    ProcessedDateRange.account_id == account_id,
                    ProcessedDateRange.start_date == min_date,
                    ProcessedDateRange.end_date == max_date
                ).first()
                
                if not existing:
                    logger.info(f"Creating reconstructed range: {min_date} to {max_date} with {email_count} emails")
                    print(f"[PRINT] Creating reconstructed range: {min_date} to {max_date} with {email_count} emails")
                    
                    new_range = ProcessedDateRange(
                        account_id=account_id,
                        start_date=min_date,
                        end_date=max_date,
                        emails_count=email_count,
                        processed_at=datetime.utcnow()
                    )
                    db.add(new_range)
                    try:
                        db.commit()
                        logger.info(f"Successfully created reconstructed processed date range")
                        print(f"[PRINT] Successfully created reconstructed processed date range")
                        
                        # Return the newly created range
                        result = [{
                            'start_date': new_range.start_date.isoformat(),
                            'end_date': new_range.end_date.isoformat(),
                            'emails_count': new_range.emails_count,
                            'processed_at': new_range.processed_at.isoformat()
                        }]
                    except Exception as e:
                        logger.error(f"Failed to create reconstructed range: {e}", exc_info=True)
                        print(f"[PRINT] Failed to create reconstructed range: {e}")
                        db.rollback()
    
    return result

@router.get("/processed-ranges/gaps")
async def get_processed_range_gaps(
    username: str,
    account_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get unprocessed date range gaps for an account"""
    from app.date_tracker import DateTracker
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Use account creation date as default start, or today as default end
    from datetime import datetime, timedelta
    if not start_date:
        # Default to the earliest processed range start, or account creation, or 5 years ago
        # This ensures we find all gaps, including those before account creation
        earliest_processed = db.query(ProcessedDateRange).filter(
            ProcessedDateRange.account_id == account_id
        ).order_by(ProcessedDateRange.start_date).first()
        
        if earliest_processed:
            # Start from the beginning of the earliest processed range
            start_date = earliest_processed.start_date
        elif hasattr(account, 'created_at') and account.created_at:
            account_created = account.created_at
            # Go back a bit before account creation to catch any gaps
            start_date = account_created - timedelta(days=30)
        else:
            # No creation date, default to 5 years ago
            start_date = datetime.utcnow() - timedelta(days=1825)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get gaps using DateTracker
    date_tracker = DateTracker(db, account_id)
    gaps = date_tracker.get_unprocessed_ranges(start_date, end_date)
    
    # Filter out gaps that are in the future or have invalid dates
    now = datetime.utcnow()
    filtered_gaps = []
    for gap_start, gap_end in gaps:
        # Skip gaps that start in the future
        if gap_start > now:
            continue
        # Clamp end_date to now if it's in the future
        if gap_end > now:
            gap_end = now
        # Skip gaps where start >= end (invalid or zero-length)
        if gap_start >= gap_end:
            continue
        # Only include gaps that span at least one full day
        # Use date comparison to ensure we're looking at full days, not just hours
        gap_start_date = gap_start.date()
        gap_end_date = gap_end.date()
        if gap_end_date <= gap_start_date:
            continue
        # Calculate days using date difference
        days = (gap_end_date - gap_start_date).days + 1
        if days < 1:
            continue
        filtered_gaps.append((gap_start, gap_end))
    
    return [
        {
            'start_date': gap_start.isoformat(),
            'end_date': gap_end.isoformat(),
            'days': (gap_end.date() - gap_start.date()).days + 1
        }
        for gap_start, gap_end in filtered_gaps
    ]

