# Mail Mind — Architecture

Local-first email **insights** dashboard. Fetches **metadata only** from Gmail (OAuth) or Yahoo (IMAP), stores in SQLite, aggregates on read. Not an email client. Mail Mind never modifies emails — it is a read-only analysis and suggestion tool.

## System boundary

```
┌──────────────── React SPA (port 3000) ────────────────┐
│  App.tsx — tabs: Accounts, Analysis, Insights,       │
│            Sender Classification                     │
│  api/client.ts → http://localhost:8000/api           │
└────────────────────────┬─────────────────────────────┘
                         │ REST
┌────────────────────────▼─────────────────────────────┐
│  FastAPI (port 8000)                                   │
│  routers/ → services/ → SQLAlchemy → SQLite            │
│  InProcessAnalysisRunner (daemon threads)              │
└────────┬───────────────────┬──────────────────────────┘
         │                   │                    │
         ▼                   ▼                    ▼
  Gmail API (OAuth)   Yahoo IMAP         Gemini / OpenAI
                      (app password)     (optional — AI classification only)
```

## Layering

| Layer | Location | Role |
|-------|----------|------|
| **UI** | `frontend/src/pages/App.tsx` | Monolithic SPA (~1.3k lines), all tabs inline |
| **API client** | `frontend/src/api/client.ts` | Typed fetch wrapper |
| **HTTP** | `backend/app/routers/` | Feature routers: accounts, analysis, insights, oauth, labels |
| **Jobs** | `backend/app/services/analysis_runner.py` | Background analysis in-process threads |
| **Providers** | `backend/app/services/gmail_*`, `yahoo_*` | Fetch + normalize metadata |
| **Classification** | `backend/app/services/classification_engine.py` | Rule-based sender labelling (Tier 1/2) |
| **AI classifier** | `backend/app/services/ai_classifier.py` | Optional Gemini/OpenAI batch classification |
| **Security** | `credential_store.py`, `token_crypto.py` | Fernet-encrypted tokens at rest |
| **Persistence** | `backend/app/db/models.py` | SQLAlchemy ORM, SQLite default |

No Celery/Redis — cancellation via `threading.Event`.

## Identity model

**No real auth.** User picks a **workspace username** stored in browser `localStorage` (`mailmind_username`). All accounts, messages, and runs are scoped by that string. Designed for single-user local deployment.

## Core entities

| Entity | Purpose |
|--------|---------|
| `Account` | Connected Gmail/Yahoo account per workspace |
| `OAuthCredential` | Encrypted refresh token (Gmail) or app password (Yahoo) |
| `AnalysisRun` | Date-range job with status, chunk progress |
| `EmailMessage` | Metadata row: sender, subject, timestamps, headers — **no body** |
| `ProcessedRange` | Half-open `[start, end)` windows successfully analyzed |
| `SenderClassification` | One row per sender per account: custom labels, confidence, source, label_sources JSON, sample subjects |

Date ranges use **half-open intervals** consistently: `[start_date, end_date_exclusive)`.

## Analysis pipeline

```
POST /analysis/start
  → InProcessAnalysisRunner spawns thread
  → 7-day chunks (CHUNK_DAYS = 7)
  → Provider fetch (Gmail API / Yahoo IMAP)
  → Normalize sender (plus-alias collapse for Gmail)
  → Batch insert (commit every 50 messages)
  → Update ProcessedRange on chunk success
```

**Cancel / failure** — Reverts partial run: deletes messages + processed ranges for that run.

**Force re-analysis** — Deletes existing messages + ranges in window before re-run.

**Gmail inflation guard** — Excludes sent/drafts from counts; optional `inbox_only` per run.

## Sender classification pipeline

Classification runs on demand via `POST /label-suggestions/classify`. It is idempotent and never overwrites manual assignments.

```
POST /label-suggestions/classify
  → classification_engine.classify_account()
  → For each sender in SenderClassification:
      Tier 1 — known domain list (linkedin.com → Career, etc.)
      Tier 2 — keyword rules on sender name / domain
      Skip if source is already "manual" or "ai"
  → Persist labels + label_sources JSON + confidence
```

**label_sources** is a JSON object on each `SenderClassification` row mapping label name → source:
- `tier1_domain` — matched a known domain rule
- `tier2_keyword` — matched a keyword rule
- `ai` — classified by Gemini/OpenAI
- `manual` — user assigned directly
- `manual_excluded` — user explicitly removed an auto label; classification engine never re-adds it

**AI enhancement** (optional, requires `MAILMIND_AI_PROVIDER` + `MAILMIND_AI_API_KEY`):

