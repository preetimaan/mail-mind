# Mail Mind - Development Roadmap

## ✅ Completed Features

### Backend Infrastructure
- [x] FastAPI application structure
- [x] SQLite database with SQLAlchemy ORM
- [x] Database schema (Users, EmailAccounts, EmailMetadata, AnalysisRuns, AnalysisResults, ProcessedDateRange)
- [x] User-specific encryption system
- [x] CORS configuration for frontend integration
- [x] Environment variable management (.env support)
- [x] Database initialization on startup

### Email Connectors
- [x] Gmail API connector with OAuth support
  - [x] OAuth credential handling
  - [x] Token refresh logic
  - [x] Email fetching by date range
  - [x] Metadata extraction (sender, subject, date)
- [x] Yahoo Mail IMAP connector
  - [x] IMAP connection handling
  - [x] App-specific password support
  - [x] Email fetching by date range
  - [x] Header decoding and parsing

### Analysis Engine
- [x] NLP analyzer with spaCy integration
  - [x] Subject line clustering (DBSCAN)
  - [x] Sender pattern analysis
  - [x] Email categorization (notifications, newsletters, social, shopping, work, personal, other)
  - [x] Frequency analysis (hourly, daily, weekday patterns)
- [x] Batch processing service
  - [x] Date range tracking to avoid reprocessing
  - [x] Incremental processing (only unprocessed dates)
  - [x] Background task execution
  - [x] Status tracking (pending, processing, completed, failed, cancelled)
  - [x] Analysis cancellation support with automatic revert
  - [x] Change tracking for revert operations (emails, analysis results, processed ranges)
- [x] Date tracker for processed ranges
  - [x] Gap detection
  - [x] Range merging for overlapping dates

### API Endpoints
- [x] Email Accounts
  - [x] `POST /api/emails/accounts` - Create account
  - [x] `GET /api/emails/accounts` - List accounts
  - [x] `DELETE /api/emails/accounts/{id}` - Delete account
- [x] Analysis
  - [x] `POST /api/analysis/batch` - Start batch analysis
  - [x] `GET /api/analysis/runs` - List analysis runs (with pagination support)
  - [x] `GET /api/analysis/runs/{id}` - Get run status
  - [x] `POST /api/analysis/runs/{id}/retry` - Retry failed analysis runs
  - [x] `POST /api/analysis/runs/{id}/stop` - Stop running analysis and revert changes
- [x] OAuth
  - [x] `GET /api/oauth/authorize` - Generate OAuth authorization URL
  - [x] `GET /api/oauth/callback` - Handle OAuth callback and store credentials (✅ Implemented - required for Gmail account setup)
- [x] Insights
  - [x] `GET /api/insights/summary` - Overall summary
  - [x] `GET /api/insights/senders` - Top senders and patterns (with pagination: limit, offset)
  - [x] `GET /api/insights/categories` - Category distribution
  - [x] `GET /api/insights/frequency` - Frequency patterns
  - [x] `GET /api/insights/frequency/yearly` - Yearly frequency analysis
  - [x] `GET /api/insights/processed-ranges` - Processed date ranges
  - [x] `GET /api/insights/processed-ranges/gaps` - Detect unprocessed date gaps
  - [x] `GET /api/insights/diagnostic` - Data integrity diagnostics
  - [x] `POST /api/insights/cleanup-duplicates` - Remove duplicate analysis results
  - [x] `POST /api/insights/remove-sent-emails` - Remove incorrectly included sent emails
  - [x] `POST /api/insights/recalculate` - Recalculate insights without re-fetching emails

### Frontend
- [x] React + TypeScript setup with Vite
- [x] Dashboard page
  - [x] Username input (with localStorage persistence)
  - [x] Account selector component
  - [x] Date range picker (with gap pre-filling support)
  - [x] Analysis trigger with loading states
  - [x] Stop analysis button (always visible, disabled when no analysis running)
  - [x] Analysis runs pagination (shows 5 most recent, "Load More" for previous runs)
  - [x] Account management UI (AddAccountModal)
  - [x] OAuth callback handling
  - [x] Failed run grouping and retry functionality
  - [x] Modular component architecture (custom hooks, extracted components)
  - [x] Sticky header with reduced padding
  - [x] Contextual error/success message placement
