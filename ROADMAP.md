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
- [ ] Account list with edit/delete actions
- [x] Credential validation before saving
- [x] Error handling for invalid credentials
- [ ] Connection testing button
- [ ] Account reconnection for expired tokens

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
- [ ] Concurrent analysis handling - Prevent/queue multiple simultaneous analyses
- [ ] Enhanced category chart UI for missing categories
- [ ] Responsive design improvements
- [ ] Dark mode support (optional)

#### 3. Export Functionality
**Status**: Not Started  
**Priority**: Medium  
**Description**: Allow users to export insights and data.

**Tasks**:
- [ ] CSV export for sender insights
- [ ] JSON export for full analysis data
- [ ] PDF report generation (optional)
- [ ] Date range selection for exports
- [ ] Export button in dashboard

#### 4. Email List, Filtering & Search
**Status**: Complete  
**Priority**: High  
**Description**: Browse and filter analyzed emails so users can reduce inbox overload and split mail by category/sender/date. Currently only aggregates (senders, categories) are shown—no list of individual emails.

**Tasks**:
- [x] **Email list API** – `GET /api/insights/emails` with pagination (`limit`, `offset`), returning email metadata + category per account. Response: subject, sender_email, sender_name, date_received, category, custom_category.
- [x] **Email list UI** – New "Emails" tab with paginated table (subject, sender, date, category, custom category). Empty state when no data.
- [x] **Filter by category** – List endpoint accepts `category=` (notifications, newsletters, social, shopping, work, personal, other). UI: category dropdown (includes custom categories).
- [x] **Filter by sender** – List endpoint accepts `sender_email=`. UI: "Emails" button in Top Senders → open email list filtered to that sender.
- [x] **Filter by date range** – List endpoint accepts `start_date`, `end_date`. UI: date-from / date-to inputs on the list view.
- [x] **Search by subject** – List endpoint accepts `q=` (substring match on subject). UI: search box in filter bar.
- [x] **Filter UI component** – Filter bar: category dropdown, sender input, date range, subject search, Apply. Debounced refetch on filter change.
- [x] **Category-click → filtered list** – Category chart segments clickable; clicking opens Emails tab with that category filter.

#### 5. Category-First Navigation & Custom Categories
**Status**: Complete  
**Priority**: High  
**Description**: Let users split emails into categories via navigation (click category → see list) and via user-defined categories (e.g. "Finance", "Urgent") by assigning senders to custom labels.

**Tasks**:
- [x] **Category-first entry** – From Insights, clicking a category opens the email list filtered to that category.
- [x] **Custom categories (user-defined)** – CustomCategory table (user_id, name). CRUD API: GET/POST/PATCH/DELETE `/api/insights/custom-categories`.
- [x] **Sender → custom category mapping** – SenderCategoryMapping table (user_id, sender_email, custom_category_id). POST/DELETE for assign/remove. One sender per custom category (reassign replaces).
- [x] **Filter by custom category** – Email list accepts `custom_category_id`; custom categories in filter dropdown alongside auto-categories.
- [x] **Custom category management UI** – Settings: CustomCategoriesManager (create, rename, delete). Top Senders: "Add to category" dropdown to assign sender to custom category.
- [ ] **Optional: subject rules** – Allow rules like "subject contains X" → custom category for future expansion.

#### 6. AI-Powered Sender Categorization
**Status**: Not Started  
**Priority**: High  
**Description**: Intelligently categorize senders using AI to suggest meaningful categories and subcategories. Builds on Custom Categories (section 5): AI suggests which senders belong in which user or system category.

**Tasks**:
- [ ] AI model integration for sender analysis (OpenAI/local LLM)
- [ ] Smart category detection based on sender domain and name patterns
- [ ] Main category suggestions:
  - **Essentials**: Insurance, rent, bank, utilities, government
  - **Life**: Shopping, food delivery, travel (Uber, Lyft), entertainment
  - **Software/Tech**: GitHub, cloud providers (AWS, GCP), domain registrars (GoDaddy), dev tools
  - **Work**: Company emails, clients, professional services
  - **Social**: Social networks, dating apps, community platforms
- [ ] Subcategory suggestions within each main category
- [ ] Bulk categorization of senders
- [ ] User ability to confirm/override AI suggestions
- [ ] Save custom categories per user
- [ ] Filter emails by AI-suggested categories
- [ ] Category-based email filter string generation

#### 7. Advanced Analytics
**Status**: Not Started  
**Priority**: Medium  
**Description**: Deeper insights and trend analysis.

