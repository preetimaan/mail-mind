# Mail Mind

An intelligent email management system that analyzes and categorizes emails based on senders, providing insights into email patterns and communication habits.

## Features

- **Batch Analysis**: Process thousands of emails by date range with real-time progress tracking
- **Analysis Control**: Stop running analyses and automatically revert changes
- **Smart Tracking**: Maintains previously analyzed dates to avoid reprocessing, can be over-ridden
- **Pattern analysis**: Heuristic categorization and subject/sender grouping
- **Multi-Provider**: Supports Gmail and Yahoo Mail
- **Secure Storage**: Encrypted local-only storage of metadata and analysis results
- **Web Dashboard**: Interactive dashboard with tab-based navigation (Analysis, Insights, Emails, Settings)
- **Browse Emails**: Paginated email list with filters (category, sender, date range, subject search)
- **Category-First Navigation**: Click a category in the pie chart to open the email list filtered by that category
- **Custom Categories**: Create sender-based categories (e.g. Finance, Urgent); assign senders from Top Senders or use AI suggestions
- **AI Category Suggestions**: Suggest categories for senders (OpenAI when `OPENAI_API_KEY` is set, else rule-based); apply to custom categories in one click
- **Pagination**: Efficient loading of analysis runs and email list (Load More)
- **Real-time Progress**: Live progress bar showing X/Y emails during analysis
- **Email Management**: Copy sender emails, Gmail filter string from selected senders, manage accounts

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React with TypeScript
- **Database**: SQLite with encryption
- **Analysis**: Heuristic batch processing (no spaCy/sklearn in the default backend)

## 🚀 Quick Start (5 Minutes)

### Step 1: Backend Setup (2 min)

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

After analysis completes, view (Insights tab):

- **Summary Stats**: Total emails, senders, accounts
- **Top Senders**: Most frequent senders; copy emails, generate Gmail filter, assign to custom category, or open "Emails" filtered by sender
- **Email Categories**: Pie chart; click a segment to open the Emails tab filtered by that category
- **Frequency Patterns**: Daily averages, hourly/weekday distribution, yearly trends
- **Processed Ranges**: Visual timeline of analyzed date ranges

### 3. Browse & Filter Emails

- Open the **Emails** tab to see a paginated list of analyzed emails
- Filter by category (auto or custom), sender, date range, or subject search
- Use "Apply" or change filters (results update after a short delay)

### 4. Custom Categories (Sender-Based)

- **Settings** → Custom categories: create categories (e.g. Finance, Urgent), rename, delete
- **Insights** → Top Senders: use "Add to category" dropdown to assign a sender to a custom category
- **Suggest categories**: Click "Suggest categories" in Top Senders to get AI/rule-based suggestions and apply them to custom categories
- **Emails** tab: Filter dropdown includes your custom categories

### 5. Key Features

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
- `GET /api/insights/senders` - Sender patterns (paginated)
- `GET /api/insights/categories` - Category distribution
- `GET /api/insights/frequency` - Frequency patterns
- `GET /api/insights/frequency/yearly` - Yearly frequency
- `GET /api/insights/processed-ranges` - Processed date ranges
- `GET /api/insights/emails` - Paginated email list (filters: category, custom_category_id, sender_email, start_date, end_date, q)
- `GET /api/insights/custom-categories` - List custom categories
- `POST /api/insights/custom-categories` - Create custom category
- `PATCH /api/insights/custom-categories/{id}` - Rename
- `DELETE /api/insights/custom-categories/{id}` - Delete
- `POST /api/insights/custom-categories/{id}/senders` - Assign senders (body: `sender_emails`)
- `POST /api/insights/ai-suggest-categories` - AI/rule-based category suggestions (body: `senders`)
- `GET /api/insights/diagnostic` - Data integrity check
- `POST /api/insights/cleanup-duplicates` - Remove duplicate analysis results
- `POST /api/insights/remove-sent-emails` - Remove sent emails from analysis
- `POST /api/insights/recalculate` - Recalculate categories without re-fetching

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Make sure backend is running on port 8000 |
| "No accounts found" | Add an account via dashboard UI (see [USER_GUIDE.md](USER_GUIDE.md)) |
| Database issues | Database is at `backend/data/mailmind.db` - delete to reset |
| Port conflicts | Backend: change `PORT` in `.env`. Frontend: change port in `vite.config.ts` |
| "Suggest categories" uses rules only | Set `OPENAI_API_KEY` in backend `.env` for AI-powered suggestions (see [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md)) |

**Notes:** Custom categories are **sender-based** (assign senders to a category; filter shows emails from those senders). Gmail requires OAuth credentials from Google Cloud Console; Yahoo requires an app-specific password. Backend: port 8000; frontend: port 3000.

For Gmail/Yahoo credential issues, see troubleshooting in [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md#troubleshooting) or [USER_GUIDE.md](USER_GUIDE.md#troubleshooting).

---

## Documentation

| Document | Purpose |
|----------|---------|
| [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md) | Developer setup: environment, Google Cloud Project, OAuth |
| [USER_GUIDE.md](USER_GUIDE.md) | End user guide: adding accounts, using the dashboard |
| [ROADMAP.md](ROADMAP.md) | Development roadmap, planned features, and known issues |
