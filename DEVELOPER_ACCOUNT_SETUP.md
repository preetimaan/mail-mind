# Developer Account Setup Guide

This guide is for **developers/admins** setting up Mail Mind. It explains how to configure the Google Cloud Project (developer account) required for Gmail API access.

**⚠️ Important:** This is different from adding user email accounts. Users add their email accounts via the dashboard - see [USER_GUIDE.md](USER_GUIDE.md) for that.

## Table of Contents

- [Understanding Developer Account vs User Email Account](#understanding-developer-account-vs-user-email-account)
- [Gmail Developer Account Setup](#gmail-developer-account-setup)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Understanding Developer Account vs User Email Account

**⚠️ IMPORTANT: These are TWO DIFFERENT things!**

### The Two Different Setups

**1. Developer Account (One-Time, Per Developer/Installation)**
- **What:** Google Cloud Project + OAuth Client ID & Secret
- **Who:** The person developing/running Mail Mind (admin/developer)
- **When:** Once, before any users can use the app
- **Purpose:** Allows Mail Mind to connect to Gmail API
- **Result:** Mail Mind can now authenticate with Gmail API (but can't access anyone's emails yet)
- **Storage:** In `.env` file (not in database)
- **Sharing:** Same credentials used by all users (app-wide)

**2. User Email Account (Per User, Per Email)**
- **What:** YOUR actual email account (Gmail or Yahoo) that you want to analyze
- **Who:** Each end user who wants to analyze their emails
- **When:** Every time a user wants to add an email account
- **Purpose:** Connect YOUR specific email account to Mail Mind
- **Result:** Mail Mind can now access and analyze THAT USER'S emails
- **Storage:** Encrypted in database (user-specific)
- **Sharing:** Each user has their own email accounts (not shared)

### Key Differences

| Aspect | Developer Account | User Email Account |
|--------|------------------|-------------------|
| **What** | Google Cloud Project + OAuth Client ID/Secret | Your Gmail/Yahoo email account |
| **Who** | Developer/Admin (person running Mail Mind) | End User (you, analyzing your emails) |
| **Frequency** | Once per installation | Per email account you want to analyze |
| **Credentials** | Client ID + Client Secret | OAuth Tokens (Gmail) or App Password (Yahoo) |
| **Scope** | App-wide (all users share this) | User-specific (your emails only) |
| **Storage** | `.env` file | Encrypted in database |
| **Purpose** | Identify Mail Mind app to Google | Access YOUR specific emails |
| **Can Share?** | Yes (same for all users) | No (unique per user, encrypted) |
| **Required For** | Gmail only (Yahoo doesn't need this) | Both Gmail and Yahoo |

### How They Work Together

1. **Developer** creates Google Cloud Project and gets Client ID/Secret (stored in `.env`)
   - This is done ONCE per Mail Mind installation
   - All users share these credentials (they identify the Mail Mind app)
2. **User** adds their email account via dashboard or API
   - For Gmail: Uses developer's Client ID/Secret to get their own OAuth tokens
   - For Yahoo: Provides email and app-specific password
3. **User's credentials** are encrypted and stored in database (user-specific)
4. Mail Mind uses Developer's Client ID/Secret + User's tokens/password to access that user's emails

**Analogy:**
- **Developer Account** = Restaurant's business license (needed to operate, one per restaurant)
- **User Email Account** = Customer's meal order (each customer orders their own food)

**Common Confusion:**
- ❌ "Do I need a Google Cloud Project for each email account?" → **No!** One project for the entire Mail Mind installation
- ❌ "Is the Client Secret my Gmail password?" → **No!** It identifies the Mail Mind app to Google, not your email account
- ❌ "Do I need to create a project every time I add an account?" → **No!** Project is created once by developer, users just add their email accounts
- ❌ "Is my email account the same as developer account?" → **No!** Developer account = Google Cloud Project (one-time), Your email account = Your Gmail/Yahoo (per account)

---

## Gmail Developer Account Setup

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
3. Python installed (for OAuth flow script, if needed)

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
   
   **After completing OAuth setup, add:**
   - `GMAIL_CLIENT_ID` - From Google Cloud Console (Step 4)
   - `GMAIL_CLIENT_SECRET` - From Google Cloud Console (Step 4)

**⚠️ Never commit `.env` to git!** It's already in `.gitignore`

### Quick Overview

Here's what you'll do (takes about 5-10 minutes):
1. ✅ Create a Google Cloud Project
2. ✅ Enable Gmail API
3. ✅ Configure OAuth consent screen (one-time setup)
4. ✅ Create OAuth credentials (get Client ID & Secret)
5. ✅ Store credentials in `.env` file

**Ready? Let's start!**

### Step 1: Create Google Cloud Project

**Who does this:** Developer/admin setting up Mail Mind  
**When:** Once, before any users can add Gmail accounts  
**Result:** Google Cloud Project with OAuth credentials

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

**Who does this:** Developer/admin  
**When:** Once, as part of developer account setup

1. In the project dashboard, go to **"APIs & Services"** → **"Library"**
2. Search for **"Gmail API"**
3. Click on **"Gmail API"**
4. Click **"Enable"**
5. Wait for the API to be enabled

### Step 3: Configure OAuth Consent Screen

**Who does this:** Developer/admin  
**When:** Once, as part of developer account setup

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
   - Enter Gmail addresses that will use Mail Mind (users can be added later)
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
- Click the **"Test users"** tab to add Gmail addresses
- For scopes, they're not required at this stage - we'll specify them in the OAuth flow code

**Note:** The consent screen is now configured. You can add more test users later if needed by going back to **"OAuth consent screen"** → **"Test users"** tab.

### Step 4: Create OAuth 2.0 Credentials

**Who does this:** Developer/admin  
**When:** Once, as part of developer account setup  
**Result:** Client ID and Client Secret (store in `.env` file)

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
5. Click **"Create"**
6. **IMPORTANT**: A popup will appear with your credentials:
   - **Client ID**: Copy this (looks like `123456789-abc.apps.googleusercontent.com`)
   - **Client Secret**: Copy this (looks like `GOCSPX-abc123xyz`)
   - **Save both** - add them to your `.env` file!
   - Click **"OK"** to close the popup

**Add to `.env` file:**
```bash
GMAIL_CLIENT_ID=your-client-id-here
GMAIL_CLIENT_SECRET=your-client-secret-here
```

**⚠️ Security Note:** Keep your Client Secret private. Don't share it or commit it to version control.

### Step 5: Verify Setup

After completing the above steps:

1. **Verify credentials are in `.env`:**
   ```bash
   # Check that these are set:
   GMAIL_CLIENT_ID=...
   GMAIL_CLIENT_SECRET=...
   ```

2. **Test that Gmail API is enabled:**
   - Go to **"APIs & Services"** → **"Dashboard"**
   - You should see "Gmail API" in the list of enabled APIs

3. **Users can now add their Gmail accounts:**
   - Users will use the dashboard UI to add accounts
   - The OAuth flow will use your Client ID/Secret
   - See [USER_GUIDE.md](USER_GUIDE.md) for user instructions

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

#### "Why can't users just use their Gmail password?"
Gmail doesn't allow password-based access for security reasons. OAuth 2.0 is the secure, standard way to access Gmail API. It gives fine-grained permissions (read-only) and can be revoked anytime.

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
- Add Gmail addresses
- Click **"Add"**

**Alternative navigation:**
- Go to: **"APIs & Services"** → **"OAuth consent screen"**
- You should see tabs: **"Publishing status"**, **"Scopes"**, **"Test users"**, **"Summary"**
- Click each tab to access those sections

**If you still can't find it:**
- Make sure you've completed the initial consent screen setup
- Try refreshing the page
- The Test users section is only available for "External" apps (not Internal/Workspace)

### Developer-Specific Issues

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

**Alternative:**
- Direct link: `https://console.cloud.google.com/apis/api/gmail.googleapis.com/overview?project=YOUR_PROJECT_ID`
- Replace `YOUR_PROJECT_ID` with your actual project ID

**Verification:**
- Go to: **APIs & Services** → **Dashboard**
- You should see "Gmail API" in the list of enabled APIs

#### "Encryption key not found"
- **Solution**: Make sure `ENCRYPTION_KEY` is set in `.env` file
- **Generate key**: Run `python backend/generate_key.py` and add to `.env`

---

## Security Notes

1. **Keep Client Secret private** - Don't share it or commit it to version control
2. **Never commit `.env`** - It's already in `.gitignore`
3. **Revoke access** if you suspect compromise:
   - Delete OAuth Client in Google Cloud Console
   - Create a new OAuth client
   - Update `.env` with new credentials
   - Users will need to re-authorize (their tokens will stop working)

### If Credentials Are Exposed

If your OAuth Client ID/Secret are accidentally exposed or committed to git:

1. **Delete OAuth Client (Most Secure):**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to **"APIs & Services"** → **"Credentials"**
   - Find your OAuth 2.0 Client ID
   - Click the **trash icon** (Delete)
   - Confirm deletion
   - **Create a new OAuth client** following the setup guide above
   - Update `.env` file with new credentials

2. **Or Regenerate Client Secret (Less Secure):**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to **"APIs & Services"** → **"Credentials"**
   - Click on your OAuth 2.0 Client ID
   - Click **"Reset Secret"** or **"Regenerate"**
   - Update `.env` file with new secret

3. **Users will need to re-authorize:**
   - Their existing OAuth tokens will stop working
   - They'll need to add their accounts again via the dashboard

---

## Next Steps

After completing developer account setup:

1. **Verify setup:**
   - Check that `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` are in `.env`
   - Verify Gmail API is enabled in Google Cloud Console

2. **Users can now add accounts:**
   - Direct users to [USER_GUIDE.md](USER_GUIDE.md) for adding their email accounts
   - Users will use the dashboard UI to add Gmail/Yahoo accounts

3. **For Yahoo:**
   - No developer account setup needed
   - Users can add Yahoo accounts directly (see [USER_GUIDE.md](USER_GUIDE.md))

For issues or questions, check the main [README.md](README.md).