- [x] Visualization components
  - [x] Stats grid (summary statistics)
  - [x] Sender chart (top senders with percentages)
    - [x] Pagination (load more in batches of 20, up to 100)
    - [x] Multi-select checkboxes for senders
    - [x] Gmail filter string generator from selected senders
    - [x] Compact row layout with text wrapping
  - [x] Category chart (category distribution)
  - [x] Frequency chart (hourly/weekly patterns)
  - [x] Yearly frequency chart (year-over-year analysis)
  - [x] Processed ranges display with gap detection
  - [x] Processed ranges chart (simplified Yes/No visualization)
- [x] Data Maintenance UI (Settings tab)
  - [x] Remove Sent Emails button
  - [x] Recalculate Insights button
  - [x] Clean Up Duplicates button
- [x] Real-time status updates
  - [x] Polling for analysis completion
  - [x] Error and success message display
  - [x] User-friendly error messages for failed runs
  - [x] Real-time progress bar for email analysis (X/Y emails during fetching)
- [x] API client with TypeScript types
- [x] Custom hooks for state management
  - [x] useUsername - username state and localStorage
  - [x] useOAuthCallback - OAuth callback handling
  - [x] useAccounts - account loading and management
  - [x] useInsights - insights data fetching
  - [x] useAnalysisPolling - analysis run polling

### Documentation
- [x] README.md with setup instructions
- [x] DEVELOPER_SETUP.md guide
- [x] USER_GUIDE.md guide
- [x] API documentation (via FastAPI Swagger UI)

### Error Handling & Observability
- [x] Comprehensive logging infrastructure throughout backend
- [x] User-friendly error message storage and display
- [x] Error categorization (token_expired, connection_error, auth_error)
- [x] Retry functionality for failed analysis runs
- [x] Failed run grouping in UI (collapsible sections)
- [x] Graceful handling of expired/revoked OAuth tokens
- [x] Utility script to mark stuck runs as failed
- [x] Analysis cancellation with automatic data revert
- [x] Change tracking during analysis for safe rollback

### Bug Fixes
- [x] Fixed `analysis_run_id` null constraint bug
- [x] Fixed timezone handling in date tracking (normalize to UTC)
- [x] Improved gap detection to find all unprocessed date ranges
- [x] Fixed duplicate email handling (composite unique constraint, IntegrityError handling, Yahoo UID support)
- [x] Fixed force reanalysis not properly deleting existing data (now deletes EmailMetadata + AnalysisResults)
- [x] Fixed Gmail fetching sent emails (now excludes sent with `-in:sent` filter)
- [x] Fixed insights not updating after multiple analysis runs

---

## 🚧 In Progress / Next Steps

### High Priority

#### 1. Enhanced Account Management
**Status**: Partially Complete  
**Priority**: Medium  
**Description**: Account management UI exists, but could be enhanced with additional features.

**Tasks**:
- [x] Add account form component (provider selection, email input, credentials)
- [x] Gmail OAuth flow UI (redirect handling)
- [x] Gmail OAuth callback handler (`/api/oauth/callback` endpoint)
- [x] Yahoo credentials form (email + app password)
- [x] Credential validation before saving
- [x] Error handling for invalid credentials
- [ ] Connection testing button

### Medium Priority

#### 2. UI/UX Enhancements
**Status**: Partially Complete  
**Priority**: Medium  
**Description**: Improve visual design and user experience.

