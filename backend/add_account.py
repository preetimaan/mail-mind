#!/usr/bin/env python3
"""
Helper script to add Gmail or Yahoo account to Mail Mind.

Usage:
    python add_account.py
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:8000"

def add_gmail_account():
    """Add Gmail account using OAuth credentials"""
    print("=" * 60)
    print("Add Gmail Account to Mail Mind")
    print("=" * 60)
    print()
    
    # Get user input
    username = input("Enter your Mail Mind username: ").strip()
    if not username:
        print("❌ Username is required!")
        sys.exit(1)
    
    email = input("Enter your Gmail address: ").strip()
    if not email:
        print("❌ Gmail address is required!")
        sys.exit(1)
    
    print()
    print("Paste your credentials JSON (from get_gmail_tokens.py):")
    print("(You can paste the entire JSON object)")
    print()
    
    credentials_input = input().strip()
    if not credentials_input:
        print("❌ Credentials are required!")
        sys.exit(1)
    
    # Parse credentials JSON
    try:
        # Try to parse as JSON
        if credentials_input.startswith('{'):
            credentials_dict = json.loads(credentials_input)
        else:
            # If it's not JSON, try to load from file
            print("❌ Invalid JSON format. Please paste the JSON object.")
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)
    
    # Prepare request
    payload = {
        "username": username,
        "provider": "gmail",
        "email": email,
        "credentials": json.dumps(credentials_dict)
    }
    
    # Make API call
    print()
    print("Adding account to Mail Mind...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/emails/accounts",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            account = response.json()
            print()
            print("=" * 60)
            print("✅ Account added successfully!")
            print("=" * 60)
            print()
            print(f"Account ID: {account['id']}")
            print(f"Email: {account['email']}")
            print(f"Provider: {account['provider']}")
            print(f"Status: {'Active' if account['is_active'] else 'Inactive'}")
            print()
            print("📋 Next steps:")
            print("1. Open the dashboard: http://localhost:3000")
            print("2. Enter your username:", username)
            print("3. Select your Gmail account")
            print("4. Choose a date range and click 'Analyze'")
            print()
        else:
            print()
            print("❌ Error adding account:")
            print(f"Status: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Detail: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print()
        print("❌ Cannot connect to backend!")
        print("Make sure the backend is running:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        sys.exit(1)

def add_yahoo_account():
    """Add Yahoo account using app-specific password"""
    print("=" * 60)
    print("Add Yahoo Account to Mail Mind")
    print("=" * 60)
    print()
    
    username = input("Enter your Mail Mind username: ").strip()
    if not username:
        print("❌ Username is required!")
        sys.exit(1)
    
    email = input("Enter your Yahoo email: ").strip()
    if not email:
        print("❌ Yahoo email is required!")
        sys.exit(1)
    
    password = input("Enter your app-specific password (16 characters, no spaces): ").strip()
    if not password:
        print("❌ App-specific password is required!")
        sys.exit(1)
    
    # Prepare credentials
    credentials = {
        "email": email,
        "password": password.replace(" ", "")  # Remove any spaces
    }
    
    # Prepare request
    payload = {
        "username": username,
        "provider": "yahoo",
        "email": email,
        "credentials": json.dumps(credentials)
    }
    
    # Make API call
    print()
    print("Adding account to Mail Mind...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/emails/accounts",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            account = response.json()
            print()
            print("=" * 60)
            print("✅ Account added successfully!")
            print("=" * 60)
            print()
            print(f"Account ID: {account['id']}")
            print(f"Email: {account['email']}")
            print(f"Provider: {account['provider']}")
            print(f"Status: {'Active' if account['is_active'] else 'Inactive'}")
            print()
            print("📋 Next steps:")
            print("1. Open the dashboard: http://localhost:3000")
            print("2. Enter your username:", username)
            print("3. Select your Yahoo account")
            print("4. Choose a date range and click 'Analyze'")
            print()
        else:
            print()
            print("❌ Error adding account:")
            print(f"Status: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Detail: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print()
        print("❌ Cannot connect to backend!")
        print("Make sure the backend is running:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        sys.exit(1)

def main():
    print()
    print("Select provider:")
    print("1. Gmail (OAuth)")
    print("2. Yahoo (App-specific password)")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        add_gmail_account()
    elif choice == "2":
        add_yahoo_account()
    else:
        print("❌ Invalid choice!")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)

