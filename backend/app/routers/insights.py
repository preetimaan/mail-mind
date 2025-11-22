from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import datetime
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
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get top senders and patterns"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get sender counts
    sender_counts = db.query(
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
    ).limit(limit).all()
    
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

@router.get("/processed-ranges")
async def get_processed_ranges(
    username: str,
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get processed date ranges for an account"""
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
    
    return [
        {
            'start_date': r.start_date.isoformat(),
            'end_date': r.end_date.isoformat(),
            'emails_count': r.emails_count,
            'processed_at': r.processed_at.isoformat()
        }
        for r in ranges
    ]