```
POST /label-suggestions/ai-enhance
  → Fetches unclassified senders (no labels, not previously AI-classified)
  → Batches 50 senders per Gemini call (reduces rate limit exposure)
  → Parses {"results": {"email": ["Label1", ...]}} response
  → Persists labels with source="ai", confidence="medium"
  → Returns processed count + remaining count
```

Gemini free tier: 15 RPM. The engine sends one batch of 50 per run; user re-runs to classify more. This keeps latency predictable and avoids exhausting the rate limit in a single request.

## Dispositions (planned)

Each `SenderClassification` row will gain a `disposition` field:

| Value | Meaning |
|---|---|
| `archive` | Keep for records, receipts, or future events |
| `delete` | Ephemeral — OTPs, delivery notifications, expired alerts |
| `unsubscribe` | Recurring sender the user wants to stop receiving |
| `undecided` | Default; user has not made a decision |

Dispositions are set by rules on classification run (label + subject keyword signals), and can be overridden per sender by the user. Mail Mind never acts on dispositions — it only surfaces them so the user can act in Gmail themselves.

**Rules (label is primary signal, subject keywords are tiebreaker):**
- Money, Gov & Tax, Health, Career, Study, Life Admin, Services → `archive`
- Sample subjects match OTP patterns (`verification code`, `one-time password`, `OTP`, `your code is`, `sign-in code`) → `delete`
- Shopping + subjects contain order/receipt/invoice keywords → `archive`
- Shopping + subjects contain sale/deal/% off keywords → `unsubscribe`
- High email volume sender with purely promotional subjects → `unsubscribe`
- Everything else → `undecided`

The UI exposes four tabs (Archive / Delete / Unsubscribe / Undecided), a per-sender disposition dropdown, and a copy-to-clipboard filter for each sender.

## Insights (computed on read)

`routers/insights.py` — SQL aggregations over stored `EmailMessage`:

- Summary counts, top senders/domains
- Category breakdown (heuristic; default `"other"`)
- Processed-range gaps (last 365 days) for UI pre-fill

No ML/LLM — pure SQL + heuristics.

## Sender Classification tab

The main workflow tab for understanding and acting on senders. All actions are read-only — Mail Mind never modifies emails, labels, or filters in Gmail/Yahoo.

Sub-sections:
- **Run Classification** — triggers the rule-based engine; shows coverage stats per label
- **Label view** — per-label sender lists; manual label assignment per sender; copy Gmail `from:` filter query per label
- **AI Enhancement** — optional; sends unclassified senders to Gemini in batches of 50; shows remaining count
- **Unclassified** — senders with no labels yet; candidates for AI or manual assignment
- **Dispositions** (planned) — senders grouped by archive / delete / unsubscribe / undecided; per-sender override; copy filter

## Configuration

`MAILMIND_*` env vars via Pydantic settings (`backend/app/settings.py`):

- `MAILMIND_DATABASE_URL` — SQLite path
- Gmail OAuth client id/secret
- `MAILMIND_TOKEN_ENCRYPTION_KEY` — Fernet key for credentials
- `MAILMIND_AI_PROVIDER` — `gemini` or `openai` (optional)
- `MAILMIND_AI_API_KEY` — API key for the configured provider (optional)
- `MAILMIND_AI_MODEL` — override the default model (optional; defaults to `gemini-2.5-flash`)

Settings are read once at startup via `@lru_cache` — restart the backend after changing `.env`.

See `DEVELOPER_SETUP.md` for operator setup.

## Design decisions (explain these)

1. **Metadata-only** — Privacy and storage; never persist bodies.
2. **Local-first** — SQLite, no cloud dependency for the app itself.
3. **In-process jobs** — Simplicity over distributed queue; fine for personal scale.
4. **Heuristic-first classification** — Tier 1/2 rule engine covers the majority of senders deterministically. AI (Gemini/OpenAI) is an optional enhancement layer, not a dependency.
5. **Account deactivation on auth failure** — Failed refresh/fetch sets `is_active = False`; UI prompts reconnect.
6. **Unified credential table** — Gmail OAuth and Yahoo app password both use `OAuthCredential`.
7. **Chunked + resumable windows** — `ProcessedRange` tracks what's done; gap endpoint drives "fill holes" UX.

## Extension points

- New provider: add `services/<provider>_fetch.py`, connect route, extend `Account.provider`
- New insight: add query in `insights.py` + tab section in `App.tsx`
- Real auth: replace username-in-localStorage with session middleware (major change)

## Related docs

- `README.md` — dev quickstart
- `USER_GUIDE.md` — end-user flows
- `DEVELOPER_SETUP.md` — OAuth, env, DB reset
- `ROADMAP.md` — feature status
