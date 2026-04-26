from fastapi import APIRouter, Query, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
import time

from app.exceptions import ValidationError, ConfigurationError

from app.database import get_db, User, EmailAccount
from app.encryption import EncryptionManager
from app.email_connectors.gmail import GmailConnector

router = APIRouter()

# In-memory state storage (in production, use Redis or similar)
# Format: {state: {"username": str, "email": str, "expires_at": float}}
oauth_states: dict[str, dict] = {}

# Clean up expired states every 10 minutes
STATE_EXPIRY_MINUTES = 10

def cleanup_expired_states():
    """Remove expired OAuth states"""
    now = time.time()
    expired = [state for state, data in oauth_states.items() if data.get("expires_at", 0) < now]
    for state in expired:
        oauth_states.pop(state, None)

class OAuthAuthorizeRequest(BaseModel):
    username: str
    email: str

@router.get("/authorize")
async def authorize_oauth(
    username: str = Query(...),
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    """Generate OAuth authorization URL for Gmail"""
    cleanup_expired_states()
    
    # Validate inputs
    if not username or not email:
        raise ValidationError("Username and email are required")
    
    # Get OAuth credentials from environment
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ConfigurationError(
            "Gmail OAuth credentials not configured. Please set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env"
        )
    
    # Get redirect URI from environment or use default
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    redirect_uri = f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/oauth/callback"
    
    try:
        # Generate authorization URL
        authorization_url, state = GmailConnector.get_authorization_url(
            redirect_uri=redirect_uri,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Store state with username and email
        expires_at = time.time() + (STATE_EXPIRY_MINUTES * 60)
        oauth_states[state] = {
            "username": username,
            "email": email,
            "expires_at": expires_at
        }
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    except Exception as e:
        raise ConfigurationError(f"Failed to generate authorization URL: {str(e)}")

@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Google"""
    cleanup_expired_states()
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Handle OAuth errors
    if error:
        error_msg = f"OAuth error: {error}"
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_error={error_msg}"
        )
    
    # Validate required parameters
    if not code or not state:
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_error=Missing authorization code or state"
        )
    
    # Verify state
    state_data = oauth_states.get(state)
    if not state_data:
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_error=Invalid or expired OAuth state"
        )
    
    # Check if state expired
    if state_data.get("expires_at", 0) < time.time():
        oauth_states.pop(state, None)
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_error=OAuth state expired. Please try again."
        )
    
    username = state_data["username"]
    email = state_data["email"]
    
    # Get OAuth credentials
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_error=Server configuration error"
        )
    
    redirect_uri = f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/oauth/callback"
    
    try:
        # Exchange code for credentials
        credentials_json = GmailConnector.exchange_code_for_credentials(
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Get or create user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Check if account already exists
        existing_account = db.query(EmailAccount).filter(
            EmailAccount.user_id == user.id,
            EmailAccount.email == email,
            EmailAccount.provider == "gmail"
        ).first()
        
        if existing_account:
            # Update existing account
            enc_manager = EncryptionManager(user.id)
            encrypted_creds = enc_manager.encrypt(credentials_json)
            existing_account.encrypted_credentials = encrypted_creds
            existing_account.is_active = True
            db.commit()
        else:
            # Create new account
            enc_manager = EncryptionManager(user.id)
            encrypted_creds = enc_manager.encrypt(credentials_json)
            
            email_account = EmailAccount(
                user_id=user.id,
                provider="gmail",
                email=email,
                encrypted_credentials=encrypted_creds,
                is_active=True
            )
            db.add(email_account)
            db.commit()
        
        # Clean up state
        oauth_states.pop(state, None)
        
        # Redirect to frontend with success
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_success=1&username={username}"
        )
        
    except Exception as e:
        # Clean up state on error
        oauth_states.pop(state, None)
        error_msg = f"Failed to add account: {str(e)}"
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_error={error_msg}"
        )

