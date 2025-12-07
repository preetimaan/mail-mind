# mail-mind

Email Analysis and Classifier Tool

An intelligent email management system that analyzes and categorizes emails based on senders and subjects, providing insights into email patterns and communication habits.

## Features

- **Batch Analysis**: Process thousands of emails by date range with real-time progress tracking
- **Analysis Control**: Stop running analyses and automatically revert changes
- **Smart Tracking**: Maintains previously analyzed dates to avoid reprocessing, can be over-ridden
- **NLP-Powered**: Uses natural language processing for pattern detection and clustering
- **Multi-Provider**: Supports Gmail and Yahoo Mail
- **Secure Storage**: Encrypted local-only storage of metadata and analysis results
- **Web Dashboard**: Interactive dashboard with tab-based navigation and modern UI
- **Pagination**: Efficient loading of analysis runs (5 at a time with "Load More")
- **Real-time Progress**: Live progress bar showing X/Y emails during analysis
- **Email Management**: Copy sender emails, view all senders, and manage accounts easily

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React with TypeScript
- **Database**: SQLite with encryption
- **NLP**: spaCy for text analysis and clustering

## 🚀 Quick Start (5 Minutes)

### Step 1: Backend Setup (2 min)

```bash
cd backend
./setup.sh
source venv/bin/activate
uvicorn main:app --reload
```

✅ Backend should be running on `http://localhost:8000`

