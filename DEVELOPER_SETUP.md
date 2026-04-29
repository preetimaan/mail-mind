# Mail Mind — Developer setup

This document is for **whoever builds, configures, or hosts** Mail Mind (developer, ops, or “friend who installed it for you”). **End users** only need `USER_GUIDE.md`: connecting mailboxes, running analysis, and reading insights — no Cloud projects, `.env`, or client secrets there.

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

## Provider connections: who does what

### Gmail (OAuth) — operator vs end user

Assume the person deploying Mail Mind is **not** the only end user.

- **Whoever runs / deploys the backend** (usually you, the developer) must register the app in **Google Cloud** once per environment:
  - Create or reuse a project, enable **Gmail API**, configure the **OAuth consent screen**, and create **OAuth 2.0 Client ID** credentials of type **Web application**.
  - Ensure OAuth scopes allow both metadata reads and labels/filters retrieval (`gmail.readonly` and `gmail.settings.basic`).
  - Set **Authorized redirect URIs** to exactly match `MAILMIND_GMAIL_REDIRECT_URI` in `backend/.env` (default in `.env.example` is `http://localhost:8000/api/oauth/gmail/callback`).
  - Put `MAILMIND_GMAIL_CLIENT_ID` and `MAILMIND_GMAIL_CLIENT_SECRET` in `backend/.env`. Restart the backend after changes.
  - While the OAuth app is in **Testing**, add every Gmail address that will connect as a **Test user** on the consent screen.
- **Each end user** uses only the product UI: **Settings → Connect Gmail** and Google’s browser sign-in/consent for **their** mailbox. They never see client id/secret or server configuration; document that flow in the **user guide**, not here.

### Yahoo (app password) — operator vs end user

- **End user**: In Yahoo **Account security**, generates an **app password** and pastes it in Mail Mind (not their normal login password). See the user guide for wording aimed at non-technical readers.
- **Operator**: Sets `MAILMIND_TOKEN_ENCRYPTION_KEY` so the backend can store that password encrypted at rest.

## Current analysis mode (important)

For **connected** accounts, analysis fetches **real provider metadata** (Gmail API / Yahoo IMAP), stores **metadata only** in SQLite, and Insights aggregate that data. Stub generation is not the normal path once accounts are connected.

## Labels & Filters tab behavior (provider differences)

- **Gmail**: backend reads labels + filter rules from Gmail API.
- **Yahoo**: backend reads folder names from IMAP (`LIST`). Filter rules are not available in this view.

## Environment variables

Use `.env.example` as the template.

- **Backend env file**: copy it to `backend/.env` (same folder you run `uvicorn` from).

**Required for real accounts**

- `MAILMIND_TOKEN_ENCRYPTION_KEY` (Fernet) — encrypts provider secrets at rest (Gmail refresh token, Yahoo app password).
- For Gmail OAuth: `MAILMIND_GMAIL_CLIENT_ID`, `MAILMIND_GMAIL_CLIENT_SECRET`, and a matching `MAILMIND_GMAIL_REDIRECT_URI`.

Generate a Fernet key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

