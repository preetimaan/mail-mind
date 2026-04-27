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
- [x] **Gmail OAuth (local-only skeleton)**
  - [x] OAuth callback route + frontend handler
  - [x] token storage (encrypted at rest)
  - [x] redirect back to Settings with status banner
  - [ ] refresh-token reuse + provider revoke (later)
- [x] **Yahoo (local-only skeleton)**
  - [x] app-password capture + secure storage
  - [x] connection validation (IMAP login)
- [x] **Reconnect + expired account handling**
  - [x] mark account inactive on auth failure (during fetch)
  - [x] reconnect CTA in UI (Connect buttons per provider)
  - [x] retry guard when account is expired/inactive (analysis requires connected)

### Operational / data maintenance
- [x] Recalculate insights (no re-fetch) (insights are computed from stored `EmailMessage`)
- [x] Cleanup duplicates safety tool (maintenance dedupe endpoint)
- [ ] (Optional) purge tools once we track sent/inbound

### Analysis semantics / robustness
- [x] Force re-analysis toggle
- [x] Large range chunking + chunk progress
- [x] Define/implement cancel semantics (revert partial writes)
- [ ] Provider-backed stop semantics (later; depends on provider fetch behavior)

### UI parity (same data, simpler visuals)
- [x] Recent analysis runs pagination (“Load more”)
- [x] Retry failed runs
- [x] Consistent status badges and clearer run state UX
- [ ] (Later) charts upgrade for Insights

### Documentation
- [x] `DEVELOPER_SETUP.md`
- [x] `USER_GUIDE.md`

---

## Next up (recommended order)

1. Provider integrations to replace stub data (Gmail + Yahoo fetch hardening)
2. Provider revoke/disconnect polish + rotation UX
3. Optional: sent mail / outbound tracking
4. UI visual upgrades (charts, richer layouts)