**Tasks**:
- [x] Add loading spinner for in-progress analysis
- [x] Improve overall UI design (modern, clean interface)
- [x] Better visual feedback for missing/empty data
- [x] Sticky header with reduced padding
- [x] Contextual error/success message placement (above relevant sections)
- [x] Modular component architecture for better maintainability
- [x] Replace browser confirm dialogs with custom modals (DeleteAccountModal, ConfirmModal)
- [x] Improved delete account flow with account selection modal
- [x] Copy email functionality for frequent senders (individual and bulk copy, filter string generation)
- [x] Show email summary with 0 values when no data exists (always visible)
- [x] Tab-based navigation and improved layout structure
- [x] Sticky tabs (stay visible when scrolling)
- [x] Compact account summary bar (single line vs. 3 cards)
- [x] UI improvements (button heights, spacing, colors, layout fixes)
- [x] Date input validation improvements
- [ ] Frontend state persistence - Restore analysis state on page refresh

#### 3. Email List, Filtering & Search
**Status**: Complete  
**Priority**: High  
**Description**: Browse and filter analyzed emails so users can reduce inbox overload and split mail by category/sender/date.

**Tasks**:
- [x] **Email list API** – `GET /api/insights/emails` with pagination (`limit`, `offset`), returning email metadata + category per account. Response: subject, sender_email, sender_name, date_received, category, custom_category.
- [x] **Email list UI** – New "Emails" tab with paginated table (subject, sender, date, category, custom category). Empty state when no data.
- [x] **Filter by category** – List endpoint accepts `category=` (notifications, newsletters, social, shopping, work, personal, other). UI: category dropdown (includes custom categories).
- [x] **Filter by sender** – List endpoint accepts `sender_email=`. UI: "Emails" button in Top Senders → open email list filtered to that sender.
- [x] **Filter by date range** – List endpoint accepts `start_date`, `end_date`. UI: date-from / date-to inputs on the list view.
- [x] **Search by subject** – List endpoint accepts `q=` (substring match on subject). UI: search box in filter bar.
- [x] **Filter UI component** – Filter bar: category dropdown, sender input, date range, subject search, Apply. Debounced refetch on filter change.
- [x] **Category-click → filtered list** – Category chart segments clickable; clicking opens Emails tab with that category filter.

#### 4. Category-First Navigation & Custom Categories
**Status**: Complete  
**Priority**: High  
**Description**: Let users split emails into categories via navigation (click category → see list) and via user-defined categories (e.g. "Finance", "Urgent") by assigning senders to custom labels.

**Tasks**:
- [x] **Category-first entry** – From Insights, clicking a category opens the email list filtered to that category.
- [x] **Custom categories (user-defined)** – CustomCategory table (user_id, name). CRUD API: GET/POST/PATCH/DELETE `/api/insights/custom-categories`.
- [x] **Sender → custom category mapping** – SenderCategoryMapping table (user_id, sender_email, custom_category_id). POST/DELETE for assign/remove. One sender per custom category (reassign replaces).
- [x] **Filter by custom category** – Email list accepts `custom_category_id`; custom categories in filter dropdown alongside auto-categories.
- [x] **Custom category management UI** – Settings: CustomCategoriesManager (create, rename, delete). Top Senders: "Add to category" dropdown to assign sender to custom category.

#### 5. AI-Powered Sender Categorization
**Status**: Complete  
**Priority**: High  
**Description**: Intelligently categorize senders using AI to suggest meaningful categories and subcategories. Builds on Custom Categories (section 4): AI suggests which senders belong in which user or system category.

**Tasks**:
- [x] AI model integration – OpenAI (gpt-4o-mini) when OPENAI_API_KEY set; else rule-based keyword matching
- [x] Smart category detection – Rule-based: domain/name keywords for Essentials, Life, Software/Tech, Work, Social, Other
- [x] Main category suggestions: Essentials, Life, Software/Tech, Work, Social, Other (with subcategory from OpenAI when used)
- [x] Bulk categorization – POST `/api/insights/ai-suggest-categories` with senders list; returns suggestions per sender
- [x] User confirm/apply – AISuggestModal: table of suggestions, apply to existing custom category or create new, per row
- [x] Save custom categories per user – Apply writes to existing custom categories / sender mappings
- [x] Filter emails by AI-suggested categories – Once applied, filter by custom category in Emails tab

