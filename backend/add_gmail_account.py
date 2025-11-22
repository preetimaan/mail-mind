#!/usr/bin/env python3
"""
Script to add Gmail account to Mail Mind.
Reads credentials from environment variables for security.

Setup:
1. Copy .env.example to .env
2. Fill in your credentials in .env
3. Run: python3 add_gmail_account.py
"""

import requests
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required environment variables
USERNAME = os.getenv("MAIL_MIND_USERNAME")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_TOKEN = os.getenv("GMAIL_TOKEN")
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN")
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
GMAIL_TOKEN_URI = os.getenv("GMAIL_TOKEN_URI", "https://oauth2.googleapis.com/token")

def validate_env():
    """Validate that all required environment variables are set"""
    missing = []
    if not USERNAME:
        missing.append("MAIL_MIND_USERNAME")
    if not GMAIL_ADDRESS:
        missing.append("GMAIL_ADDRESS")
    if not GMAIL_TOKEN:
        missing.append("GMAIL_TOKEN")
    if not GMAIL_REFRESH_TOKEN:
        missing.append("GMAIL_REFRESH_TOKEN")
    if not GMAIL_CLIENT_ID:
        missing.append("GMAIL_CLIENT_ID")
    if not GMAIL_CLIENT_SECRET:
        missing.append("GMAIL_CLIENT_SECRET")
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print()
        print("📋 Setup instructions:")
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print("2. Edit .env and fill in your credentials")
        print("3. Get OAuth tokens by running: python3 get_gmail_tokens.py")
        print("4. Add the tokens to your .env file")
        return False
    return True

def get_credentials_json():
    """Build credentials JSON from environment variables"""
    return {
        "token": GMAIL_TOKEN,
        "refresh_token": GMAIL_REFRESH_TOKEN,
        "token_uri": GMAIL_TOKEN_URI,
        "client_id": GMAIL_CLIENT_ID,
        "client_secret": GMAIL_CLIENT_SECRET,
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
    }

API_URL = "http://localhost:8000/api/emails/accounts"

def main():
    # Validate environment variables
    if not validate_env():
        sys.exit(1)
    
    # Build credentials from environment
    credentials_json = get_credentials_json()
    
    # Validate credentials JSON can be serialized
    try:
        credentials_str = json.dumps(credentials_json)
        # Verify it can be parsed back
        json.loads(credentials_str)
    except Exception as e:
        print(f"❌ Error serializing credentials JSON: {e}")
        print("Please check your .env file values are correct")
        sys.exit(1)
    
    payload = {
        "username": USERNAME,
        "provider": "gmail",
        "email": GMAIL_ADDRESS,
        "credentials": credentials_str
    }
    
    print("Adding Gmail account to Mail Mind...")
    print(f"Username: {USERNAME}")
    print(f"Email: {GMAIL_ADDRESS}")
    print()
    
    try:
        # Debug: Show what we're sending (without sensitive data)
        print("Debug info:")
        print(f"  Username: {USERNAME}")
        print(f"  Email: {GMAIL_ADDRESS}")
        print(f"  Provider: gmail")
        print(f"  Credentials length: {len(credentials_str)} chars")
        print(f"  Credentials preview: {credentials_str[:50]}...")
        print()
        
        response = requests.post(API_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            account = response.json()
            print("✅ Account added successfully!")
            print()
            print(f"Account ID: {account['id']}")
            print(f"Email: {account['email']}")
            print(f"Provider: {account['provider']}")
            print()
            print("📋 Next steps:")
            print("1. Open dashboard: http://localhost:3000")
            print(f"2. Enter username: {USERNAME}")
            print("3. Select your Gmail account")
            print("4. Choose a date range and click 'Analyze'")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print()
            # Try to get error details
            try:
                error_data = response.json()
                print("Error details:")
                print(json.dumps(error_data, indent=2))
            except:
                print("Response body:")
                print(response.text[:500])  # First 500 chars
                print()
                print("💡 This might be a server error. Check backend logs for details.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend!")
        print("Make sure backend is running: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

