from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from app.database import get_db, User, EmailAccount
from app.encryption import EncryptionManager
from app.email_connectors.gmail import GmailConnector
from app.email_connectors.yahoo import YahooConnector

router = APIRouter()

class EmailAccountCreate(BaseModel):
    provider: str  # 'gmail' or 'yahoo'
    email: str
    credentials: str  # Encrypted credentials JSON (for Gmail) or app password (for Yahoo)
    username: str

class YahooAccountCreate(BaseModel):
    email: str
    app_password: str
    username: str

class TestConnectionRequest(BaseModel):
    provider: str
    credentials: str  # JSON string for Gmail, app password for Yahoo
    email: str

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
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return []
        
        accounts = db.query(EmailAccount).filter(EmailAccount.user_id == user.id).all()
        return accounts
    except Exception as e:
        print(f"Error listing accounts for user {username}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load accounts: {str(e)}")

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

@router.post("/accounts/yahoo", response_model=EmailAccountResponse)
async def create_yahoo_account(
    account: YahooAccountCreate,
    db: Session = Depends(get_db)
):
    """Create a new Yahoo email account connection"""
    # Get or create user
    user = db.query(User).filter(User.username == account.username).first()
    if not user:
        user = User(username=account.username)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # For Yahoo, credentials is just the app password (stored as JSON)
    credentials_json = json.dumps({"app_password": account.app_password})
    
    # Encrypt credentials
    enc_manager = EncryptionManager(user.id)
    encrypted_creds = enc_manager.encrypt(credentials_json)
    
    # Check if account already exists
    existing_account = db.query(EmailAccount).filter(
        EmailAccount.user_id == user.id,
        EmailAccount.email == account.email,
        EmailAccount.provider == "yahoo"
    ).first()
    
    if existing_account:
        # Update existing account
        existing_account.encrypted_credentials = encrypted_creds
        existing_account.is_active = True
        db.commit()
        db.refresh(existing_account)
        return existing_account
    
    # Create account
    email_account = EmailAccount(
        user_id=user.id,
        provider="yahoo",
        email=account.email,
        encrypted_credentials=encrypted_creds,
        is_active=True
    )
    db.add(email_account)
    db.commit()
    db.refresh(email_account)
    
    return email_account

@router.post("/accounts/test-connection")
async def test_connection(
    request: TestConnectionRequest,
    db: Session = Depends(get_db)
):
    """Test email account connection before saving"""
    try:
        if request.provider == "gmail":
            # For Gmail, credentials should be JSON string
            try:
                credentials_json = request.credentials
                connector = GmailConnector(credentials_json)
                # Try to fetch a small date range to test connection
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=1)
                emails = connector.fetch_emails_by_date_range(start_date, end_date, max_results=1)
                return {"success": True, "message": "Connection successful"}
            except Exception as e:
                return {"success": False, "message": f"Connection failed: {str(e)}"}
        
        elif request.provider == "yahoo":
            # For Yahoo, credentials is app password
            try:
                connector = YahooConnector(request.email, request.credentials)
                # Try to connect and fetch a small date range
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=1)
                emails = connector.fetch_emails_by_date_range(start_date, end_date, max_results=1)
                return {"success": True, "message": "Connection successful"}
            except Exception as e:
                return {"success": False, "message": f"Connection failed: {str(e)}"}
        
        else:
            return {"success": False, "message": f"Unsupported provider: {request.provider}"}
    
    except Exception as e:
        return {"success": False, "message": f"Error testing connection: {str(e)}"}