**Manual Setup (if script doesn't work):**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
mkdir -p data
```

**Configure environment:**
- Copy `.env.example` to `.env` if it doesn't exist
- Generate encryption key: `python generate_key.py`
- Add the key to `.env` as `ENCRYPTION_KEY=...`

### Step 2: Frontend Setup (1 min)

```bash
cd frontend
npm install
npm run dev
```

✅ Frontend should be running on `http://localhost:3000`

### Step 3: Add Email Account

**📖 See [USER_GUIDE.md](USER_GUIDE.md) for user instructions**

**Important: Two Types of Accounts**

1. **Developer Account (One-Time Setup)**: Google Cloud Project credentials
   - Required for Gmail API access
   - Set up once per developer/installation
   - See [DEVELOPER_ACCOUNT_SETUP.md](DEVELOPER_ACCOUNT_SETUP.md) for Google Cloud Project setup

2. **User Email Accounts (Per User)**: Your actual email accounts to analyze
   - Gmail: Use OAuth flow in dashboard UI
   - Yahoo: Enter email and app-specific password in dashboard UI
   - Add via dashboard "Add Account" button or API (see [USER_GUIDE.md](USER_GUIDE.md))

**Quick Summary:**
- **Gmail**: OAuth flow handled in dashboard UI
- **Yahoo**: Enter email and app-specific password in dashboard UI
- See [USER_GUIDE.md](USER_GUIDE.md) for complete user instructions

### Step 4: Use the Dashboard

1. Open `http://localhost:3000`
2. Enter your username (saved in browser)
3. Select your email account
4. Pick a date range (e.g., last 30 days)
5. Click "Analyze"
6. Watch real-time progress (X/Y emails processed)
7. View insights in organized tabs!

## Setup Details

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- **For Gmail**: Google Cloud Project with OAuth credentials (one-time developer setup)
- **For Yahoo**: App-specific password (per email account)

## Usage

### 1. Configure Email Accounts

**For Developers:** See [DEVELOPER_ACCOUNT_SETUP.md](DEVELOPER_ACCOUNT_SETUP.md) for Google Cloud Project setup  
**For Users:** See [USER_GUIDE.md](USER_GUIDE.md) for adding your email accounts

#### Understanding Account Types

**Developer Account (One-Time Setup - For Gmail Only):**
- **What**: Google Cloud Project with OAuth Client ID/Secret
- **Who**: Developer/admin setting up Mail Mind
- **When**: Once, before any users can add Gmail accounts
- **Purpose**: Enables Mail Mind to connect to Gmail API
- **Result**: Mail Mind can now authenticate with Gmail (but can't access emails yet)
- **See**: [DEVELOPER_ACCOUNT_SETUP.md](DEVELOPER_ACCOUNT_SETUP.md)

**User Email Accounts (Per User, Per Email):**
- **What**: Your actual email accounts (Gmail or Yahoo) to analyze
- **Who**: Each end user who wants to analyze their emails
- **When**: Every time a user wants to add an email account
- **Purpose**: Connect YOUR specific email account to Mail Mind
- **Result**: Mail Mind can now access and analyze THAT USER'S emails
- **See**: [USER_GUIDE.md](USER_GUIDE.md)

#### Quick Overview

**Gmail Setup (Two Steps):**
1. **Developer Setup** (one-time): Create Google Cloud Project, enable Gmail API, create OAuth credentials
   - See [DEVELOPER_ACCOUNT_SETUP.md](DEVELOPER_ACCOUNT_SETUP.md)
2. **User Setup** (per account): Add your Gmail account via dashboard UI (OAuth flow) or API
   - See [USER_GUIDE.md](USER_GUIDE.md)

**Yahoo Setup:**
1. Enable 2-Step Verification
2. Generate App-Specific Password from Yahoo Account Security
3. Add account via dashboard UI or API
   - See [USER_GUIDE.md](USER_GUIDE.md)

**Adding Accounts:**
- **Recommended**: Use the "Add Account" button in the dashboard UI
- **Gmail**: OAuth flow handled directly in the browser (uses developer's Google Cloud credentials)
- **Yahoo**: Enter email and app-specific password
- **Alternative**: Add via API (see [USER_GUIDE.md](USER_GUIDE.md) for examples)

### 2. Run Batch Analysis

1. **Open the dashboard**: `http://localhost:3000`
2. **Enter your username** (creates a user profile)
3. **Select an email account** from the dropdown
4. **Choose date range** for analysis:
   - Select start and end dates
   - Click "Analyze"
5. **Monitor progress**: The system shows analysis status
   - Real-time progress bar: "Processing X/Y emails..."
   - Status: `pending` → `processing` → `completed`
   - View number of emails processed
   - Stop button available to cancel running analyses (with automatic revert)
6. **View analysis history**: 
   - Shows 5 most recent analysis runs
   - Click "Load More" to see previous runs
   - Failed runs grouped together with retry option

### 3. View Insights

After analysis completes, view:

- **Summary Stats**: Total emails, senders, accounts
- **Top Senders**: Most frequent email senders with percentages
- **Email Categories**: Distribution (notifications, newsletters, work, personal, etc.)
- **Frequency Patterns**: 
  - Daily averages
  - Hourly distribution (peak hours)
  - Weekday patterns
  - Yearly trends (year-over-year comparison)
- **Processed Ranges**: Visual timeline showing which months are fully processed (Yes/No visualization) - helps identify gaps in analysis
- **Top Senders**: View all senders with copy-to-clipboard functionality

### 4. Key Features

**Smart Date Tracking**:
- System automatically tracks processed date ranges
- Re-analyzing the same range only processes new/unprocessed dates
- View processed ranges in the dashboard with Yes/No visualization (fully processed vs. gaps)

**Batch Processing**:
- Handles thousands of emails efficiently
- Processes in chunks to avoid memory issues
- Background processing with status updates

**Encrypted Storage**:
- All email metadata and analysis results are encrypted
- User-specific encryption keys
- Local-only storage (no cloud)

## API Endpoints

### Email Accounts
- `POST /api/emails/accounts` - Add email account
- `GET /api/emails/accounts?username=...` - List accounts
- `DELETE /api/emails/accounts/{id}` - Remove account

### Analysis
- `POST /api/analysis/batch` - Start batch analysis
- `GET /api/analysis/runs?limit=5&offset=0` - List analysis runs (with pagination)
- `GET /api/analysis/runs/{id}` - Get run status
- `POST /api/analysis/runs/{id}/retry` - Retry failed analysis runs
- `POST /api/analysis/runs/{id}/stop` - Stop running analysis and revert changes

### Insights
- `GET /api/insights/summary` - Overall summary
- `GET /api/insights/senders` - Sender patterns
- `GET /api/insights/categories` - Category distribution
- `GET /api/insights/frequency` - Frequency patterns
- `GET /api/insights/processed-ranges` - Processed date ranges

## Troubleshooting

**"spaCy model not found"**
→ Run: `pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl`

**"Connection refused"**
→ Make sure backend is running on port 8000

**"No accounts found"**
→ Add an account first via dashboard UI or API (see USER_GUIDE.md)

**Database issues**:
- Database is created automatically in `backend/data/mailmind.db`
- Delete the file to reset (loses all data)

**Port conflicts**:
- Backend: Change `PORT` in `.env` or use `--port` flag
- Frontend: Change port in `vite.config.ts`

## Next Steps

See [ROADMAP.md](ROADMAP.md) for detailed development roadmap and priorities.

## Documentation

- **[DEVELOPER_ACCOUNT_SETUP.md](DEVELOPER_ACCOUNT_SETUP.md)** - Developer guide for setting up Google Cloud Project (Gmail API)
- **[USER_GUIDE.md](USER_GUIDE.md)** - User guide for adding email accounts and using the dashboard
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap and UX improvements
