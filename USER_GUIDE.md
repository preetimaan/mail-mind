# Mail Mind User Guide

Welcome to Mail Mind! This guide will help you understand and use the dashboard to gain insights into your email patterns.

## Quick Start

### Setting Up a New User Account

**Good news:** There's no separate "create user account" step! User accounts are created automatically.

**Process:**
1. Open the dashboard: `http://localhost:3000`
2. Enter a new username (one you haven't used before)
3. Add your first email account (see below)
4. **The user account is created automatically** when you add the first email account

**Example:**
- Username: `john_doe` (first time)
- Add Gmail account: `john@gmail.com`
- → User account "john_doe" is automatically created
- → Email account "john@gmail.com" is added to "john_doe"

**Important:**
- Usernames must be unique (each username = one user account)
- Use the same username for all email accounts you want grouped together
- Different usernames = separate user accounts with separate data

### Adding Your First Email Account

When you add your first email account, the user account is created automatically.

**Option A: Gmail (Recommended)**
1. Click "Add Account" button
2. Select "Gmail"
3. You'll be redirected to Google to authorize
4. Sign in and grant permissions
5. You'll be redirected back to the dashboard
6. Account appears automatically

**Option B: Yahoo**
1. Generate app-specific password from [Yahoo Account Security](https://login.yahoo.com/account/security)
2. Click "Add Account" button
3. Select "Yahoo"
4. Enter your email and app-specific password
5. Click "Add Account"
6. Account appears automatically

**Result:**
- ✅ User account is created automatically (username you entered)
- ✅ Email account is added to your user account
- ✅ You can now analyze emails!

### Adding Additional Email Accounts

**If you already have a user account** (you've added at least one email account):

1. **Enter your existing username** in the dashboard
2. **Click "Add Account"** button
3. Follow the same steps as above (Gmail or Yahoo)

**You can add multiple email accounts to the same username:**
- All accounts with the same username are grouped together
- Each account's data is kept separate
- You can switch between accounts using the account selector

### Start Analyzing

1. Select your email account from the dropdown
2. Choose a date range to analyze (e.g., last 30 days, last year)
3. Click "Analyze" and watch the progress!

---

## Getting Started

### Understanding User Accounts vs Email Accounts

**Important:** Mail Mind uses a simple username system - there's no separate "user account" creation step!

- **Username**: A name you choose to group your email accounts together (e.g., "john_doe", "work", "personal")
- **User Account**: Created automatically when you add your first email account
- **Email Account**: Your actual Gmail or Yahoo account that you want to analyze

**How it works:**
1. You enter a username in the dashboard
2. When you add your first email account, Mail Mind automatically creates your user account
3. All email accounts added with the same username are grouped together
4. You can add multiple email accounts to the same username

---

## Understanding Your Dashboard

The dashboard is organized into tabs for easy navigation. Here's what each section shows:

### 📊 Summary Statistics

**What you'll see:**
- **Total Accounts**: How many email accounts you've added
- **Total Emails**: Total emails analyzed across all accounts
- **Total Senders**: Number of unique people/organizations emailing you
- **Account-specific stats**: Breakdown for the currently selected account

**What it means:**
- Quick overview of your email volume
- Helps you understand the scale of your email data
- Shows how much analysis has been completed

---

### 👥 Top Senders

**What you'll see:**
- Bar chart showing your top 10 email senders
- List of top email domains (e.g., gmail.com, company.com)
- Copy buttons to easily copy sender email addresses

**What it means:**
- Identifies who emails you most frequently
- Helps spot important contacts vs. automated emails
- Domain analysis shows which organizations email you most

**Tips:**
- Click the copy icon next to any sender to copy their email
- Use "Copy All" to copy all top senders at once
- Toggle "Show All Senders" to see beyond the top 10

**Example:**
- If "noreply@amazon.com" is at the top → You get many Amazon notifications
- If a colleague's name appears → They're a frequent contact

---

### 📁 Email Categories

**What you'll see:**
- Pie chart showing how your emails are categorized:
  - **Notifications**: System alerts, confirmations, receipts
  - **Newsletters**: Marketing emails, digests, subscriptions
  - **Social**: Emails from social media platforms
  - **Shopping**: Order confirmations, shipping updates, e-commerce
  - **Work**: Meeting invites, project updates, work-related
  - **Personal**: Direct emails from people (not automated)
  - **Other**: Everything else

**What it means:**
- Shows the breakdown of your email types
- Helps you understand if you're getting mostly automated emails vs. personal
- Percentage shows what portion of your inbox each category represents

**Tips:**
- High "Newsletters" percentage? → Consider unsubscribing from unused subscriptions
- High "Work" percentage? → Work-heavy email usage
- High "Personal" percentage? → Lots of direct communication

---

### ⏰ Email Frequency

**What you'll see:**
- **Summary Stats**:
  - Daily average emails
  - Total emails analyzed
  - Peak hour (when you receive most emails)
- **Hourly Chart**: Email volume by hour of day
- **Weekday Chart**: Email volume by day of week
- **Yearly Trends**: Year-over-year comparison (if you have multi-year data)

**What it means:**
- **Daily Average**: Your typical email volume
- **Peak Hour**: Best time to check email (when most arrive)
- **Hourly Pattern**: Shows if emails come throughout the day or in bursts
- **Weekday Pattern**: Shows if weekends are quieter or work emails cluster on weekdays

**Tips:**
- Peak hour at 9 AM? → Check email in the morning
- High weekday, low weekend? → Work-related email pattern
- Even distribution? → Consistent email flow throughout

---

### 📅 Processed Date Ranges

**What you'll see:**
- Visual timeline chart showing which months are fully processed
  - Green = Month is fully analyzed
  - Red = Month has gaps or hasn't been analyzed
- Table showing all processed date ranges with email counts

**What it means:**
- Shows which date ranges have already been analyzed
- **Smart feature**: The system won't re-analyze dates you've already processed
- If you analyze overlapping dates, it only processes the new/unprocessed parts
- Helps you track what's been analyzed

**Example:**
- If January 2024 is already processed, analyzing "Jan 15 - Feb 15" will only process February 1-15
- Saves time and prevents duplicate work

---

### 📋 Recent Analysis Runs

**What you'll see:**
- List of your most recent analysis jobs (5 at a time)
- For each run:
  - Date range analyzed
  - Status (pending, processing, completed, failed, cancelled)
  - Number of emails processed
  - Error messages (if failed)
- "Load More" button to see older runs
- Failed runs grouped together with "Retry All" option

**What it means:**
- Tracks your analysis history
- Shows job status in real-time with progress updates
- Status badges are color-coded for quick recognition
- Easy retry for failed analyses

**Status Colors:**
- 🟡 Yellow = Waiting to start
- 🔵 Blue = Currently processing
- 🟢 Green = Completed successfully
- 🔴 Red = Failed (with error message)
- ⚫ Gray = Cancelled by you

---

### 🔍 Analyzing Your Emails

**How to analyze:**
1. Select your email account from the dropdown
2. Choose a date range:
   - Pick start date (when to begin)
   - Pick end date (when to end)
   - The system can help fill gaps automatically
3. Click "Analyze"
4. Watch the progress bar: "Processing 150/500 emails..."
5. Results appear automatically when complete!

**Features:**
- **Real-time Progress**: See exactly how many emails are being processed
- **Stop Button**: Always visible in the header - cancel anytime safely
- **Automatic Revert**: If you cancel, all changes are automatically undone
- **Smart Processing**: Only processes dates you haven't analyzed yet

**How long does it take?**
- 100 emails: ~10-30 seconds
- 1,000 emails: ~2-5 minutes
- 10,000+ emails: 10+ minutes
- Progress bar shows real-time updates

---

## Managing Your Accounts

### Setting Up a New User Account

**How to create a new user account:**

There's no separate "create user account" step! User accounts are created automatically.

**Process:**
1. Open the dashboard at `http://localhost:3000`
2. Enter a new username (one you haven't used before)
3. Add your first email account (see below)
4. **The user account is created automatically** when you add the first email account

**Example:**
- Username: `john_doe` (first time)
- Add Gmail account: `john@gmail.com`
- → User account "john_doe" is automatically created
- → Email account "john@gmail.com" is added to "john_doe"

**Important:**
- Usernames must be unique (each username = one user account)
- Use the same username for all email accounts you want grouped together
- Different usernames = separate user accounts with separate data

### Adding a New Email Account to an Existing User

**If you already have a user account** (you've added at least one email account before):

1. **Enter your existing username** in the dashboard
2. **Click "Add Account"** button
3. Follow the steps below to add Gmail or Yahoo

**If this is your first email account:**
- The user account will be created automatically when you add the email account

### Understanding What You're Adding

**What You're Adding:**
- Your **email account** (Gmail or Yahoo) that you want to analyze
- This is different from a "developer account" (Google Cloud Project)
- You're connecting YOUR email to Mail Mind, not setting up developer credentials

**Important:**
- Each email account you add is separate
- You can add multiple email accounts to the same username
- Each account's data is kept separate
- You're not sharing accounts with other users

---

### Adding a Gmail Account

#### Option A: Via Dashboard UI (Recommended)

1. Click "Add Account" button
2. Select "Gmail"
3. You'll be redirected to Google to authorize access
4. Sign in with your Google account
5. Grant permissions to Mail Mind
6. You'll be redirected back to the dashboard
7. Account appears automatically once added

**What happens:**
- This uses OAuth (secure, no password needed)
- You're giving Mail Mind permission to read YOUR emails (read-only)
- The developer/admin must have set up Google Cloud Project first (one-time setup)
- Your OAuth tokens are encrypted and stored securely

**Gmail Account Requirements:**
- **2-Step Verification** must be enabled on your Gmail account
- The app only requests **read-only** access to your emails
- You can revoke access anytime at [Google Account Security](https://myaccount.google.com/permissions)

#### Option B: Via API (Advanced)

If you prefer to add accounts via API, see the [Adding Accounts via API](#adding-accounts-via-api) section below.

---

### Adding a Yahoo Account

#### Option A: Via Dashboard UI (Recommended)

**Before you start:** You need to generate an app-specific password first.

**Step 1: Generate App-Specific Password**

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

**Step 2: Add Account in Dashboard**

1. Open Mail Mind dashboard
2. Click "Add Account" button
3. Select "Yahoo"
4. Enter your email address
5. Enter your app-specific password (16 characters, no spaces)
6. Click "Add Account"
7. Account is added automatically

**Yahoo Account Requirements:**
- ✅ **2-Step Verification** must be enabled
- ✅ **App-specific password** must be generated (not your regular password)
- ✅ IMAP access is enabled by default for Yahoo Mail

#### Option B: Via API (Advanced)

If you prefer to add accounts via API, see the [Adding Accounts via API](#adding-accounts-via-api) section below.

---

### Adding Accounts via API

If you prefer to add accounts programmatically or via command line, you can use the API.

#### API Endpoint

```
POST http://localhost:8000/api/emails/accounts
```

#### Request Body

```json
{
  "username": "string",
  "provider": "gmail" | "yahoo",
  "email": "string",
  "credentials": "string (JSON)"
}
```

#### Gmail Example (using curl)

**First, get OAuth tokens** (see helper script method below), then:

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

**Getting Gmail OAuth Tokens:**

**Option 1: Using Helper Script (Recommended)**

```bash
cd backend
pip install google-auth-oauthlib google-auth-httplib2
python get_gmail_tokens.py
```

Follow the prompts:
1. Enter Client ID and Client Secret (from developer's `.env` file)
2. Open the authorization URL in your browser
3. Sign in and grant permissions
4. You'll see a "Not Found" error - **this is normal!**
5. Copy the URL from your browser's address bar
6. Paste it into the script
7. Get your credentials JSON - use this in the API call above

**Option 2: Using Google OAuth Playground**

1. Go to [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
2. Click the gear icon (⚙️) in top right
3. Check **"Use your own OAuth credentials"**
4. Enter **Client ID** and **Client Secret** (from developer)
5. In left panel, find **"Gmail API v1"**
6. Select **"https://www.googleapis.com/auth/gmail.readonly"**
7. Click **"Authorize APIs"**
8. Sign in and grant permissions
9. Click **"Exchange authorization code for tokens"**
10. Copy the tokens and format as JSON (see example above)

#### Yahoo Example (using curl)

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

#### Verify Account Was Added

```bash
curl "http://localhost:8000/api/emails/accounts?username=your_username"
```

---

### Deleting an Account

1. Click "Delete Account" button
2. Select the account you want to remove
3. Confirm deletion
4. All data for that account is removed

**Note:** This permanently deletes:
- The account connection
- All stored email metadata for that account
- All analysis results for that account

---

## Tips & Best Practices

### Understanding Your Results

**High Newsletter Percentage?**
- Consider unsubscribing from unused subscriptions
- Use email filters to organize newsletters

**One Sender Dominating?**
- Check if it's important (colleague) or spam
- Consider filtering if it's noise

**Low Personal Email?**
- Most emails are automated/notifications
- Consider if you need to reduce subscriptions

**Many Processed Ranges?**
- System is working efficiently
- Won't re-process the same dates
- Safe to re-run analysis on same ranges

### Getting the Most Out of Mail Mind

1. **Start Small**: Analyze a recent date range first (e.g., last 30 days)
2. **Expand Gradually**: Once comfortable, analyze longer ranges
3. **Compare Accounts**: Add multiple accounts to see differences
4. **Track Trends**: Analyze different time periods to see how patterns change
5. **Use Insights**: Take action based on what you learn (unsubscribe, filter, organize)

---

## Common Questions

**Q: Why do I see 0 emails?**
- You haven't analyzed any date ranges yet
- Click "Analyze" to process emails

**Q: Why are some categories missing?**
- Categories only appear if you have emails in that category
- Empty categories don't show in the pie chart

**Q: Can I analyze the same dates twice?**
- Yes! But it only processes new/unprocessed emails
- Processed ranges prevent duplicate work
- Safe to re-run - won't waste time or resources

**Q: What if analysis fails?**
- Check the error message (displayed in the UI)
- Failed runs are grouped together with a "Retry All" button
- Common issues: Invalid credentials, network problems, API limits
- Individual retry available for each failed run

**Q: Can I cancel a running analysis?**
- Yes! Use the "Stop" button (always visible in the header)
- Canceling automatically reverts all changes made during that analysis
- Safe to cancel at any time - no data corruption

**Q: How do I know which dates need analysis?**
- Check the Processed Date Ranges section
- Red months in the timeline chart indicate gaps
- The system can auto-fill date ranges to cover gaps

**Q: Is my data secure?**
- Yes! All data is stored locally on your computer
- Email metadata is encrypted
- No data is sent to external servers (except to fetch emails from Gmail/Yahoo)

**Q: Can I use multiple accounts?**
- Yes! Add as many email accounts as you want
- Switch between accounts using the account selector
- Each account's data is kept separate

**Q: What's the difference between a "developer account" and my email account?**
- **Developer Account** (Google Cloud Project): Set up once by the developer/admin to enable Gmail API access. You don't need to worry about this - it's already configured.
- **Your Email Account**: The Gmail or Yahoo account YOU add to analyze YOUR emails. This is what you add using the "Add Account" button.
- **You only need to add your email accounts** - the developer account is already set up!

---

## Troubleshooting

### Account Setup Issues

#### Gmail Account Issues

**"Invalid credentials" error**
- Your OAuth tokens may have expired
- **Solution**: Remove the account and add it again via dashboard
- The OAuth flow will get fresh tokens

**"Access blocked: This app's request is invalid"**
- The developer may need to add your email as a test user
- **Solution**: Contact the developer/admin to add your Gmail to the OAuth consent screen test users

**"Not Found" error after granting Gmail permissions**
- This is normal if using the helper script method
- **Solution**: Copy the URL from your browser's address bar and paste it into the script

**"Gmail API has not been used in project X before or it is disabled"**
- The developer hasn't enabled Gmail API yet
- **Solution**: Contact the developer/admin to enable Gmail API in Google Cloud Console

#### Yahoo Account Issues

**"Invalid credentials" or "Login failed"**
- **Check**: Are you using an **app-specific password** (not your regular password)?
- **Solution**: Generate a new app-specific password from Yahoo Account Security
- **Check**: Remove any spaces from the password when copying

**"IMAP access denied"**
- **Check**: Is 2-Step Verification enabled?
- **Solution**: Enable 2-Step Verification, then generate app password

**"Connection timeout"**
- **Check**: Firewall or network blocking IMAP port 993
- **Solution**: Ensure port 993 (IMAP SSL) is not blocked

**"Too many login attempts"**
- **Solution**: Wait 15-30 minutes, then try again
- **Check**: Make sure you're using the correct app-specific password

### Analysis Issues

#### Analysis Not Starting
- Check that your account credentials are valid
- Make sure the backend server is running
- Try refreshing the page

#### Analysis Failing
- Check error message in the UI
- Verify account credentials are correct
- For Gmail: Make sure OAuth authorization is valid (try removing and re-adding account)
- For Yahoo: Make sure you're using an app-specific password (not your regular password)
- Check that your account appears in the account selector

#### No Data Showing
- Make sure you've completed at least one analysis
- Check that the date range you analyzed contains emails
- Try analyzing a different date range
- Verify your account is selected in the account selector

#### Slow Performance
- Large date ranges take longer to process
- Check the progress bar for real-time updates
- Be patient - the system processes emails efficiently
- 10,000+ emails can take 10+ minutes

### General Issues

#### "User not found"
- The username will be created automatically on first account add
- **Solution**: Use the same username for all accounts you want to group together

#### Account added but analysis fails
- **Check**: Verify credentials are correct
- **Solution**: Delete and re-add the account with fresh credentials
- For Gmail: Re-run OAuth flow to get new tokens
- For Yahoo: Generate a new app-specific password

---

## Next Steps

After viewing your insights:

1. **Identify Patterns**: Notice trends in senders, categories, frequency
2. **Take Action**: Unsubscribe, filter, or organize based on insights
3. **Analyze More**: Process different date ranges to see trends over time
4. **Compare Accounts**: Add multiple accounts to see differences
5. **Track Changes**: Re-analyze periodically to see how patterns evolve

---

## Need Help?

- Check the [README.md](README.md) for setup instructions
- Review the [ROADMAP.md](ROADMAP.md) for upcoming features
- Make sure your backend server is running on port 8000
- Check browser console for any error messages

Happy analyzing! 📧✨

