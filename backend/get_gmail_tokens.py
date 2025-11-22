#!/usr/bin/env python3
"""
Helper script to obtain Gmail OAuth tokens for Mail Mind.

Usage:
    python get_gmail_tokens.py

Requirements:
    pip install google-auth-oauthlib google-auth-httplib2
"""

from google_auth_oauthlib.flow import Flow
import json
import sys
from urllib.parse import urlparse, parse_qs

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
REDIRECT_URI = "http://localhost:8000/api/oauth/callback"

def extract_code_from_url(url_or_code):
    """Extract authorization code from URL or return as-is if it's already just the code"""
    # If it looks like a URL, parse it
    if url_or_code.startswith('http://') or url_or_code.startswith('https://'):
        try:
            parsed = urlparse(url_or_code)
            params = parse_qs(parsed.query)
            if 'code' in params:
                return params['code'][0]
        except Exception:
            pass
    
    # If it contains 'code=', try to extract it
    if 'code=' in url_or_code:
        try:
            # Find code= and extract until next & or end
            start = url_or_code.find('code=') + 5
            end = url_or_code.find('&', start)
            if end == -1:
                end = len(url_or_code)
            return url_or_code[start:end]
        except Exception:
            pass
    
    # Otherwise, assume it's already just the code
    return url_or_code.strip()

def main():
    print("=" * 60)
    print("Gmail OAuth Token Generator for Mail Mind")
    print("=" * 60)
    print()
    
    # Get credentials from user
    print("Enter your OAuth 2.0 credentials from Google Cloud Console:")
    print("(You can find these at: https://console.cloud.google.com/apis/credentials)")
    print()
    
    client_id = input("Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required!")
        sys.exit(1)
    
    client_secret = input("Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required!")
        sys.exit(1)
    
    print()
    print("-" * 60)
    
    # Create OAuth flow
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        # Get authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        print()
        print("Step 1: Open this URL in your browser:")
        print()
        print(authorization_url)
        print()
        print("-" * 60)
        print()
        print("Step 2: Sign in with your Google account")
        print("Step 3: Grant permissions to Mail Mind")
        print("Step 4: After authorization, you'll be redirected to a URL")
        print()
        print("⚠️  IMPORTANT: You'll see a 'Not Found' error page - THIS IS NORMAL!")
        print("   The callback endpoint doesn't exist yet, but the code is in the URL.")
        print()
        print("Step 5: Look at your browser's address bar - you'll see a URL like:")
        print("   http://localhost:8000/api/oauth/callback?code=4/0Axxx...&scope=...")
        print()
        print("Step 6: Copy ONLY the 'code' part from the URL")
        print("   Example: If URL is '...?code=4/0Aabc123xyz&scope=...'")
        print("   Copy this: 4/0Aabc123xyz")
        print()
        print("💡 Tip: The code starts after 'code=' and ends before '&' (or end of URL)")
        print()
        print("-" * 60)
        print()
        
        # Get authorization code
        user_input = input("Enter the authorization code (or full URL): ").strip()
        if not user_input:
            print("❌ Authorization code is required!")
            sys.exit(1)
        
        # Extract code from URL if user pasted the full URL
        code = extract_code_from_url(user_input)
        
        if not code:
            print("❌ Could not extract authorization code from input!")
            print("   Please paste either:")
            print("   - Just the code: 4/0Aabc123xyz...")
            print("   - Or the full URL: http://localhost:8000/api/oauth/callback?code=4/0Aabc123xyz...")
            sys.exit(1)
        
        # Exchange code for tokens
        print()
        print("Exchanging code for tokens...")
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Prepare credentials JSON
        credentials_json = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        print()
        print("=" * 60)
        print("✅ Success! Your credentials JSON:")
        print("=" * 60)
        print()
        print(json.dumps(credentials_json, indent=2))
        print()
        print("=" * 60)
        print()
        print("📋 Next steps:")
        print("1. Copy the JSON above")
        print("2. Use it in the API call to add your Gmail account:")
        print()
        print('curl -X POST http://localhost:8000/api/emails/accounts \\')
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"username":"your_username","provider":"gmail","email":"your@gmail.com","credentials":"<PASTE_JSON_HERE>"}\'')
        print()
        print("⚠️  Note: The credentials field must be a JSON string (escape quotes)")
        print("   Or use the Python/JavaScript examples from ACCOUNT_SETUP.md")
        print()
        
    except Exception as e:
        print()
        print("❌ Error:", str(e))
        print()
        print("Common issues:")
        print("- Invalid Client ID or Client Secret")
        print("- Redirect URI mismatch (should be: http://localhost:8000/api/oauth/callback)")
        print("- Gmail API not enabled in Google Cloud Console")
        print()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)

