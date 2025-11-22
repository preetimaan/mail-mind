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
  - [x] Status tracking (pending, processing, completed, failed)
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
  - [x] `GET /api/analysis/runs` - List analysis runs
  - [x] `GET /api/analysis/runs/{id}` - Get run status
- [x] Insights
  - [x] `GET /api/insights/summary` - Overall summary
  - [x] `GET /api/insights/senders` - Top senders and patterns
  - [x] `GET /api/insights/categories` - Category distribution
  - [x] `GET /api/insights/frequency` - Frequency patterns
  - [x] `GET /api/insights/processed-ranges` - Processed date ranges

### Frontend
- [x] React + TypeScript setup with Vite
- [x] Dashboard page
  - [x] Username input
  - [x] Account selector component
  - [x] Date range picker
  - [x] Analysis trigger with loading states
- [x] Visualization components
  - [x] Stats grid (summary statistics)
  - [x] Sender chart (top senders with percentages)
  - [x] Category chart (category distribution)
  - [x] Frequency chart (hourly/weekly patterns)
  - [x] Processed ranges display
- [x] Real-time status updates
  - [x] Polling for analysis completion
  - [x] Error and success message display
- [x] API client with TypeScript types

### Documentation
- [x] README.md with setup instructions
- [x] QUICKSTART.md guide
- [x] API documentation (via FastAPI Swagger UI)

### Bug Fixes
- [x] Fixed `analysis_run_id` null constraint bug

---

## 🚧 In Progress / Next Steps

### High Priority

#### 1. Email Account Management UI
**Status**: Not Started  
**Priority**: High  
**Description**: Currently accounts must be added via API/curl. Need a user-friendly interface.

**Tasks**:
- [ ] Add account form component (provider selection, email input, credentials)
- [ ] Gmail OAuth flow UI (redirect handling)
- [ ] Yahoo credentials form (email + app password)
- [ ] Account list with edit/delete actions
- [ ] Credential validation before saving
- [ ] Error handling for invalid credentials

#### 2. Gmail OAuth Callback Handler
**Status**: Not Started  
**Priority**: High  
**Description**: Implement OAuth redirect endpoint for Gmail authentication.

**Tasks**:
- [ ] Create `/api/oauth/callback` endpoint
- [ ] Handle OAuth state verification
- [ ] Exchange authorization code for tokens
- [ ] Store encrypted credentials
- [ ] Redirect to frontend with success/error
- [ ] Handle token refresh on expiration

#### 3. Enhanced Error Handling
**Status**: Not Started  
**Priority**: Medium-High  
**Description**: Better error messages and recovery mechanisms.

**Tasks**:
- [ ] Structured error responses from API
- [ ] User-friendly error messages in frontend
- [ ] Retry logic for failed API calls
- [ ] Connection timeout handling
- [ ] Rate limiting awareness (Gmail API limits)
- [ ] Graceful degradation when services unavailable

### Medium Priority

#### 4. UI/UX Enhancements
**Status**: Not Started  
**Priority**: Medium  
**Description**: Improve visual design and user experience.

**Tasks**:
- [ ] Add loading spinner for in-progress analysis
- [ ] Improve overall UI design (modern, clean interface)
- [ ] Better visual feedback for missing/empty data
- [ ] Enhanced category chart UI for missing categories
- [ ] Responsive design improvements
- [ ] Dark mode support (optional)

#### 5. Yearly Frequency Analysis
**Status**: Not Started  
**Priority**: Medium  
**Description**: Add yearly frequency summary with data availability indicators.

**Tasks**:
- [ ] Yearly aggregation endpoint (`/api/insights/frequency/yearly`)
- [ ] Year-over-year comparison chart
- [ ] Visual indicators for missing data periods
- [ ] Year selector component
- [ ] Data completeness indicators (show gaps in data)
- [ ] Summary statistics per year

#### 6. Export Functionality
**Status**: Not Started  
**Priority**: Medium  
**Description**: Allow users to export insights and data.

**Tasks**:
- [ ] CSV export for sender insights
- [ ] JSON export for full analysis data
- [ ] PDF report generation (optional)
- [ ] Date range selection for exports
- [ ] Export button in dashboard

#### 7. Email Filtering & Search
**Status**: Not Started  
**Priority**: Medium  
**Description**: Filter and search through analyzed emails.

**Tasks**:
- [ ] Filter by sender
- [ ] Filter by category
- [ ] Filter by date range
- [ ] Search by subject line
- [ ] Filter UI component
- [ ] Search results display

#### 8. Advanced Analytics
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

### Low Priority / Future Enhancements

#### 7. Multi-Account Comparison
**Status**: Not Started  
**Priority**: Low  
**Description**: Compare insights across multiple email accounts.

**Tasks**:
- [ ] Side-by-side account comparison
- [ ] Aggregate statistics across accounts
- [ ] Account-specific insights toggle

#### 8. Email Content Analysis
**Status**: Not Started  
**Priority**: Low  
**Description**: Analyze email body content (requires full email access).

**Tasks**:
- [ ] Sentiment analysis
- [ ] Keyword extraction
- [ ] Topic modeling
- [ ] Attachment detection
- [ ] Link extraction

#### 9. Notifications & Alerts
**Status**: Not Started  
**Priority**: Low  
**Description**: Notify users about email patterns.

**Tasks**:
- [ ] Unusual sender alerts
- [ ] High volume notifications
- [ ] Category change alerts
- [ ] Email digest summaries

#### 10. Performance Optimizations
**Status**: Not Started  
**Priority**: Low  
**Description**: Optimize for large-scale email processing.

