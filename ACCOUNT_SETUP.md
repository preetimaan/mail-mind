# Account Setup Guide

This guide explains how to add email accounts (Gmail and Yahoo) to Mail Mind using the API.

## Table of Contents

- [Understanding Developer vs User Setup](#understanding-developer-vs-user-setup)
- [Gmail Setup](#gmail-setup)
- [Yahoo Setup](#yahoo-setup)
- [Adding Accounts via API](#adding-accounts-via-api)
- [Troubleshooting](#troubleshooting)

---

## Understanding Developer vs User Setup

This section clarifies the difference between **developer setup** (Google Cloud Project) and **user setup** (email accounts).

### The Two Different Setups

**1. Developer Setup (One-Time, Per Developer)**
- **What:** Google Cloud Project + OAuth Client Credentials
- **Who:** The person developing/running Mail Mind
- **When:** Once, before anyone can use the app
- **Purpose:** Allows Mail Mind to connect to Gmail API
- **Result:** Mail Mind can now talk to Gmail API (but can't access anyone's emails yet)

**2. User Setup (Per User, Per Email Account)**
- **What:** Adding your email account to Mail Mind
- **Who:** Each end user who wants to analyze their emails
- **When:** Every time a user wants to add an email account
- **Purpose:** Connect YOUR specific Gmail account to Mail Mind
- **Result:** Mail Mind can now access THAT USER'S emails

### Key Differences

| Aspect | Developer Setup | User Setup |
|--------|----------------|------------|
| **What** | Google Cloud Project + OAuth Client | OAuth Tokens for user's Gmail |
| **Who** | Developer/Admin | End User |
| **Frequency** | Once | Per email account |
| **Credentials** | Client ID + Client Secret | Access Token + Refresh Token |
| **Scope** | App-wide (all users) | User-specific |
| **Storage** | `.env` file | Encrypted in database |
| **Purpose** | Identify Mail Mind app | Access specific user's emails |
| **Can Share?** | Yes (same for all users) | No (unique per user) |

### How They Work Together

1. **Developer** creates Google Cloud Project and gets Client ID/Secret (stored in `.env`)
2. **User** uses Developer's Client ID/Secret to get their own OAuth tokens
3. **User's tokens** are encrypted and stored in database
4. Mail Mind uses Developer's Client ID/Secret + User's tokens to access that user's emails

**Analogy:**
- Developer setup = Restaurant's business license (needed to operate)
- User setup = Customer giving permission to access their email (per-user authorization)

**Common Confusion:**
- ❌ "Do I need a Google Cloud Project for each email account?" → **No!** One project for the entire app
- ❌ "Is the Client Secret my password?" → **No!** It identifies the Mail Mind app, not your account
- ❌ "Do I need to create a project every time I add an account?" → **No!** Project is created once, you just get new tokens for each account

---

## Gmail Setup

### Why Google Cloud Project?

**Good news: It's completely FREE for personal use!** 🎉

Google Cloud Platform offers a **free tier** that includes:
- Free project creation (unlimited)
- Free Gmail API usage (generous quotas for personal use)
- Free OAuth 2.0 credentials

**Why is it needed?**
- Gmail requires OAuth 2.0 authentication to access the Gmail API
- You need a Google Cloud Project to create OAuth credentials (Client ID & Secret)
- This is Google's security requirement - you can't access Gmail API without it
- The project is just a container for your OAuth credentials, no billing required

**Cost:** $0 for personal use. You only pay if you exceed very high API quotas (unlikely for personal email analysis).

**Important: Free Trial vs Free Tier**
- Google may show you a "$300 free trial" signup - **you can skip this!**
- The free trial is optional and requires a credit card
- For Mail Mind, you only need the **Always Free tier** (no credit card needed)
- OAuth credentials work perfectly without the trial or billing enabled

**Free Tier Details (Always Free - No Trial Needed):**
- Gmail API: 1 billion quota units per day (free, no trial required)
- Each email fetch uses ~5 quota units
- That's ~200 million emails per day (way more than you'll ever need!)
- OAuth credentials: Unlimited (free, no trial required)
- Project creation: Unlimited (free, no trial required)

**When would you pay?**
- Only if you process millions of emails per day (enterprise scale)
- For personal use analyzing your own emails, you'll never hit the limits
- **No credit card required** for free tier usage

### Prerequisites

1. A Google account (free)
2. Access to [Google Cloud Console](https://console.cloud.google.com/) (free)
3. Python installed (for OAuth flow script)

### Environment Variables Setup

**Before starting, set up your environment variables:**

1. **Copy the example file:**
   ```bash
   cd backend
   cp env.example .env
   ```

2. **Generate encryption key:**
   ```bash
   python generate_key.py
   # Copy the output to .env as ENCRYPTION_KEY=...
   ```

3. **Edit `.env` and fill in:**
   - `ENCRYPTION_KEY` - From step above
   - `CORS_ORIGINS` - Default: `http://localhost:3000,http://localhost:5173`
   - `DATABASE_URL` - Default: `sqlite:///./data/mailmind.db`
   
   **For adding accounts via script (optional):**
   - `MAIL_MIND_USERNAME` - Your username
   - `GMAIL_ADDRESS` - Your Gmail
   - `GMAIL_CLIENT_ID` - From Google Cloud Console (Step 4)
   - `GMAIL_CLIENT_SECRET` - From Google Cloud Console (Step 4)
   - `GMAIL_TOKEN` - From get_gmail_tokens.py (Step 5)
   - `GMAIL_REFRESH_TOKEN` - From get_gmail_tokens.py (Step 5)

**⚠️ Never commit `.env` to git!** It's already in `.gitignore`

### Quick Overview

Here's what you'll do (takes about 5-10 minutes):
1. ✅ Create a Google Cloud Project
2. ✅ Enable Gmail API
3. ✅ Configure OAuth consent screen (one-time setup)
4. ✅ Create OAuth credentials (get Client ID & Secret)
5. ✅ Get OAuth tokens using helper script
6. ✅ Add account via API

**Ready? Let's start!**

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. If you see the **"Try Google Cloud with $300 in free credits"** screen:
   - **You can skip this!** Click **"Skip"** or look for a way to proceed without the trial
   - The free trial is optional - you don't need it for Mail Mind
   - OAuth credentials work perfectly without billing enabled
3. Click **"Select a project"** → **"New Project"**
4. Enter project name (e.g., "Mail Mind")
5. Click **"Create"**
6. Wait for project creation, then select it

**Note:** If Google requires billing to be enabled:
- Some Google Cloud features require billing even for free tier
- **You won't be charged** for Gmail API usage (it's Always Free)
- Google only charges if you use paid services or exceed free quotas
- For Mail Mind (just OAuth + Gmail API), you'll stay within free limits
- You can set up billing alerts to $0 if you're concerned

**Bottom line:** Even if billing is required, you'll pay $0 for Mail Mind usage.

### Step 2: Enable Gmail API

1. In the project dashboard, go to **"APIs & Services"** → **"Library"**
2. Search for **"Gmail API"**
3. Click on **"Gmail API"**
4. Click **"Enable"**
5. Wait for the API to be enabled

### Step 3: Configure OAuth Consent Screen

**First, you need to set up the OAuth consent screen (one-time setup):**

1. In Google Cloud Console, go to **"APIs & Services"** → **"OAuth consent screen"**
   - (Or use the left sidebar menu: **"APIs & Services"** → **"OAuth consent screen"**)
2. If this is your first time, you'll see a screen asking you to configure the consent screen:
   - Select **"External"** (unless you have a Google Workspace account)
   - Click **"Create"**
3. You'll now see a multi-step form. Fill in **Step 1: App information**:
   - **App name**: `Mail Mind` (or your choice)
   - **User support email**: Select your email from dropdown
   - **Developer contact information**: Enter your email
   - Click **"Save and Continue"** at the bottom
4. **Step 2: Scopes** (you should see this page after clicking Save and Continue):
   - You don't need to add any scopes here (we'll add them in code)
   - Just click **"Save and Continue"** to proceed
   - *(If you don't see this page, that's okay - you can skip to the next step)*
5. **Step 3: Test users** (you should see this page next):
   - Click **"+ ADD USERS"** button
   - Enter your Gmail address (the one you want to analyze)
   - Click **"Add"**
   - Click **"Save and Continue"** at the bottom
   - *(If you don't see this page, you can add test users later - see note below)*
6. **Step 4: Summary**:
   - Review the information
   - Click **"Back to Dashboard"** or **"Dashboard"**

**If you don't see Scopes or Test users pages during setup:**
- The UI might have changed or you might be on a simplified flow
- **Don't worry!** You can access these sections later from the main OAuth consent screen page
- After completing the initial setup, you'll be on the OAuth consent screen dashboard
- Look for **tabs** at the top of the page: **"Publishing status"**, **"Scopes"**, **"Test users"**, **"Summary"**
- Click the **"Test users"** tab to add your Gmail address
- For scopes, they're not required at this stage - we'll specify them in the OAuth flow code

**Note:** The consent screen is now configured. You can add more test users later if needed by going back to **"OAuth consent screen"** → **"Test users"** tab.

### Step 4: Create OAuth 2.0 Credentials

**Now create the actual OAuth credentials:**

1. Go to **"APIs & Services"** → **"Credentials"** (or click **"Credentials"** in the left sidebar)
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"OAuth client ID"** from the dropdown
4. In the **Create OAuth client ID** dialog:
   - **Application type**: Select **"Web application"**
   - **Name**: Enter `Mail Mind OAuth Client` (or your choice)
   - **Authorized redirect URIs**: Click **"+ ADD URI"** and enter:
     ```
     http://localhost:8000/api/oauth/callback
     ```
     *(Note: This endpoint will be implemented in a future update. For now, you'll use a manual OAuth flow with the helper script.)*
5. Click **"Create"**
6. **IMPORTANT**: A popup will appear with your credentials:
   - **Client ID**: Copy this (looks like `123456789-abc.apps.googleusercontent.com`)
   - **Client Secret**: Copy this (looks like `GOCSPX-abc123xyz`)
   - **Save both** - you'll need them for the next step!
   - Click **"OK"** to close the popup

**⚠️ Security Note:** Keep your Client Secret private. Don't share it or commit it to version control.

### Step 5: Get OAuth Tokens (Manual Method)

Since the OAuth callback endpoint isn't implemented yet, you'll need to manually obtain tokens using a Python script.

#### Option A: Using Helper Script (Recommended)

**Use the provided helper script** located at `backend/get_gmail_tokens.py`:

```bash
cd backend
pip install google-auth-oauthlib google-auth-httplib2
python get_gmail_tokens.py
```

**Follow these steps:**

1. **Enter your Client ID and Client Secret** when prompted (from Step 4)
2. **Open the authorization URL** shown in your browser
3. **Sign in** with your Google account
4. **Grant permissions** to Mail Mind
5. **⚠️ IMPORTANT: You'll see a "Not Found" error page - THIS IS NORMAL!**
   - The callback endpoint doesn't exist yet, but the authorization code is in the URL
   - Look at your browser's **address bar** - you'll see a URL like:
     ```
     http://localhost:8000/api/oauth/callback?code=4/0Aabc123xyz...&scope=...
     ```
6. **Copy the code from the URL:**
   - You can copy the **entire URL** and paste it into the script (it will extract the code automatically)
   - Or copy just the code part (everything after `code=` and before `&`)
   - Example: If URL is `...?code=4/0Aabc123xyz&scope=...`, copy `4/0Aabc123xyz`
7. **Paste the code** (or full URL) into the script when prompted
8. **Get your credentials JSON** - copy this for the next step!

**The script will automatically extract the code** if you paste the full URL, making it easier!

#### Option B: Using Google OAuth Playground (Alternative)

1. Go to [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
2. Click the gear icon (⚙️) in top right
3. Check **"Use your own OAuth credentials"**
4. Enter your **Client ID** and **Client Secret**
5. In left panel, find **"Gmail API v1"**
6. Select **"https://www.googleapis.com/auth/gmail.readonly"**
7. Click **"Authorize APIs"**
8. Sign in and grant permissions
9. Click **"Exchange authorization code for tokens"**
10. Copy the **refresh_token** and **access_token**
11. Format as JSON:
```json
{
  "token": "ya29.xxx...",
  "refresh_token": "1//xxx...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret",
  "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
}
```

### Step 6: Add Gmail Account via API

```bash
curl -X POST http://localhost:8000/api/emails/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "provider": "gmail",
    "email": "your@gmail.com",
    "credentials": "{\"token\":\"ya29.xxx\",\"refresh_token\":\"1//xxx\",\"token_uri\":\"https://oauth2.googleapis.com/token\",\"client_id\":\"your-client-id\",\"client_secret\":\"your-secret\",\"scopes\":[\"https://www.googleapis.com/auth/gmail.readonly\"]}"
  }'
```

**Important Notes:**
- Replace `your_username` with your Mail Mind username
- Replace `your@gmail.com` with your Gmail address
- The `credentials` field must be a **JSON string** (escaped quotes)
- The credentials will be encrypted before storage

### Gmail Account Settings

**No special settings required on your Gmail account!** The OAuth flow handles permissions. However:

- Make sure **2-Step Verification** is enabled (required for OAuth)
- The app only requests **read-only** access to your emails
- You can revoke access anytime at [Google Account Security](https://myaccount.google.com/permissions)

---

## Yahoo Setup

### Prerequisites

1. A Yahoo account
2. Access to Yahoo Account Security settings

### Step 1: Enable App-Specific Password

Yahoo requires an **app-specific password** (not your regular password) for IMAP access.

1. Go to [Yahoo Account Security](https://login.yahoo.com/account/security)
2. Sign in to your Yahoo account
3. Scroll down to **"App passwords"** section
4. Click **"Generate app password"** or **"Manage app passwords"**
5. If prompted, verify your identity
6. Select **"Mail"** as the app type
7. Enter a name (e.g., "Mail Mind")
8. Click **"Generate"**
9. **IMPORTANT**: Copy the 16-character password immediately (you won't see it again!)
   - Format: `xxxx xxxx xxxx xxxx` (remove spaces when using)

**Note**: If you don't see "App passwords" option:
- You may need to enable **2-Step Verification** first
- Go to **"Two-step verification"** and enable it
- Then return to App passwords

### Step 2: Add Yahoo Account via API

```bash
curl -X POST http://localhost:8000/api/emails/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "provider": "yahoo",
    "email": "your@yahoo.com",
    "credentials": "{\"email\":\"your@yahoo.com\",\"password\":\"xxxxxxxxxxxxxxxx\"}"
  }'
```

**Important Notes:**
- Replace `your_username` with your Mail Mind username
- Replace `your@yahoo.com` with your Yahoo email
- Replace `xxxxxxxxxxxxxxxx` with your **16-character app-specific password** (no spaces)
- The `credentials` field must be a **JSON string** (escaped quotes)

### Yahoo Account Settings

**Required Settings:**
- ✅ **2-Step Verification** must be enabled
- ✅ **App-specific password** must be generated (not your regular password)
- ✅ IMAP access is enabled by default for Yahoo Mail

**No additional IMAP settings needed** - Yahoo Mail has IMAP enabled by default.

---

## Adding Accounts via API

### API Endpoint

```
POST http://localhost:8000/api/emails/accounts
```

### Request Body

```json
{
  "username": "string",
  "provider": "gmail" | "yahoo",
  "email": "string",
  "credentials": "string (JSON)"
}
```

### Response

```json
{
  "id": 1,
  "provider": "gmail",
  "email": "user@gmail.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

### Examples

#### Gmail Example (using curl)

```bash
curl -X POST http://localhost:8000/api/emails/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "provider": "gmail",
    "email": "john@gmail.com",
    "credentials": "{\"token\":\"ya29.a0AfH6SMB...\",\"refresh_token\":\"1//0gX...\",\"token_uri\":\"https://oauth2.googleapis.com/token\",\"client_id\":\"123456.apps.googleusercontent.com\",\"client_secret\":\"GOCSPX-abc123\",\"scopes\":[\"https://www.googleapis.com/auth/gmail.readonly\"]}"
  }'
```

#### Yahoo Example (using curl)

```bash
curl -X POST http://localhost:8000/api/emails/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "provider": "yahoo",
    "email": "john@yahoo.com",
    "credentials": "{\"email\":\"john@yahoo.com\",\"password\":\"abcdabcdabcdabcd\"}"
  }'
```

#### Using Python requests

```python
import requests
import json

# Gmail
gmail_credentials = {
    "token": "ya29.xxx...",
    "refresh_token": "1//xxx...",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "your-client-id",
    "client_secret": "your-secret",
    "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
}

response = requests.post(
    "http://localhost:8000/api/emails/accounts",
    json={
        "username": "john_doe",
        "provider": "gmail",
        "email": "john@gmail.com",
        "credentials": json.dumps(gmail_credentials)
    }
)
print(response.json())

# Yahoo
yahoo_credentials = {
    "email": "john@yahoo.com",
    "password": "abcdabcdabcdabcd"  # App-specific password
}

response = requests.post(
    "http://localhost:8000/api/emails/accounts",
    json={
        "username": "john_doe",
        "provider": "yahoo",
        "email": "john@yahoo.com",
        "credentials": json.dumps(yahoo_credentials)
    }
)
print(response.json())
```

#### Using JavaScript/Fetch

```javascript
// Gmail
const gmailCredentials = {
  token: "ya29.xxx...",
  refresh_token: "1//xxx...",
  token_uri: "https://oauth2.googleapis.com/token",
  client_id: "your-client-id",
  client_secret: "your-secret",
  scopes: ["https://www.googleapis.com/auth/gmail.readonly"]
};

fetch('http://localhost:8000/api/emails/accounts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'john_doe',
    provider: 'gmail',
    email: 'john@gmail.com',
    credentials: JSON.stringify(gmailCredentials)
  })
})
.then(res => res.json())
.then(data => console.log(data));

// Yahoo
const yahooCredentials = {
  email: "john@yahoo.com",
  password: "abcdabcdabcdabcd"  // App-specific password
};

fetch('http://localhost:8000/api/emails/accounts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'john_doe',
    provider: 'yahoo',
    email: 'john@yahoo.com',
    credentials: JSON.stringify(yahooCredentials)
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

### Verify Account Was Added

```bash
curl "http://localhost:8000/api/emails/accounts?username=your_username"
```

---

## Troubleshooting

### Frequently Asked Questions

#### "Do I need to pay for Google Cloud Project?"
**No!** Google Cloud Platform is free for personal use. Creating a project, enabling APIs, and using OAuth credentials costs $0. You only pay if you exceed enterprise-scale quotas (billions of API calls per day), which is impossible for personal email analysis.

#### "I see a '$300 free trial' screen - do I need to sign up?"
**No, you can skip it!** The free trial is optional. For Mail Mind, you only need the **Always Free tier** which doesn't require:
- Credit card
- Free trial signup
- Billing account

Just skip the trial screen and proceed to create a project. OAuth credentials work perfectly without billing enabled.

#### "Why can't I just use my Gmail password?"
Gmail doesn't allow password-based access for security reasons. OAuth 2.0 is the secure, standard way to access Gmail API. It gives you fine-grained permissions (read-only) and can be revoked anytime.

#### "Can I use this without Google Cloud?"
Unfortunately, no. Google requires OAuth 2.0 credentials from a Google Cloud Project to access the Gmail API. This is a security requirement, not optional. However, it's completely free and takes just a few minutes to set up.

#### "I can't find the Scopes or Test users pages in OAuth consent screen"
**This is normal!** Google's UI may vary. Here's what to do:

**If you don't see Scopes page:**
- That's fine - scopes aren't required at setup
- We'll specify the scope (`gmail.readonly`) in the OAuth flow code
- Just proceed to the next step

**If you don't see Test users page:**
- After setting up the consent screen, go back to **"OAuth consent screen"**
- Look for tabs at the top: **"Publishing status"**, **"Scopes"**, **"Test users"**
- Click the **"Test users"** tab
- Click **"+ ADD USERS"** button
- Add your Gmail address
- Click **"Add"**

**Alternative navigation:**
- Go to: **"APIs & Services"** → **"OAuth consent screen"**
- You should see tabs: **"Publishing status"**, **"Scopes"**, **"Test users"**, **"Summary"**
- Click each tab to access those sections

**If you still can't find it:**
- Make sure you've completed the initial consent screen setup
- Try refreshing the page
- The Test users section is only available for "External" apps (not Internal/Workspace)

### Gmail Issues

#### "Invalid credentials" error
- **Check**: Token may have expired. Refresh tokens should auto-refresh, but if not:
  - Re-run the OAuth flow to get new tokens
  - Make sure `refresh_token` is included (requires `prompt='consent'`)

#### "Not Found" error after granting Gmail permissions
**This is normal!** The callback endpoint doesn't exist yet, but the authorization code is in the URL.

**What to do:**
1. **Don't close the error page** - look at your browser's address bar
2. You'll see a URL like: `http://localhost:8000/api/oauth/callback?code=4/0Aabc123xyz...`
3. **Copy the entire URL** and paste it into the script (it will extract the code automatically)
4. Or **copy just the code part**: everything after `code=` and before `&` (or end of URL)
5. The script will handle extracting the code from the URL

**Example:**
- Full URL: `http://localhost:8000/api/oauth/callback?code=4/0Aabc123xyz&scope=...`
- Code to copy: `4/0Aabc123xyz`
- Or just paste the full URL - the script will extract it!

#### "Access blocked: This app's request is invalid"
- **Check**: OAuth consent screen may need verification
- **Solution**: Add your email as a test user in OAuth consent screen
- **Or**: Publish the app (requires verification for production)

#### "Redirect URI mismatch"
- **Check**: The redirect URI in Google Cloud Console must match exactly
- **Solution**: Ensure `http://localhost:8000/api/oauth/callback` is added (no trailing slash)

#### "Scope not found"
- **Check**: Gmail API must be enabled in Google Cloud Console
- **Solution**: Enable Gmail API in APIs & Services → Library

#### "Gmail API has not been used in project X before or it is disabled"
**This error means the Gmail API isn't enabled in your Google Cloud project.**

**Quick Fix:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/library)
2. Search for **"Gmail API"**
3. Click on **"Gmail API"**
4. Click the **"Enable"** button
5. Wait 10-30 seconds for it to enable
6. Wait 1-2 minutes for changes to propagate
7. Try analyzing emails again

**Alternative:**
- Direct link: `https://console.cloud.google.com/apis/api/gmail.googleapis.com/overview?project=YOUR_PROJECT_ID`
- Replace `YOUR_PROJECT_ID` with your actual project ID

**Verification:**
- Go to: **APIs & Services** → **Dashboard**
- You should see "Gmail API" in the list of enabled APIs

#### Token expires frequently
- **Solution**: Make sure you're using `refresh_token` (not just `token`)
- The app should auto-refresh, but if issues persist, regenerate tokens

### Yahoo Issues

#### "Invalid credentials" or "Login failed"
- **Check**: Are you using an **app-specific password** (not your regular password)?
- **Solution**: Generate a new app-specific password from Yahoo Account Security
- **Check**: Remove any spaces from the password when copying

#### "IMAP access denied"
- **Check**: Is 2-Step Verification enabled?
- **Solution**: Enable 2-Step Verification, then generate app password

#### "Connection timeout"
- **Check**: Firewall or network blocking IMAP port 993
- **Solution**: Ensure port 993 (IMAP SSL) is not blocked

#### "Too many login attempts"
- **Solution**: Wait 15-30 minutes, then try again
- **Check**: Make sure you're using the correct app-specific password

### General Issues

#### "User not found"
- **Solution**: The username will be created automatically on first account add
- **Check**: Use the same username for all accounts you want to group together

#### "Encryption key not found"
- **Solution**: Make sure `ENCRYPTION_KEY` is set in `.env` file
- **Generate key**: Run `python backend/generate_key.py` and add to `.env`

#### Account added but analysis fails
- **Check**: Verify credentials are correct using the list accounts endpoint
- **Check**: Test the credentials manually (Gmail API Explorer, or IMAP connection for Yahoo)
- **Solution**: Delete and re-add the account with fresh credentials

### Testing Credentials

#### Test Gmail Credentials

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

credentials_json = '{"token":"...","refresh_token":"...","client_id":"...","client_secret":"...","token_uri":"...","scopes":[...]}'
creds_dict = json.loads(credentials_json)
creds = Credentials.from_authorized_user_info(creds_dict)

service = build('gmail', 'v1', credentials=creds)
profile = service.users().getProfile(userId='me').execute()
print(f"Email: {profile['emailAddress']}")
```

#### Test Yahoo Credentials

```python
import imaplib

email = "your@yahoo.com"
password = "your-app-password"  # 16 chars, no spaces

imap = imaplib.IMAP4_SSL("imap.mail.yahoo.com", 993)
imap.login(email, password)
print("✅ Connection successful!")
imap.logout()
```

---

## Security Notes

1. **Credentials are encrypted** before storage using user-specific encryption keys
2. **Never share** your OAuth credentials or app passwords
3. **Revoke access** if you suspect compromise:
   - Gmail: [Google Account Permissions](https://myaccount.google.com/permissions)
   - Yahoo: Regenerate app password in Account Security
4. **Use app-specific passwords** for Yahoo (never your main password)
5. **Keep encryption key secure** - if lost, all encrypted data is unrecoverable

### If Credentials Are Exposed

If your OAuth credentials or tokens are accidentally exposed or committed to git:

1. **Revoke OAuth tokens immediately:**
   - Gmail: [Google Account Permissions](https://myaccount.google.com/permissions) → Remove Mail Mind access
   - Yahoo: Regenerate app password

2. **Delete OAuth Client (Most Secure):**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to **"APIs & Services"** → **"Credentials"**
   - Find your OAuth 2.0 Client ID
   - Click the **trash icon** (Delete)
   - Confirm deletion
   - **Create a new OAuth client** following the setup guide above

3. **Or Regenerate Client Secret (Less Secure):**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to **"APIs & Services"** → **"Credentials"**
   - Click on your OAuth 2.0 Client ID
   - Click **"Reset Secret"** or **"Regenerate"**
   - Update `.env` file with new secret

4. **Get new tokens and update account**

---

## Next Steps

After adding an account:
1. Verify it appears in the dashboard (enter username, select account)
2. Run a test analysis on a small date range (e.g., last 7 days)
3. Check that insights are generated correctly

For issues or questions, check the main [README.md](README.md) or [QUICKSTART.md](QUICKSTART.md).

