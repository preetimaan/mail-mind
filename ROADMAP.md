# Mail Mind roadmap

This branch implements Mail Mind with a clean, local-first architecture.

## Scope decisions

- **No Emails browser tab** (explicitly out of scope).
- **Heuristic-only suggestions** (no AI dependency required).
- **UI**: keep the same **data** and flows as the original, but allow **simpler visuals** for now (upgrade later).

---

## Implemented (done)

### Core foundation
- [x] Repo scaffold: backend + frontend, dev scripts, `.gitignore`
- [x] Local username workspace (persisted in `localStorage`)

### Data model
- [x] `EmailAccount`
- [x] `AnalysisRun`
- [x] `ProcessedRange` (half-open)
- [x] `EmailMessage` (stub metadata for now)

### Analyze (runs + coverage)
- [x] Async analysis runs (in-process background runner)
- [x] Progress polling
- [x] Stop endpoint
- [x] Processed ranges list
- [x] Gaps endpoint + clickable gaps UI

### Insights (based on stored messages)
- [x] Summary endpoint (accounts + counts)
- [x] Top senders endpoint
- [x] Categories endpoint
- [x] Yearly frequency endpoint
- [x] Insights tab UI (simple list rendering)

---

## Parity backlog (from original branch)

### Provider / auth / reconnect flows
- [ ] **Gmail OAuth**
  - [ ] OAuth callback route + frontend handler
  - [ ] token storage (encrypted at rest)
  - [ ] “account added successfully” UX
- [ ] **Yahoo**
  - [ ] app-password capture + secure storage
  - [ ] connection validation + helpful errors
- [ ] **Reconnect + expired account handling**
  - [ ] mark account inactive on auth failure
  - [ ] reconnect CTA in UI
  - [ ] retry guard when account is expired/inactive

### Operational / data maintenance
- [ ] Recalculate insights (no re-fetch)
- [ ] Cleanup duplicates (after force re-analysis)
- [ ] (Optional) purge tools once we track sent/inbound

### Analysis semantics / robustness
- [ ] Force re-analysis toggle
- [ ] Large range chunking + chunk progress
- [ ] Define/implement cancel semantics (keep partial vs revert partial)

### UI parity (same data, simpler visuals)
- [ ] Recent analysis runs pagination (“Load more”)
- [ ] Retry failed runs
- [ ] Consistent status badges and clearer run state UX
- [ ] (Later) charts upgrade for Insights

### Documentation
- [ ] `DEVELOPER_SETUP.md`
- [ ] `USER_GUIDE.md`

---

## Next up (recommended order)

1. Docs (`DEVELOPER_SETUP.md`, `USER_GUIDE.md`)
2. Reconnect + retry guard plumbing
3. Retry + runs pagination
4. Force re-analysis + duplicates cleanup
5. Chunking + improved stop/cancel semantics
6. Provider integrations (Gmail then Yahoo) to replace stub data

