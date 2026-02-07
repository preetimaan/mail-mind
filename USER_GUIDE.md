# Mail Mind User Guide

This guide helps you add email accounts and use the dashboard to gain insights into your email patterns.

**Note:** This guide is for end users. If you're setting up Mail Mind for the first time (developer/admin), see [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md).

---

## Quick Start

### 1. Add Your Email Account

**Gmail:**
1. Open the dashboard at `http://localhost:3000`
2. Enter a username (e.g., `john_doe`)
3. Click "Add Account" → Select "Gmail"
4. Sign in with Google and grant permissions
5. Account appears automatically

**Yahoo:**
1. First, generate an app-specific password from [Yahoo Account Security](https://login.yahoo.com/account/security)
2. Open the dashboard and enter a username
3. Click "Add Account" → Select "Yahoo"
4. Enter your email and app-specific password
5. Account appears automatically

### 2. Run Your First Analysis

1. Select your email account from the dropdown
2. Choose a date range (e.g., last 30 days)
3. Click "Analyze" and watch the progress
4. View insights in the organized tabs

---

## Managing Accounts

### Understanding Usernames

- **Username**: Groups your email accounts together (e.g., "john_doe", "work")
- **User account**: Created automatically when you add your first email
- **Email account**: Your actual Gmail or Yahoo account to analyze

**Tips:**
- Use the same username for all accounts you want grouped together
- Different usernames = separate data

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

### Adding a Gmail Account (Details)

1. Click "Add Account" → Select "Gmail"
2. Sign in with your Google account
3. Grant permissions to Mail Mind (read-only access)
4. You'll be redirected back - account appears automatically

**Requirements:**
- 2-Step Verification must be enabled on your Gmail account
- You can revoke access anytime at [Google Account Security](https://myaccount.google.com/permissions)

**Note:** If you see "Access blocked" error, contact your admin to add your email as a test user in Google Cloud Console.

---

### Adding a Yahoo Account (Details)

**Step 1: Generate App-Specific Password**

Yahoo requires an app-specific password (not your regular password):

1. Go to [Yahoo Account Security](https://login.yahoo.com/account/security)
2. Enable **2-Step Verification** if not already enabled
3. Scroll to **"App passwords"** → Click **"Generate app password"**
4. Select **"Mail"** as the app type, name it "Mail Mind"
5. **Copy the 16-character password** (you won't see it again!)

**Step 2: Add Account in Dashboard**

1. Click "Add Account" → Select "Yahoo"
2. Enter your email address
3. Enter the 16-character app-specific password (no spaces)
4. Click "Add Account"

**Requirements:**
- 2-Step Verification must be enabled
- Use app-specific password, not your regular password

---

### Deleting an Account

1. Click "Delete Account" button
2. Select the account to remove
3. Confirm deletion

**Note:** This permanently deletes the account, all email metadata, and analysis results for that account.

---

### Adding Accounts via API (Advanced)

For programmatic account management, use the API:

```bash
# Yahoo account
curl -X POST http://localhost:8000/api/emails/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "provider": "yahoo",
    "email": "your@yahoo.com",
    "credentials": "{\"email\":\"your@yahoo.com\",\"password\":\"your-app-password\"}"
  }'

# List accounts
curl "http://localhost:8000/api/emails/accounts?username=your_username"
```

For Gmail via API, you'll need OAuth tokens. See the backend helper script: `python backend/get_gmail_tokens.py`

---

## Common Questions

| Question | Answer |
|----------|--------|
| Why do I see 0 emails? | You haven't analyzed any date ranges yet. Click "Analyze" to process emails. |
| Why are some categories missing? | Categories only appear if you have emails in that category. |
| Can I analyze the same dates twice? | Yes! It only processes new/unprocessed emails. Safe to re-run. |
| Can I cancel a running analysis? | Yes! Use the "Stop" button. All changes are automatically reverted. |
| How do I know which dates need analysis? | Check "Processed Date Ranges" - red months indicate gaps. |
| Is my data secure? | Yes! All data is stored locally and encrypted. Only email fetching contacts external servers. |
| Can I use multiple accounts? | Yes! Add as many accounts as you want and switch between them. |

---

## Troubleshooting

### Gmail Issues

| Issue | Solution |
|-------|----------|
| "Invalid credentials" | Remove and re-add the account via dashboard |
| "Access blocked" | Contact admin to add your email as a test user |
| "Gmail API disabled" | Contact admin to enable Gmail API |

### Yahoo Issues

| Issue | Solution |
|-------|----------|
| "Invalid credentials" / "Login failed" | Use app-specific password (not regular password). Remove spaces. |
| "IMAP access denied" | Enable 2-Step Verification, then generate app password |
| "Too many login attempts" | Wait 15-30 minutes, then retry |

### Analysis Issues

| Issue | Solution |
|-------|----------|
| Analysis not starting | Check credentials are valid, backend is running |
| Analysis failing | Check error message. Try removing and re-adding account. |
| No data showing | Run an analysis first. Check date range contains emails. |
| Slow performance | Large date ranges take longer. 10,000+ emails can take 10+ minutes. |

---

## Need Help?

- **Setup issues**: See [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md)
- **General info**: See [README.md](README.md)
- **Backend not running**: Make sure `uvicorn main:app --reload` is running in the backend folder