**Tasks**:
- [ ] Trends over time (email volume charts)
- [ ] Sender relationship mapping
- [ ] Category trends (how categories change over time)
- [ ] Peak time analysis (best times to check email)
- [ ] Sender importance scoring
- [ ] Email thread analysis (if thread_id available)
- [ ] **Priority / importance buckets (optional)** – Simple priority or bucket (e.g. High / Medium / Low or "Needs reply" / "Read later" / "Archive"). Filter email list by priority. Can be manual (user marks) or heuristic at first (e.g. work + recent = high).

### Low Priority / Future Enhancements

#### 8. Multi-Account Comparison
**Status**: Not Started  
**Priority**: Low  
**Description**: Compare insights across multiple email accounts.

**Tasks**:
- [ ] Side-by-side account comparison
- [ ] Aggregate statistics across accounts
- [ ] Account-specific insights toggle

#### 9. Email Content Analysis
**Status**: Not Started  
**Priority**: Low  
**Description**: Analyze email body content (requires full email access).

**Tasks**:
- [ ] Sentiment analysis
- [ ] Keyword extraction
- [ ] Topic modeling
- [ ] Attachment detection
- [ ] Link extraction

#### 10. Notifications & Alerts
**Status**: Not Started  
**Priority**: Low  
**Description**: Notify users about email patterns.

**Tasks**:
- [ ] Unusual sender alerts
- [ ] High volume notifications
- [ ] Category change alerts
- [ ] Email digest summaries

#### 11. Performance Optimizations
**Status**: Not Started  
**Priority**: Low  
**Description**: Optimize for large-scale email processing.

**Tasks**:
- [ ] Batch processing optimization (larger chunks)
- [ ] Database indexing improvements
- [ ] Caching for frequently accessed insights
- [ ] Async email fetching improvements
- [ ] Memory optimization for large batches

#### 11. Performance Optimizations
**Status**: Not Started  
**Priority**: Low  
**Description**: Optimize for large-scale email processing.

**Tasks**:
- [ ] Batch processing optimization (larger chunks)
- [ ] Database indexing improvements
- [ ] Caching for frequently accessed insights
- [ ] Async email fetching improvements
- [ ] Memory optimization for large batches

#### 12. Testing
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

#### 12. Testing
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

#### 13. Deployment & DevOps
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

## 🐛 Known Issues

1. **Gmail API rate limits** - No handling for rate limit errors (429 responses)
2. **Large batch processing** - May timeout or fail for very large date ranges (10k+ emails)
3. **Frontend state persistence** - Page refresh resets state including running analysis
4. **Concurrent analysis handling** - No prevention of multiple simultaneous analyses
5. **Frontend timeout mismatch** - Frontend times out after 30s even when backend succeeds

---

## 📊 Feature Priority Matrix

| Feature | Priority | Effort | Impact | Status |
|---------|----------|--------|--------|--------|
| Email List, Filtering & Search | High | Medium | High | Complete |
| Category-First Navigation & Custom Categories | High | Medium | High | Complete |
| AI-Powered Sender Categorization | High | High | High | Not Started |
| UI/UX Enhancements | Medium | Medium | Medium | Partially Complete |
| Export Functionality | Medium | Low | Medium | Not Started |
| Testing | Medium | High | High | Not Started |
| Deployment & DevOps | Medium | Medium | High | Not Started |
| Advanced Analytics | Medium | High | Medium | Not Started |
| Multi-Account Comparison | Low | Medium | Low | Not Started |
| Content Analysis | Low | High | Low | Not Started |
| Performance Optimization | Low | High | Medium | Not Started |

---

## 🎯 Next Focus Areas

- ~~**Email list + filters**~~ ✅ Done – Paginated email list API and UI, filter by category/sender/date, subject search
- ~~**Category-first navigation**~~ ✅ Done – Click category in Insights → open email list filtered to that category
- ~~**Custom categories**~~ ✅ Done – User-defined categories and sender→category mapping; filter list by custom category
- AI-Powered Sender Categorization (suggestions building on custom categories)
- Frontend state persistence (restore analysis state on refresh)
- Concurrent analysis handling (prevent/queue multiple analyses)
- Export functionality (CSV/JSON)
- Testing infrastructure

---

## 📝 Notes

- All data is encrypted and stored locally
- Gmail requires OAuth 2.0 credentials from Google Cloud Console
- Yahoo requires app-specific password (not regular password)
- spaCy model must be installed separately: `pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl`
- Backend runs on port 8000, frontend on port 3000 (Vite default)
