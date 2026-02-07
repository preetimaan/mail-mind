# Mail Mind

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

---

## Quick Start

```bash
# Backend (Terminal 1)
cd backend
./setup.sh
source venv/bin/activate
uvicorn main:app --reload
```

```bash
# Frontend (Terminal 2)
cd frontend
npm install
npm run dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

**First time?** See [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md#first-time-setup) for environment setup and Google Cloud configuration (required for Gmail).

---

## Setup Guide

| Role | Documentation | Description |
|------|---------------|-------------|
| **Developer (Returning)** | [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md#returning-developer-quick-start) | Quick start for developers who've already set up |
| **Developer (First Time)** | [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md#first-time-setup) | Full setup: environment, Google Cloud Project, OAuth |
| **End User** | [USER_GUIDE.md](USER_GUIDE.md) | Add email accounts and use the dashboard |

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- **For Gmail**: Google Cloud Project with OAuth credentials (one-time developer setup)
- **For Yahoo**: App-specific password (per email account)

---

## Using Mail Mind

### 1. Run Analysis

1. Open the dashboard at `http://localhost:3000`
2. Enter your username (saved in browser)
3. Select your email account from the dropdown
4. Choose a date range and click "Analyze"
5. Watch real-time progress (X/Y emails processed)
6. View insights in organized tabs

### 2. View Insights

After analysis completes, view:

- **Summary Stats**: Total emails, senders, accounts
- **Top Senders**: Most frequent email senders with percentages
- **Email Categories**: Distribution (notifications, newsletters, work, personal, etc.)
- **Frequency Patterns**: Daily averages, hourly distribution, weekday patterns, yearly trends
- **Processed Ranges**: Visual timeline showing which months are fully processed

### 3. Key Features

**Smart Date Tracking**: System tracks processed date ranges and only processes new/unprocessed dates on re-analysis.

**Batch Processing**: Handles thousands of emails efficiently with background processing.

**Encrypted Storage**: All email metadata and analysis results are encrypted locally.

---

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

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "spaCy model not found" | Run: `pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl` |
| "Connection refused" | Make sure backend is running on port 8000 |
| "No accounts found" | Add an account via dashboard UI (see [USER_GUIDE.md](USER_GUIDE.md)) |
| Database issues | Database is at `backend/data/mailmind.db` - delete to reset |
| Port conflicts | Backend: change `PORT` in `.env`. Frontend: change port in `vite.config.ts` |

For Gmail/Yahoo credential issues, see troubleshooting in [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md#troubleshooting) or [USER_GUIDE.md](USER_GUIDE.md#troubleshooting).

---

## Documentation

| Document | Purpose |
|----------|---------|
| [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md) | Developer setup: environment, Google Cloud Project, OAuth |
| [USER_GUIDE.md](USER_GUIDE.md) | End user guide: adding accounts, using the dashboard |
| [ROADMAP.md](ROADMAP.md) | Development roadmap, planned features, and known issues |
