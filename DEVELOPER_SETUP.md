# Mail Mind — Developer setup

This is the current Mail Mind implementation.

## Prereqs

- Python 3.10+
- Node 18+

## Run locally

### Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

### Frontend (Vite/React)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Local “session”

The “login” is a local workspace username stored in `localStorage` under `mailmind_username`.

- **Clear login**: click **Log out** in the UI, or clear that key from your browser storage.

## Database

- **Engine**: SQLite via SQLAlchemy
- **DB file (current default)**: created in the backend working directory as `backend/mailmind.db`
- Tables are created automatically on backend startup (`create_all`).

### Reset DB

Stop the backend, then:

```bash
rm -f backend/mailmind.db
```

Start backend again to re-create tables.

## Current analysis mode (important)

Until provider integrations are implemented (Gmail OAuth / Yahoo), analysis runs generate **deterministic stub email metadata** (`EmailMessage`) so:

- the **Insights** tab is real (aggregations over stored rows)
- behavior is stable/reproducible for development

Provider integrations will replace stub generation, but keep the same storage/insights pipeline.

## Environment variables

We will add `_rebuild/.env.example` when provider integrations land (Gmail/Yahoo creds, encryption keys, etc.).