**Tasks**:
- [ ] Batch processing optimization (larger chunks)
- [ ] Database indexing improvements
- [ ] Caching for frequently accessed insights
- [ ] Async email fetching improvements
- [ ] Memory optimization for large batches

#### 11. Testing
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

#### 12. Deployment & DevOps
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

1. **Analysis Run ID Bug** - ✅ Fixed
2. **No progress tracking** - Analysis runs don't show progress percentage during processing
3. **No retry mechanism** - Failed analysis runs require manual restart
4. **Gmail API rate limits** - No handling for rate limit errors (429 responses)
5. **Large batch processing** - May timeout or fail for very large date ranges (10k+ emails)

---

## 📊 Feature Priority Matrix

| Feature | Priority | Effort | Impact | Status |
|---------|----------|--------|--------|--------|
| Account Management UI | High | Medium | High | Not Started |
| OAuth Callback | High | Low | High | Not Started |
| Error Handling | High | Medium | High | Not Started |
| UI/UX Enhancements | Medium | Medium | Medium | Not Started |
| Yearly Frequency Analysis | Medium | Medium | Medium | Not Started |
| Export Functionality | Medium | Low | Medium | Not Started |
| Email Filtering | Medium | Medium | Medium | Not Started |
| Advanced Analytics | Medium | High | Medium | Not Started |
| Testing | Medium | High | High | Not Started |
| Multi-Account Comparison | Low | Medium | Low | Not Started |
| Content Analysis | Low | High | Low | Not Started |
| Performance Optimization | Low | High | Medium | Not Started |

---

## 🎯 Current Sprint Goals

1. ✅ Fix analysis_run_id bug
2. ⏳ Implement account management UI
3. ⏳ Add OAuth callback handler
4. ⏳ Improve error handling
5. ⏳ Add loading spinner and UI improvements
6. ⏳ Implement yearly frequency analysis

---

## 🎨 User Experience Improvements

### Phase 1: Quick Wins (Easy to Implement)

#### 1. **Auto-Detect Username from Email**
- When adding account, suggest username based on email
- Example: `john@gmail.com` → suggest username `john`
- Still allow manual override

#### 2. **Remember Username in Browser**
- Store username in `localStorage`
- Auto-fill on page load
- "Remember me" checkbox

#### 3. **Username Validation & Help Text**
- Add placeholder: "e.g., your_name or email_prefix"
- Show help text: "This groups your accounts together"
- Validate format (alphanumeric + underscore)

#### 4. **Show Username in Account List**
- Display which username each account belongs to
- Help users remember what they used

### Phase 2: Account Management UI (Medium Effort)

#### 1. **Add Account Button in Dashboard**
- Button: "Add Email Account"
- Opens modal/form
- Two tabs: "Gmail" and "Yahoo"

#### 2. **Gmail OAuth Flow in UI**
- **Step 1**: Enter Gmail address
- **Step 2**: Click "Connect Gmail"
- **Step 3**: Redirect to Google OAuth (or popup)
- **Step 4**: User authorizes
- **Step 5**: Callback handles token exchange
- **Step 6**: Account added automatically

**Backend Changes Needed:**
- Add `/api/oauth/authorize` endpoint (generates OAuth URL)
- Add `/api/oauth/callback` endpoint (handles OAuth callback)
- Store OAuth state in session/cache

#### 3. **Yahoo Account Form**
- Simple form: Email + App Password
- Instructions inline: "How to get app password"
- Validate credentials before saving

#### 4. **Account Management**
- List all accounts in dashboard
- Edit account (update credentials)
- Delete account
- Test connection button

### Phase 3: Better User Experience (More Complex)

#### 1. **Session-Based Authentication**
- Replace username with session tokens
- Auto-login after adding first account
- "Switch User" option

#### 2. **Email-Based Username**
- Use email as primary identifier
- Username becomes optional alias
- Easier to remember

#### 3. **Account Groups/Profiles**
- Create "profiles" (work, personal, etc.)
- Group accounts by profile
- Switch between profiles

#### 4. **Simplified First-Time Setup**
- Onboarding wizard:
  1. Welcome screen
  2. "Add your first email account"
  3. Guided OAuth flow
  4. Quick analysis of recent emails
  5. Show results

### Current User Journey vs. Improved Journey

**Current Journey (Complex):**
```
1. Read ACCOUNT_SETUP.md (10 min)
2. Set up Google Cloud Project (5 min)
3. Get OAuth tokens via script (5 min)
4. Add to .env file (2 min)
5. Run add_gmail_account.py (1 min)
6. Open dashboard
7. Enter username (hope you remember it!)
8. Select account
9. Analyze
```
**Total: ~25 minutes, technical knowledge required**

**Improved Journey (Simple):**
```
1. Open dashboard
2. Click "Add Account"
3. Select "Gmail"
4. Enter email
5. Click "Connect" → OAuth popup
6. Authorize → Done!
7. Account appears automatically
8. Click "Analyze"
```
**Total: ~2 minutes, no technical knowledge**

### Priority Recommendations

**Must Have (P0):**
1. ✅ Remember username in browser
2. ✅ Add account UI (at least for Yahoo)
3. ✅ OAuth callback endpoint for Gmail

**Should Have (P1):**
1. Account list with edit/delete
2. Connection testing
3. Better error messages

**Nice to Have (P2):**
1. Onboarding wizard
2. Profile system
3. Session management

---

## 📝 Notes

- All data is encrypted and stored locally
- Gmail requires OAuth 2.0 credentials from Google Cloud Console
- Yahoo requires app-specific password (not regular password)
- spaCy model must be installed separately: `pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl`
- Backend runs on port 8000, frontend on port 3000 (Vite default)
