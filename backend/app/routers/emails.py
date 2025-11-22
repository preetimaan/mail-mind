from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db, User, EmailAccount
from app.encryption import EncryptionManager

router = APIRouter()

class EmailAccountCreate(BaseModel):
    provider: str  # 'gmail' or 'yahoo'
    email: str
    credentials: str  # Encrypted credentials JSON
    username: str

class EmailAccountResponse(BaseModel):
    id: int
    provider: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/accounts", response_model=EmailAccountResponse)
async def create_email_account(
    account: EmailAccountCreate,
    db: Session = Depends(get_db)
):
    """Create a new email account connection"""
    # Get or create user
    user = db.query(User).filter(User.username == account.username).first()
    if not user:
        user = User(username=account.username)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Encrypt credentials
    enc_manager = EncryptionManager(user.id)
    encrypted_creds = enc_manager.encrypt(account.credentials)
    
    # Create account
    email_account = EmailAccount(
        user_id=user.id,
        provider=account.provider,
        email=account.email,
        encrypted_credentials=encrypted_creds,
        is_active=True
    )
    db.add(email_account)
    db.commit()
    db.refresh(email_account)
    
    return email_account

@router.get("/accounts", response_model=List[EmailAccountResponse])
async def list_email_accounts(
    username: str,
    db: Session = Depends(get_db)
):
    """List all email accounts for a user"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return []
    
    return db.query(EmailAccount).filter(EmailAccount.user_id == user.id).all()

@router.delete("/accounts/{account_id}")
async def delete_email_account(
    account_id: int,
    username: str,
    db: Session = Depends(get_db)
):
    """Delete an email account"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id,
        EmailAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account deleted"}

