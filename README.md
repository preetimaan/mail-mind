# Mail Mind

Local-first email insights dashboard.

## Docs

- User guide: `USER_GUIDE.md`
- Developer setup: `DEVELOPER_SETUP.md`
- Roadmap: `ROADMAP.md`

## Dev

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```