#### 6. Gmail & large-range ingestion reliability
**Status**: Not Started  
**Priority**: High (operational)  
**Description**: Overall ranges longer than ~2 years are split server-side into ~365-day half-open chunks, so Gmail is not queried for the entire span at once. Each chunk still performs paginated `messages.list` plus one `messages.get` per message (metadata). The analysis **start** request returns quickly (background work); risk is mainly **429** rate limits, long wall time per chunk, **250k messages/chunk** truncation, and **duplicate API work** from pre-fetch email counting.

**Tasks**:
- [ ] Retries with exponential backoff (and jitter) on transient errors and **429** rate limits
- [ ] Skip, cap, or replace Gmail **`get_email_count_by_date_range`** with a cheaper estimate (today it can mirror nearly a full list+get pass before fetch)
- [ ] Configurable **chunk length** (e.g. env `MAILMIND_ANALYSIS_CHUNK_DAYS`) for very dense mailboxes
- [ ] Explore Gmail **batch HTTP** for batched `messages.get` (fewer round-trips)
- [ ] Observability: log rate-limit events, per-chunk truncation warnings, elapsed time per chunk

### Low Priority / Future Enhancements

#### 7. Multi-Account Comparison
**Status**: Not Started  
**Priority**: Low  
**Description**: Compare insights across multiple email accounts.

**Tasks**:
- [ ] Side-by-side account comparison
- [ ] Aggregate statistics across accounts
- [ ] Account-specific insights toggle

#### 8. Performance Optimizations
**Status**: Not Started  
**Priority**: Low  
**Description**: Optimize for large-scale email processing.

**Tasks**:
- [ ] Batch processing optimization (larger chunks)
- [ ] Database indexing improvements
- [ ] Caching for frequently accessed insights
- [ ] Async email fetching improvements
- [ ] Memory optimization for large batches

#### 9. Testing
**Status**: Not Started  
**Priority**: Medium  
**Description**: Add comprehensive test coverage.

**Tasks**:
- [ ] Unit tests for NLP analyzer
- [ ] Unit tests for date tracker
- [ ] Integration tests for API endpoints
- [ ] Frontend component tests
- [ ] E2E tests for analysis flow
- [ ] Mock email connectors for testing

#### 10. Deployment & DevOps
**Status**: Not Started  
**Priority**: Medium  
**Description**: Production deployment setup.

**Tasks**:
- [ ] Docker containerization
- [ ] Docker Compose for local development
- [ ] Production deployment guide
- [ ] Environment configuration management
- [ ] Database migration system
- [ ] Logging and monitoring setup

---

## 📊 Feature Priority Matrix

| Feature | Priority | Effort | Impact | Status |
|---------|----------|--------|--------|--------|
| Gmail / large-range ingestion (§6) | High | Medium | High | Not Started |
| Email list, filtering & search | High | Medium | High | Complete |
| Category-first nav & custom categories | High | Medium | High | Complete |
| AI-powered sender categorization | High | High | High | Complete |
| UI/UX enhancements | Medium | Medium | Medium | Partially complete |
| Testing | Medium | High | High | Not Started |
| Deployment & DevOps | Medium | Medium | High | Not Started |
| Multi-account comparison | Low | Medium | Low | Not Started |
| Performance optimization | Low | High | Medium | Not Started |

---

## 📝 Notes

- All data is encrypted and stored locally (SQLite under `backend/data/` by default; relative `DATABASE_URL` resolves against the `backend/` directory).
- **Batch analysis dates** are calendar days: API accepts `YYYY-MM-DD`, combined to naive local midnights; ranges are half-open `[start, end)` (start inclusive, end exclusive). The frontend sends wall-calendar strings, not `Date.toISOString()`, to avoid UTC shifting the intended bounds.
- **Processed ranges** in the DB use the same half-open convention for `ProcessedDateRange`; optional migration script: `python -m scripts.migrate_processed_ranges_exclusive_end` from `backend/`.
- Gmail requires OAuth 2.0 credentials from Google Cloud Console; Yahoo uses an app-specific password per account.
- spaCy model (for NLP): `pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl`
- Default dev ports: backend **8000**, frontend **3000** (Vite).
