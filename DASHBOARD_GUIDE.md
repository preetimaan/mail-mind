# Mail Mind Dashboard Guide

This guide explains what each section of the Mail Mind dashboard shows, what the data means, and how it's obtained.

## Table of Contents

- [Overview](#overview)
- [Dashboard Sections](#dashboard-sections)
  - [1. Summary Statistics](#1-summary-statistics-stats-grid)
  - [2. Top Senders Chart](#2-top-senders-chart)
  - [3. Email Categories Chart](#3-email-categories-chart)
  - [4. Email Frequency Chart](#4-email-frequency-chart)
  - [5. Processed Date Ranges](#5-processed-date-ranges)
  - [6. Recent Analysis Runs](#6-recent-analysis-runs)
  - [7. Batch Analysis Section](#7-batch-analysis-section)
- [Data Sources & Technical Details](#data-sources--technical-details)
- [Understanding the Data Flow](#understanding-the-data-flow)
- [Tips for Interpreting Results](#tips-for-interpreting-results)
- [Common Questions](#common-questions)

---

## Overview

After entering your username and selecting an email account, the dashboard displays several sections with insights about your email patterns. All data is stored locally in a SQLite database and processed using NLP analysis.

**Data Flow:**
1. **Fetch**: Emails are fetched from Gmail/Yahoo APIs
2. **Store**: Metadata is stored in `EmailMetadata` table
3. **Analyze**: NLP analysis categorizes and clusters emails
4. **Display**: Insights are calculated from stored data

---

## Dashboard Sections

### 1. Summary Statistics (Stats Grid)

**Location:** Appears right after selecting an account

**What it shows:**
- **All Accounts Summary:**
  - **Total Accounts**: Number of email accounts you've added to Mail Mind
  - **Total Emails**: Total number of emails analyzed across all accounts
  - **Total Senders**: Number of unique email addresses that have sent you emails
- **Current Account Summary:**
  - **Account Emails**: Number of emails in the currently selected account
  - **Account Senders**: Number of unique senders for the selected account
  - **Processed Ranges**: Number of date ranges that have been analyzed (prevents re-processing)

**What it means:**
- Gives you a quick overview of your email volume and diversity
- Helps you understand the scale of your email data
- Shows how much analysis has been completed

**Data Source:**
- **Tables**: `EmailMetadata`, `EmailAccount`, `ProcessedDateRange`
- **Endpoint**: `/api/insights/summary`
- **Calculation**: Counts and aggregates from database

---

### 2. Top Senders Chart

**Location:** Below the summary statistics

**What it shows:**
- **Bar Chart**: Top 10 email senders by volume
  - X-axis: Sender name (or email if name unavailable)
  - Y-axis: Number of emails received
  - Each bar shows how many emails you received from that sender
- **Top Domains List**: Below the chart, shows:
  - Email domains (e.g., gmail.com, company.com)
  - Total email count per domain

**What it means:**
- Identifies who emails you most frequently
- Helps spot important contacts vs. spam/newsletters
- Domain analysis shows which organizations email you most
- Useful for understanding your communication patterns

**Example:**
- If "noreply@amazon.com" is at the top, you get many Amazon notifications
- If a colleague's name appears, they're a frequent contact

**Data Source:**
- **Table**: `EmailMetadata`
- **Endpoint**: `/api/insights/senders?account_id=X`
- **Account-Specific**: ✅ Yes, filtered by `account_id`
- **How it works**: Groups by `sender_email` and `sender_name`, counts emails per sender, orders by count

---

### 3. Email Categories Chart

**Location:** Below the Top Senders section

**What it shows:**
- **Pie Chart**: Distribution of emails by category
- **Categories:**
  - **Notifications**: System alerts, confirmations, receipts
  - **Newsletters**: Marketing emails, digests, subscriptions
  - **Social**: Emails from social media platforms
  - **Shopping**: Order confirmations, shipping updates, e-commerce
  - **Work**: Meeting invites, project updates, work-related
  - **Personal**: Direct emails from people (not automated)
  - **Other**: Everything else that doesn't fit above categories

**What it means:**
- Shows the breakdown of your email types
- Helps you understand if you're getting mostly automated emails vs. personal
- Percentage shows what portion of your inbox each category represents
- Useful for email management decisions

**Example:**
- High "Newsletters" percentage = many subscriptions to manage
- High "Work" percentage = work-heavy email usage
- High "Personal" percentage = lots of direct communication

**Data Source:**
- **Table**: `AnalysisResult` (joined with `EmailMetadata`)
- **Endpoint**: `/api/insights/categories?account_id=X`
- **Account-Specific**: ✅ Yes, filtered by `account_id`
- **How categories are determined**: During analysis phase, based on subject and sender keywords:
  - 'notifications': "notification", "alert", "reminder"
  - 'newsletters': "newsletter", "digest", "unsubscribe"
  - 'social': "facebook", "twitter", "linkedin" (in sender)
  - 'shopping': "order", "purchase", "shipping"
  - 'work': "meeting", "calendar", "team"
  - 'personal': Direct emails (not noreply, has @)
  - 'other': Everything else

---

### 4. Email Frequency Chart

**Location:** Below the Categories section

**What it shows:**
- **Summary Stats:**
  - **Daily Average**: Average number of emails per day
  - **Total Emails**: Total count analyzed
  - **Unique Days**: Number of days with email activity
  - **Peak Hour**: Hour of day when you receive most emails (24-hour format)

- **Hourly Distribution (Bar Chart):**
  - Shows email volume by hour of day (0:00 to 23:00)
  - Helps identify when you're most likely to receive emails
  - X-axis: Hours of the day
  - Y-axis: Number of emails

- **Weekday Distribution (Bar Chart):**
  - Shows email volume by day of week
  - Monday through Sunday
  - Helps identify which days are busiest

**What it means:**
- **Daily Average**: Helps you understand your email volume
- **Peak Hour**: Best time to check email (when most arrive)
- **Hourly Pattern**: Shows if you get emails throughout the day or in bursts
- **Weekday Pattern**: Shows if weekends are quieter, or if work emails cluster on weekdays

**Example:**
- Peak hour at 9:00 = most emails arrive in the morning
- High weekday volume, low weekend = work-related email pattern
- Even distribution = consistent email flow

**Data Source:**
- **Table**: `EmailMetadata`
- **Endpoint**: `/api/insights/frequency?account_id=X`
- **Account-Specific**: ✅ Yes, filtered by `account_id`
- **How it works**: Extracts date/time components from `date_received`, groups by hour and weekday, calculates averages

---

### 5. Processed Date Ranges

**Location:** Below the Batch Analysis section

**What it shows:**
- **Table** with columns:
  - **Start Date**: Beginning of analyzed date range
  - **End Date**: End of analyzed date range
  - **Emails**: Number of emails found in that range
  - **Processed**: When the analysis was completed

**What it means:**
- Shows which date ranges have already been analyzed
- **Prevents duplicate processing**: The system won't re-analyze these dates
- Helps you track what's been processed
- If you analyze overlapping dates, it only processes the new/unprocessed parts

**Example:**
- If you see "Jan 1 - Jan 31, 2024" processed, analyzing "Jan 15 - Feb 15" will only process Feb 1-15
- Saves time and API quota

**Data Source:**
- **Table**: `ProcessedDateRange`
- **Endpoint**: `/api/insights/processed-ranges?account_id=X`

---

### 6. Recent Analysis Runs

**Location:** Below Processed Ranges

**What it shows:**
- List of the 5 most recent analysis jobs
- For each run:
  - **Date Range**: Start and end dates analyzed
  - **Status**: 
    - `pending` - Queued but not started
    - `processing` - Currently analyzing
    - `completed` - Finished successfully
    - `failed` - Error occurred
  - **Emails Processed**: Number of emails analyzed (if completed)

**What it means:**
- Tracks your analysis history
- Shows job status in real-time
- Helps you see what's been analyzed and when
- Status badges are color-coded for quick recognition

---

### 7. Batch Analysis Section

**Location:** After selecting an account

**What it shows:**
- **Date Range Picker**: Select start and end dates
- **Analyze Button**: Starts the analysis process

**What it does:**
- Lets you choose which date range to analyze
- Processes emails in that range
- Shows loading state while processing
- Displays success/error messages

**How to use:**
1. Select start date (when to begin analysis)
2. Select end date (when to end analysis)
3. Click "Analyze"
4. Wait for processing (status updates automatically)
5. Results appear in other sections once complete

---

## Data Sources & Technical Details

### Email Subjects - Do We Get Them?

**✅ YES, We Do Get Email Subjects!**

**Where Subjects Are Stored:**
1. **In `EmailMetadata` Table**: Stored as plain text, indexed for search
2. **In Encrypted Analysis Data**: Also stored encrypted in `AnalysisResult.encrypted_analysis` for privacy/security

**How Subjects Are Used:**
1. **Categorization**: Subject keywords determine category (notifications, work, etc.)
2. **Clustering**: Subjects are clustered using NLP (DBSCAN) to find similar emails
3. **Analysis**: Subject patterns help identify email types

**Can You See Subjects in the UI?**
- **Currently**: ❌ No, subjects are not displayed in the dashboard UI
- They're used internally for categorization
- They're stored in the database
- They could be displayed if needed (future feature)

### Data Summary Table

| Section | Data Source | Account-Specific? | Uses Subject? | Uses Date? | Uses Sender? |
|---------|-------------|-------------------|---------------|------------|--------------|
| Summary Stats | EmailMetadata, EmailAccount | Mixed (total + account) | ❌ | ❌ | ❌ |
| Top Senders | EmailMetadata | ✅ Yes | ❌ | ❌ | ✅ Yes |
| Categories | AnalysisResult + EmailMetadata | ✅ Yes | ✅ Yes | ❌ | ✅ Yes |
| Frequency | EmailMetadata | ✅ Yes | ❌ | ✅ Yes | ❌ |

### Key Technical Points

1. **All charts are account-specific** (except summary which shows both)
2. **Subjects are retrieved and stored** but not displayed in UI
3. **Categories are determined during analysis** using subject/sender keywords
4. **Frequency uses only timestamps** from `date_received`
5. **Data is stored locally** in SQLite database
6. **Analysis happens once** - results are cached in `AnalysisResult` table

---

## Understanding the Data Flow

1. **Enter Username** → Loads your accounts
2. **Select Account** → Shows summary statistics
3. **Choose Date Range** → Click "Analyze"
4. **Processing** → System fetches and analyzes emails
5. **Results** → Charts and insights update automatically

---

## Tips for Interpreting Results

### High Newsletter Percentage?
- Consider unsubscribing from unused subscriptions
- Use filters to organize newsletters

### Peak Hour at 9 AM?
- Check email in the morning when most arrive
- Set up morning email routine

### One Sender Dominating?
- Check if it's important (colleague) or spam
- Consider filtering if it's noise

### Low Personal Email?
- Most emails are automated/notifications
- Consider if you need to reduce subscriptions

### Many Processed Ranges?
- System is working efficiently
- Won't re-process the same dates
- Safe to re-run analysis on same ranges

---

## Common Questions

**Q: Why do I see 0 emails?**
- You haven't analyzed any date ranges yet
- Click "Analyze" to process emails

**Q: Why are some categories missing?**
- Categories only appear if you have emails in that category
- Empty categories don't show in the pie chart

**Q: Can I analyze the same dates twice?**
- Yes, but it only processes new/unprocessed emails
- Processed ranges prevent duplicate work

**Q: How long does analysis take?**
- Depends on email volume
- 100 emails: ~10-30 seconds
- 1000 emails: ~2-5 minutes
- 10,000+ emails: 10+ minutes

**Q: What if analysis fails?**
- Check the error message
- Common issues: Gmail API not enabled, invalid credentials, network issues
- Try again or check backend logs

**Q: Are email subjects stored?**
- Yes, subjects are stored in the database
- They're used for categorization and clustering
- Currently not displayed in the UI (future feature)

---

## Color Coding

- **Status Badges:**
  - 🟡 Yellow = `pending`
  - 🔵 Blue = `processing`
  - 🟢 Green = `completed`
  - 🔴 Red = `failed`

- **Charts:**
  - Purple/blue gradient theme
  - Consistent colors across all visualizations

---

## Next Steps

After viewing your insights:
1. **Identify patterns**: Notice trends in senders, categories, frequency
2. **Take action**: Unsubscribe, filter, or organize based on insights
3. **Analyze more**: Process different date ranges to see trends over time
4. **Compare accounts**: Add multiple accounts to see differences

---

## Future Possibilities

Since we have subject data:
- **Subject search/filter**: Could add search by subject line
- **Subject display**: Could show subjects in email lists
- **Subject trends**: Could analyze subject patterns over time
- **Smart filtering**: Could filter by subject keywords

