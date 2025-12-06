# mail-mind

Email Analysis and Classifier Tool

An intelligent email management system that analyzes and categorizes emails based on senders and subjects, providing insights into email patterns and communication habits.

## Features

- **Batch Analysis**: Process thousands of emails by date range
- **Analysis Control**: Stop running analyses and automatically revert changes
- **Smart Tracking**: Maintains previously analyzed dates to avoid reprocessing
- **NLP-Powered**: Uses natural language processing for pattern detection and clustering
- **Multi-Provider**: Supports Gmail and Yahoo Mail
- **Secure Storage**: Encrypted local-only storage of metadata and analysis results
- **Web Dashboard**: Interactive dashboard for insights and visualization
- **Pagination**: Efficient loading of analysis runs (5 at a time with "Load More")

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

**📖 See [ACCOUNT_SETUP.md](ACCOUNT_SETUP.md) for detailed instructions**

**Quick Summary:**
- **Gmail**: Get OAuth tokens using `backend/get_gmail_tokens.py` helper script
- **Yahoo**: Generate app-specific password from Yahoo Account Security
- Add account via API (examples in ACCOUNT_SETUP.md)

**Helper Script for Gmail:**
```bash
cd backend
python get_gmail_tokens.py
# Follow the prompts to get your credentials JSON
```

### Step 4: Use the Dashboard

1. Open `http://localhost:3000`
2. Enter your username
3. Select your email account
4. Pick a date range (e.g., last 30 days)
5. Click "Analyze"
6. Wait for processing (status updates automatically)
7. View insights!

## Setup Details

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Gmail: OAuth credentials (for Gmail API)
- Yahoo: App-specific password (for IMAP)

## Usage

### 1. Configure Email Accounts

**📖 For detailed step-by-step instructions, see [ACCOUNT_SETUP.md](ACCOUNT_SETUP.md)**

#### Quick Overview

**Gmail Setup:**
1. Create Google Cloud Project and enable Gmail API
2. Create OAuth 2.0 credentials
3. Get OAuth tokens (use `backend/get_gmail_tokens.py` helper script)
4. Add account via API with credentials JSON

**Yahoo Setup:**
1. Enable 2-Step Verification
2. Generate App-Specific Password from Yahoo Account Security
3. Add account via API with email and app password

**Adding Accounts:**
- Currently accounts must be added via API (UI coming soon)
- See [ACCOUNT_SETUP.md](ACCOUNT_SETUP.md) for complete instructions and examples

### 2. Run Batch Analysis

1. **Open the dashboard**: `http://localhost:3000`
2. **Enter your username** (creates a user profile)
3. **Select an email account** from the dropdown
4. **Choose date range** for analysis:
   - Select start and end dates
   - Click "Analyze"
5. **Monitor progress**: The system shows analysis status
   - Status: `pending` → `processing` → `completed`
   - View number of emails processed
   - Stop button available to cancel running analyses
6. **View analysis history**: 
   - Shows 5 most recent analysis runs
   - Click "Load More" to see previous runs

### 3. View Insights

After analysis completes, view:

- **Summary Stats**: Total emails, senders, accounts
- **Top Senders**: Most frequent email senders with percentages
- **Email Categories**: Distribution (notifications, newsletters, work, personal, etc.)
- **Frequency Patterns**: 
  - Daily averages
  - Hourly distribution (peak hours)
  - Weekday patterns
- **Processed Ranges**: Visual timeline showing which months are fully processed (Yes/No) - helps identify gaps in analysis

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
→ Add an account first using the API endpoints (see ACCOUNT_SETUP.md)

**Database issues**:
- Database is created automatically in `backend/data/mailmind.db`
- Delete the file to reset (loses all data)

**Port conflicts**:
- Backend: Change `PORT` in `.env` or use `--port` flag
- Frontend: Change port in `vite.config.ts`

## Next Steps

See [ROADMAP.md](ROADMAP.md) for detailed development roadmap and priorities.

## Documentation

- **[ACCOUNT_SETUP.md](ACCOUNT_SETUP.md)** - Complete account setup guide (Gmail & Yahoo, developer vs user setup, security)
- **[DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)** - Understanding the dashboard UI and data sources
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap and UX improvements
