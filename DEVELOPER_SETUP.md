# Developer Setup Guide

This guide is for **developers/admins** setting up Mail Mind. For end users adding email accounts, see [USER_GUIDE.md](USER_GUIDE.md).

## Table of Contents

- [Returning Developer Quick Start](#returning-developer-quick-start)
- [First-Time Setup](#first-time-setup)
  - [Environment Setup](#environment-setup)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Google Cloud Project Setup](#google-cloud-project-setup) (required for Gmail)
- [Understanding Developer vs User Accounts](#understanding-developer-vs-user-accounts)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

---

## Returning Developer Quick Start

If you've already completed the first-time setup, use this to get running quickly:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

```bash
# Terminal 2: Frontend
cd frontend
npm run dev
```

**Verify:**
- Backend: http://localhost:8000/docs (Swagger UI)
- Frontend: http://localhost:3000

**Need to reconfigure?** Check your `.env` file has:
- `ENCRYPTION_KEY` - generated encryption key
- `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` - from Google Cloud Console (for Gmail support)

---

## First-Time Setup

### Environment Setup

1. **Copy the example environment file:**
   ```bash
   cd backend
   cp env.example .env
   ```

2. **Generate encryption key:**
   ```bash
   python generate_key.py
   # Copy the output to .env as ENCRYPTION_KEY=...
   ```

3. **Edit `.env` and configure:**
   - `ENCRYPTION_KEY` - From step above (required)
   - `CORS_ORIGINS` - Default: `http://localhost:3000,http://localhost:5173`
   - `DATABASE_URL` - Default: `sqlite:///./data/mailmind.db`
   
   **After Google Cloud setup (for Gmail), add:**
   - `GMAIL_CLIENT_ID` - From Google Cloud Console
   - `GMAIL_CLIENT_SECRET` - From Google Cloud Console

   **Optional (for AI-powered category suggestions):**
   - `OPENAI_API_KEY` - OpenAI API key; if set, "Suggest categories" uses gpt-4o-mini. If not set, rule-based keyword suggestions are used.

**⚠️ Never commit `.env` to git!** It's already in `.gitignore`

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
# Optional: for AI category suggestions (otherwise rule-based suggestions are used)
# pip install openai
mkdir -p data
uvicorn main:app --reload
```

✅ Backend should be running on `http://localhost:8000`

**Or use the setup script:**
```bash
cd backend
./setup.sh
source venv/bin/activate
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

✅ Frontend should be running on `http://localhost:3000`

---

## Google Cloud Project Setup

**Required for Gmail support.** Yahoo Mail doesn't require this - users just need an app-specific password.

### Why is this needed?

Gmail requires OAuth 2.0 authentication via a Google Cloud Project. This is Google's security requirement for accessing the Gmail API. **Good news: It's completely FREE for personal use!**

**What's included free:**
- Project creation (unlimited)
- Gmail API usage (generous quotas)
- OAuth 2.0 credentials

**Note:** Google may show a "$300 free trial" signup - **you can skip this!** Mail Mind only needs the Always Free tier (no credit card required).

### Prerequisites

- A Google account (free)
- Access to [Google Cloud Console](https://console.cloud.google.com/)

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name (e.g., "Mail Mind")
4. Click **"Create"** and wait for project creation
5. Select your new project

### Step 2: Enable Gmail API

1. Go to **"APIs & Services"** → **"Library"**
2. Search for **"Gmail API"**
3. Click on **"Gmail API"** → Click **"Enable"**

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** → Click **"Create"**
3. Fill in the form:
   - **App name**: `Mail Mind`
   - **User support email**: Select your email
   - **Developer contact information**: Enter your email
4. Click **"Save and Continue"** through remaining steps
5. On **Test users** step: Click **"+ ADD USERS"** and add Gmail addresses that will use Mail Mind

**Note:** You can add more test users later from **"OAuth consent screen"** → **"Test users"** tab.

### Step 4: Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Configure:
   - **Application type**: Web application
   - **Name**: `Mail Mind OAuth Client`
   - **Authorized redirect URIs**: Add `http://localhost:8000/api/oauth/callback`
4. Click **"Create"**
5. **Copy the Client ID and Client Secret** from the popup

### Step 5: Add Credentials to Environment

Add to your `backend/.env` file:
```bash
GMAIL_CLIENT_ID=your-client-id-here
GMAIL_CLIENT_SECRET=your-client-secret-here
```

### Step 6: Verify Setup

1. Check `.env` has both `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET`
2. Verify Gmail API is enabled in **"APIs & Services"** → **"Dashboard"**
3. Users can now add Gmail accounts via the dashboard (see [USER_GUIDE.md](USER_GUIDE.md))

---

## Understanding Developer vs User Accounts

**These are two different things:**

| Aspect | Developer Account | User Email Account |
|--------|------------------|-------------------|
| **What** | Google Cloud Project credentials | Your Gmail/Yahoo account |
| **Who** | Developer/Admin | End User |
| **When** | Once per installation | Each email you want to analyze |
| **Storage** | `.env` file | Encrypted in database |
| **Purpose** | Identify Mail Mind app to Google | Access your specific emails |

**How they work together:**
1. Developer creates Google Cloud Project → gets Client ID/Secret (stored in `.env`)
2. User adds email via dashboard → uses developer's credentials to get their own OAuth tokens
3. User's tokens are encrypted and stored per-user in the database

**Common questions:**
- "Do I need a Google Cloud Project for each email?" → **No**, one project for the entire installation
- "Is the Client Secret my Gmail password?" → **No**, it identifies the Mail Mind app to Google

---

## Troubleshooting

### Google Cloud Setup Issues

#### "Redirect URI mismatch"
- **Check**: The redirect URI in Google Cloud Console must match exactly
- **Solution**: Ensure `http://localhost:8000/api/oauth/callback` is added (no trailing slash)

#### "Gmail API has not been used in project X before or it is disabled"
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/library)
2. Search for **"Gmail API"** → Click **"Enable"**
3. Wait 1-2 minutes for changes to propagate

#### "I can't find Test users in OAuth consent screen"
- After setup, go to **"OAuth consent screen"**
- Look for tabs at the top: **"Test users"**
- Click **"+ ADD USERS"** to add Gmail addresses

### Environment Issues

#### "Encryption key not found"
```bash
cd backend
python generate_key.py
# Copy output to .env as ENCRYPTION_KEY=...
```

#### "spaCy model not found"
```bash
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
```

### FAQ

**"Why can't users just use their Gmail password?"**  
Gmail requires OAuth 2.0 for security. It provides fine-grained permissions and can be revoked anytime.

---

## Security Notes

1. **Keep Client Secret private** - Don't share it or commit it to version control
2. **Never commit `.env`** - It's already in `.gitignore`
3. **Revoke access** if you suspect compromise:
   - Delete OAuth Client in Google Cloud Console → Create a new one
   - Update `.env` with new credentials
   - Users will need to re-authorize

### If Credentials Are Exposed

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **"APIs & Services"** → **"Credentials"**
2. Delete the exposed OAuth Client (or click **"Reset Secret"**)
3. Create a new OAuth client and update `.env`
4. Users will need to re-add their accounts

---

## Next Steps

After completing setup:

1. **Verify**: Check `.env` has `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET`
2. **Test**: Open http://localhost:3000 and try adding an account
3. **Users**: Direct users to [USER_GUIDE.md](USER_GUIDE.md) for adding their email accounts

**Note:** Yahoo Mail doesn't require Google Cloud setup - users can add Yahoo accounts directly with an app-specific password.
