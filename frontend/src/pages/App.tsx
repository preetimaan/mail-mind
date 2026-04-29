import { useEffect, useMemo, useRef, useState } from 'react'
import {
  api,
  type AnalysisRun,
  type CategoryInsights,
  type EmailAccount,
  type GmailFilterRule,
  type GmailLabel,
  type InsightsSummary,
  type ProcessedRange,
  type ProcessedRangeGap,
  type SenderInsights,
  type SenderMessageSample,
  type YearlyFrequencyInsights,
} from '../api/client'

type Tab = 'analysis' | 'insights' | 'filters' | 'settings'

const TAB_LABELS: Record<Tab, string> = {
  analysis: 'Analyze',
  insights: 'Insights',
  filters: 'Labels & Filters',
  settings: 'Settings',
}

function yyyyMmDd(d: Date) {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

function addDays(dateStr: string, days: number) {
  const d = new Date(`${dateStr}T00:00:00`)
  d.setDate(d.getDate() + days)
  return yyyyMmDd(d)
}

function providerLabel(p: EmailAccount['provider']): string {
  return p === 'gmail' ? 'Gmail' : 'Yahoo'
}

/** Consumer domains only; Google Workspace / custom domains need a manual provider pick. */
function suggestedProviderFromEmail(email: string): 'gmail' | 'yahoo' | null {
  const m = email.trim().toLowerCase().match(/@([^@\s]+)$/)
  if (!m) return null
  const host = m[1]
  if (['yahoo.com', 'ymail.com', 'rocketmail.com'].includes(host)) return 'yahoo'
  if (['gmail.com', 'googlemail.com'].includes(host)) return 'gmail'
  return null
}

export default function App() {
  const [username, setUsername] = useState('')
  const [loggedIn, setLoggedIn] = useState(false)
  const [tab, setTab] = useState<Tab>('analysis')
  const [oauthBanner, setOauthBanner] = useState<string | null>(null)

  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null)

  const canUseAccount = useMemo(() => loggedIn && accounts.length > 0, [loggedIn, accounts.length])
  const selectedAccount = useMemo(
    () => (selectedAccountId ? accounts.find((a) => a.id === selectedAccountId) ?? null : null),
    [accounts, selectedAccountId],
  )

  const [startDate, setStartDate] = useState(yyyyMmDd(new Date(Date.now() - 1000 * 60 * 60 * 24 * 7)))
  // End field is end_date_exclusive (first day NOT in range). Default = day after today → same as old “inclusive today”.
  const [endDate, setEndDate] = useState(addDays(yyyyMmDd(new Date()), 1))
  const [runs, setRuns] = useState<AnalysisRun[]>([])
  const [runsOffset, setRunsOffset] = useState(0)
  const [hasMoreRuns, setHasMoreRuns] = useState(false)
  const [loadingMoreRuns, setLoadingMoreRuns] = useState(false)
  const [processedRanges, setProcessedRanges] = useState<ProcessedRange[]>([])
  const [gaps, setGaps] = useState<ProcessedRangeGap[]>([])
  const [runError, setRunError] = useState<string | null>(null)
  const [runBusy, setRunBusy] = useState(false)
  const [forceReanalysis, setForceReanalysis] = useState(false)
  const [inboxOnly, setInboxOnly] = useState(false)

  const [summary, setSummary] = useState<InsightsSummary | null>(null)
  const [senderInsights, setSenderInsights] = useState<SenderInsights | null>(null)
  const [categoryInsights, setCategoryInsights] = useState<CategoryInsights | null>(null)
  const [yearlyInsights, setYearlyInsights] = useState<YearlyFrequencyInsights | null>(null)
  const [insightsError, setInsightsError] = useState<string | null>(null)
  const [gmailLabels, setGmailLabels] = useState<GmailLabel[] | null>(null)
  const [gmailFilters, setGmailFilters] = useState<GmailFilterRule[] | null>(null)
  const [gmailFiltersError, setGmailFiltersError] = useState<string | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem('mailmind_username') ?? ''
    if (saved.trim().length > 0) {
      setUsername(saved)
      setLoggedIn(true)
    }

    const url = new URL(window.location.href)
    const tabParam = url.searchParams.get('tab')
    const oauth = url.searchParams.get('oauth')
    const status = url.searchParams.get('status')
    const message = url.searchParams.get('message')
    if (oauth === 'gmail' && status) {
      if (status === 'ok') setOauthBanner('Gmail connected.')
      else setOauthBanner(`Gmail connect failed${message ? `: ${message}` : ''}`)
      if (tabParam === 'settings') setTab('settings')
      url.searchParams.delete('oauth')
      url.searchParams.delete('tab')
      url.searchParams.delete('status')
      url.searchParams.delete('message')
      url.searchParams.delete('account_id')
      window.history.replaceState({}, '', url.toString())
    }
  }, [])

  useEffect(() => {
    if (!loggedIn) return
    void (async () => {
      const data = await api.listAccounts(username)
      setAccounts(data)
      if (data.length > 0 && selectedAccountId === null) setSelectedAccountId(data[0].id)
    })()
  }, [loggedIn, username])

  useEffect(() => {
    if (!loggedIn || !selectedAccountId) return
    void (async () => {
      const data = await api.listRuns(selectedAccountId, 5, 0)
      setRuns(data.runs)
      setRunsOffset(data.runs.length)
      setHasMoreRuns(data.has_more)
      const ranges = await api.listProcessedRanges(selectedAccountId)
      setProcessedRanges(ranges)
      const gapsData = await api.listProcessedRangeGaps(selectedAccountId)
      setGaps(gapsData)
    })()
  }, [loggedIn, selectedAccountId])

  useEffect(() => {
    if (!loggedIn) return
    void (async () => {
      try {
        const data = await api.getSummary(username, selectedAccountId)
        setSummary(data)
      } catch (e: any) {
        setSummary(null)
      }
    })()
  }, [loggedIn, username, selectedAccountId])

  useEffect(() => {
    if (!loggedIn || !selectedAccountId) return
    if (tab !== 'insights') return

    setInsightsError(null)
    void (async () => {
      try {
        const [senders, cats, yearly] = await Promise.all([
          api.getSenders(selectedAccountId),
          api.getCategories(selectedAccountId),
          api.getYearlyFrequency(selectedAccountId),
        ])
        setSenderInsights(senders)
        setCategoryInsights(cats)
        setYearlyInsights(yearly)
      } catch (e: any) {
        setInsightsError(e?.message ?? 'Failed to load insights')
        setSenderInsights(null)
        setCategoryInsights(null)
        setYearlyInsights(null)
      }
    })()
  }, [loggedIn, selectedAccountId, tab])

  useEffect(() => {
    if (!loggedIn || !selectedAccountId || tab !== 'filters') return
    if (selectedAccount?.provider !== 'gmail') {
      setGmailLabels([])
      setGmailFilters([])
      setGmailFiltersError('Labels & Filters is available for Gmail accounts.')
      return
    }
    setGmailFiltersError(null)
    void (async () => {
      try {
        const data = await api.getGmailLabelsFilters(selectedAccountId)
        setGmailLabels(data.labels)
        setGmailFilters(data.filters)
        setGmailFiltersError(data.filters_error)
      } catch (e: any) {
        setGmailLabels(null)
        setGmailFilters(null)
        setGmailFiltersError(e?.message ?? 'Failed to load Gmail labels/filters')
      }
    })()
  }, [loggedIn, selectedAccountId, tab, selectedAccount?.provider])

  useEffect(() => {
    if (!loggedIn || !selectedAccountId) return
    if (tab !== 'analysis') return

    const hasRunning = runs.some((r) => r.status === 'pending' || r.status === 'processing')
    if (!hasRunning) return

    const id = window.setInterval(() => {
      void (async () => {
        const data = await api.listRuns(selectedAccountId, 5, 0)
        setRuns(data.runs)
        const ranges = await api.listProcessedRanges(selectedAccountId)
        setProcessedRanges(ranges)
        const gapsData = await api.listProcessedRangeGaps(selectedAccountId)
        setGaps(gapsData)
      })()
    }, 750)
    return () => window.clearInterval(id)
  }, [loggedIn, selectedAccountId, tab, runs])

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Arial', padding: '1.5rem', maxWidth: 1000, margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <h1 style={{ margin: 0 }}>Mail Mind</h1>
        {loggedIn ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 600 }}>{username}</span>
            <button
              onClick={() => {
                localStorage.removeItem('mailmind_username')
                setLoggedIn(false)
                setUsername('')
                setAccounts([])
                setSelectedAccountId(null)
              }}
            >
              Log out
            </button>
          </div>
        ) : null}
      </header>

      {!loggedIn ? (
        <div style={{ marginTop: '1.5rem', border: '1px solid #e5e7eb', borderRadius: 12, padding: '1rem' }}>
          <h2 style={{ marginTop: 0 }}>Login</h2>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="username"
              style={{ flex: 1, padding: '0.5rem 0.75rem' }}
            />
            <button
              onClick={() => {
                const u = username.trim()
                if (u.length === 0) return
                localStorage.setItem('mailmind_username', u)
                setUsername(u)
                setLoggedIn(true)
              }}
              disabled={username.trim().length === 0}
            >
              Continue
            </button>
          </div>
        </div>
      ) : (
        <>
          <nav style={{ display: 'flex', gap: 8, marginTop: '1.25rem' }}>
            {(['analysis', 'insights', 'filters', 'settings'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: 10,
                  border: '1px solid #e5e7eb',
                  background: tab === t ? '#111827' : 'white',
                  color: tab === t ? 'white' : '#111827',
                  cursor: 'pointer',
                }}
              >
                {TAB_LABELS[t]}
              </button>
            ))}
          </nav>

          <section style={{ marginTop: '1.25rem', border: '1px solid #e5e7eb', borderRadius: 12, padding: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
              <h2 style={{ margin: 0 }}>{TAB_LABELS[tab]}</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <label style={{ fontSize: 14, color: '#374151' }}>Account</label>
                <select
                  value={selectedAccountId ?? ''}
                  onChange={(e) => setSelectedAccountId(Number(e.target.value))}
                  disabled={!canUseAccount}
                >
                  <option value="" disabled>
                    {accounts.length === 0 ? 'No accounts' : 'Select'}
                  </option>
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {providerLabel(a.provider)} • {a.email}
                      {a.is_connected ? '' : ' (not connected)'}
                      {a.is_active ? '' : ' (inactive)'}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {selectedAccount && !selectedAccount.is_active ? (
              <div style={{ marginTop: 10, padding: 10, border: '1px solid #f59e0b', borderRadius: 10, background: '#fffbeb' }}>
                <div style={{ fontSize: 13, color: '#92400e' }}>
                  <strong>Account inactive.</strong> Connect it in Settings before running analysis.
                </div>
              </div>
            ) : selectedAccount && !selectedAccount.is_connected ? (
              <div style={{ marginTop: 10, padding: 10, border: '1px solid #f59e0b', borderRadius: 10, background: '#fffbeb' }}>
                <div style={{ fontSize: 13, color: '#92400e' }}>
                  <strong>Account not connected.</strong> Connect it in Settings before running analysis.
                </div>
              </div>
            ) : null}

            {summary && selectedAccountId ? (
              <div
                style={{
                  marginTop: 12,
                  padding: 10,
                  border: '1px solid #e5e7eb',
                  borderRadius: 10,
                  background: '#f9fafb',
                  display: 'flex',
                  gap: 16,
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ fontSize: 13, color: '#374151' }}>
                  <strong>{summary.current_account.account_emails}</strong> emails
                </div>
                <div style={{ fontSize: 13, color: '#374151' }}>
                  <strong>{summary.current_account.account_senders}</strong> senders
                </div>
                <div style={{ fontSize: 13, color: '#374151' }}>
                  <strong>{summary.current_account.processed_ranges}</strong> processed ranges
                </div>
              </div>
            ) : null}

            {tab === 'settings' ? (
              <Settings
                username={username}
                accounts={accounts}
                selectedAccountId={selectedAccountId}
                banner={oauthBanner}
                clearBanner={() => setOauthBanner(null)}
                onAccountsChange={(a) => {
                  setAccounts(a)
                  if (a.length === 0) setSelectedAccountId(null)
                  if (selectedAccountId && !a.some((x) => x.id === selectedAccountId)) setSelectedAccountId(null)
                }}
              />
            ) : tab === 'analysis' ? (
              <Analyze
                accountId={selectedAccountId}
                accountConnected={!!selectedAccount?.is_connected && !!selectedAccount?.is_active}
                startDate={startDate}
                endDate={endDate}
                setStartDate={setStartDate}
                setEndDate={setEndDate}
                forceReanalysis={forceReanalysis}
                setForceReanalysis={setForceReanalysis}
                inboxOnly={inboxOnly}
                setInboxOnly={setInboxOnly}
                runs={runs}
                setRuns={setRuns}
                hasMoreRuns={hasMoreRuns}
                loadingMoreRuns={loadingMoreRuns}
                loadMoreRuns={async () => {
                  if (!selectedAccountId) return
                  if (loadingMoreRuns || !hasMoreRuns) return
                  setLoadingMoreRuns(true)
                  try {
                    const data = await api.listRuns(selectedAccountId, 5, runsOffset)
                    setRuns((prev) => [...prev, ...data.runs])
                    setRunsOffset((prev) => prev + data.runs.length)
                    setHasMoreRuns(data.has_more)
                  } finally {
                    setLoadingMoreRuns(false)
                  }
                }}
                processedRanges={processedRanges}
                gaps={gaps}
                busy={runBusy}
                setBusy={setRunBusy}
                error={runError}
                setError={setRunError}
              />
            ) : tab === 'insights' ? (
              <Insights
                accountId={selectedAccountId}
                error={insightsError}
                senders={senderInsights}
                categories={categoryInsights}
                yearly={yearlyInsights}
              />
            ) : tab === 'filters' ? (
              <LabelsAndFilters
                account={selectedAccount}
                labels={gmailLabels}
                filters={gmailFilters}
                filtersError={gmailFiltersError}
              />
            ) : (
              <div style={{ marginTop: 12, color: '#6b7280' }}>
                Stub UI. Next: wire analysis runs + insights.
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}

function TopSenderRow({
  accountId,
  email,
  name,
  count,
}: {
  accountId: number
  email: string
  name: string | null
  count: number
}) {
  const [expanded, setExpanded] = useState(false)
  const [samples, setSamples] = useState<SenderMessageSample[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)

  const listIds = useMemo(() => {
    const out = new Set<string>()
    for (const s of samples ?? []) {
      const v = s.headers?.['list-id']
      if (v && v.trim()) out.add(v.trim())
    }
    return Array.from(out)
  }, [samples])

  async function copyText(label: string, text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(label)
      window.setTimeout(() => setCopied((cur) => (cur === label ? null : cur)), 1200)
    } catch {
      setErr('Clipboard unavailable in this browser/session.')
    }
  }

  async function onToggle() {
    if (expanded) {
      setExpanded(false)
      return
    }
    setExpanded(true)
    if (samples !== null) return
    setLoading(true)
    setErr(null)
    try {
      const res = await api.getSenderSamples(accountId, email)
      setSamples(res.samples)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ paddingBottom: 8, marginBottom: 8, borderBottom: '1px solid #f3f4f6' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 240 }}>
          {name ? <div style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>{name}</div> : null}
          <div style={{ fontSize: 12, color: '#6b7280', wordBreak: 'break-all' }}>{email}</div>
          <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => void copyText('search', `from:${email}`)}
              style={{ fontSize: 12, padding: '4px 8px', cursor: 'pointer' }}
            >
              Copy search
            </button>
            <button
              type="button"
              onClick={() =>
                void copyText(
                  'filter',
                  `matches:from:${email}\naction:apply-label:ToReview\naction:never-spam:false\naction:archive:false`,
                )
              }
              style={{ fontSize: 12, padding: '4px 8px', cursor: 'pointer' }}
            >
              Copy filter
            </button>
            <button type="button" onClick={onToggle} style={{ fontSize: 12, padding: '4px 8px', cursor: 'pointer' }}>
              {expanded ? 'Hide' : 'Headers'}
            </button>
          </div>
        </div>
        <div style={{ fontSize: 13, color: '#6b7280', flexShrink: 0 }}>{count}</div>
      </div>
      {copied ? <div style={{ marginTop: 6, fontSize: 12, color: '#059669' }}>Copied {copied} query.</div> : null}
      {expanded ? (
        <div style={{ marginTop: 8, fontSize: 12, color: '#4b5563' }}>
          {loading ? <div style={{ color: '#6b7280' }}>Loading…</div> : null}
          {err ? <div style={{ color: '#b91c1c' }}>{err}</div> : null}
          {!loading && !err && samples?.length === 0 ? <div style={{ color: '#6b7280' }}>No rows.</div> : null}
          {samples?.map((row, i) => (
            <div key={i} style={{ marginTop: 10, padding: 8, background: '#f9fafb', borderRadius: 6 }}>
              <div style={{ color: '#6b7280', marginBottom: 4 }}>{row.received_at}</div>
              <div style={{ fontWeight: 500, marginBottom: 6 }}>{row.subject || '(no subject)'}</div>
              {row.headers && Object.keys(row.headers).length > 0 ? (
                <pre
                  style={{
                    margin: 0,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    fontSize: 11,
                    lineHeight: 1.45,
                    fontFamily: 'ui-monospace, monospace',
                  }}
                >
                  {Object.keys(row.headers)
                    .sort()
                    .map((k) => `${k}: ${row.headers![k]}`)
                    .join('\n')}
                </pre>
              ) : (
                <div style={{ color: '#9ca3af', fontStyle: 'italic' }}>
                  No header snapshot (older analysis). Run analysis again on a date range that includes these messages to
                  capture From / To / Reply-To / Return-Path, etc.
                </div>
              )}
            </div>
          ))}
          {listIds.length > 0 ? (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 6 }}>Detected list ids</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {listIds.map((id) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => void copyText('list-id', `list:${id}`)}
                    style={{ fontSize: 12, padding: '4px 8px', cursor: 'pointer' }}
                  >
                    Copy list:{id}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

function LabelsAndFilters({
  account,
  labels,
  filters,
  filtersError,
}: {
  account: EmailAccount | null
  labels: GmailLabel[] | null
  filters: GmailFilterRule[] | null
  filtersError: string | null
}) {
  const [copied, setCopied] = useState<string | null>(null)

  async function copyText(text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(text)
      window.setTimeout(() => setCopied((cur) => (cur === text ? null : cur)), 1200)
    } catch {
      // ignore clipboard failures in read-only contexts
    }
  }

  if (!account) return <div style={{ marginTop: 12, color: '#6b7280' }}>Select an account.</div>
  if (account.provider !== 'gmail') {
    return <div style={{ marginTop: 12, color: '#6b7280' }}>Labels & Filters is currently available for Gmail accounts.</div>
  }

  const labelById = new Map((labels ?? []).map((l) => [l.id, l.name]))

  return (
    <div style={{ marginTop: 12 }}>
      {filtersError ? <div style={{ color: '#b91c1c', marginBottom: 8 }}>{filtersError}</div> : null}
      {copied ? <div style={{ color: '#059669', marginBottom: 8, fontSize: 12 }}>Copied filter query.</div> : null}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 12 }}>
        <div style={{ padding: 12, border: '1px solid #e5e7eb', borderRadius: 10 }}>
          <h3 style={{ margin: '0 0 8px 0' }}>Labels</h3>
          {!labels ? (
            <div style={{ color: '#6b7280' }}>Loading…</div>
          ) : labels.length === 0 ? (
            <div style={{ color: '#6b7280' }}>No labels found.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {labels.map((l) => (
                <div key={l.id} style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                  <div style={{ fontSize: 13, color: '#374151' }}>
                    {l.name} <span style={{ color: '#9ca3af' }}>({l.type})</span>
                  </div>
                  <div style={{ fontSize: 12, color: '#6b7280' }}>
                    {l.messages_total == null ? '—' : l.messages_total}
                    {l.messages_unread == null ? '' : ` (${l.messages_unread} unread)`}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div style={{ padding: 12, border: '1px solid #e5e7eb', borderRadius: 10 }}>
          <h3 style={{ margin: '0 0 8px 0' }}>Filters</h3>
          {!filters ? (
            <div style={{ color: '#6b7280' }}>Loading…</div>
          ) : filters.length === 0 ? (
            <div style={{ color: '#6b7280' }}>No Gmail filters found.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 520, overflowY: 'auto', paddingRight: 4 }}>
              {filters.map((f) => {
                const parts: string[] = []
                if (f.criteria.from) parts.push(`from:${f.criteria.from}`)
                if (f.criteria.to) parts.push(`to:${f.criteria.to}`)
                if (f.criteria.subject) parts.push(`subject:(${f.criteria.subject})`)
                if (f.criteria.query) parts.push(f.criteria.query)
                if (f.criteria.negated_query) parts.push(`-(${f.criteria.negated_query})`)
                const query = parts.join(' ').trim() || '(no criteria)'
                const addLabels = (f.action.add_label_ids || []).map((id) => labelById.get(id) || id)
                const removeLabels = (f.action.remove_label_ids || []).map((id) => labelById.get(id) || id)
                return (
                  <div key={f.id} style={{ border: '1px solid #f3f4f6', borderRadius: 8, padding: 8 }}>
                    <div style={{ fontSize: 12, color: '#374151', marginBottom: 6, wordBreak: 'break-word' }}>{query}</div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>
                      +[{addLabels.join(', ') || 'none'}] / -[{removeLabels.join(', ') || 'none'}]
                    </div>
                    <div style={{ marginTop: 6 }}>
                      <button type="button" style={{ fontSize: 12, padding: '4px 8px', cursor: 'pointer' }} onClick={() => void copyText(query)}>
                        Copy query
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Insights({
  accountId,
  error,
  senders,
  categories,
  yearly,
}: {
  accountId: number | null
  error: string | null
  senders: SenderInsights | null
  categories: CategoryInsights | null
  yearly: YearlyFrequencyInsights | null
}) {
  if (!accountId) return <div style={{ marginTop: 12, color: '#6b7280' }}>Select an account to view insights.</div>

  return (
    <div style={{ marginTop: 12 }}>
      {error ? <div style={{ color: '#b91c1c', marginBottom: 8 }}>{error}</div> : null}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
        <div style={{ padding: 12, border: '1px solid #e5e7eb', borderRadius: 10 }}>
          <h3 style={{ margin: '0 0 8px 0' }}>Top senders</h3>
          <p style={{ margin: '0 0 10px 0', fontSize: 12, color: '#6b7280', lineHeight: 1.4 }}>
            Counts use the parsed <strong>From</strong> address. Your own address often ranks high (mail to yourself,
            receipts, Google account mail, sent copies in the date window). Use <strong>Headers</strong> on a row to see
            recent sample messages and selected RFC headers.
          </p>
          {!senders ? (
            <div style={{ color: '#6b7280' }}>Loading…</div>
          ) : senders.total_emails === 0 ? (
            <div style={{ color: '#6b7280' }}>No data yet. Run an analysis.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {senders.top_senders.map((s) => (
                <TopSenderRow key={s.email} accountId={accountId} email={s.email} name={s.name} count={s.count} />
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: 12, border: '1px solid #e5e7eb', borderRadius: 10 }}>
          <h3 style={{ margin: '0 0 8px 0' }}>Top domains</h3>
          {!senders ? (
            <div style={{ color: '#6b7280' }}>Loading…</div>
          ) : senders.top_domains.length === 0 ? (
            <div style={{ color: '#6b7280' }}>No data yet. Run an analysis.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {senders.top_domains.map((d) => (
                <div key={d.domain} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <div style={{ fontSize: 13, color: '#374151', wordBreak: 'break-all' }}>{d.domain}</div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>{d.count}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: 12, border: '1px solid #e5e7eb', borderRadius: 10 }}>
          <h3 style={{ margin: '0 0 8px 0' }}>Categories</h3>
          {!categories ? (
            <div style={{ color: '#6b7280' }}>Loading…</div>
          ) : categories.total === 0 ? (
            <div style={{ color: '#6b7280' }}>No data yet. Run an analysis.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {categories.categories.map((c) => (
                <div key={c.category} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <div style={{ fontSize: 13, color: '#374151' }}>{c.category}</div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>
                    {c.count} ({c.percentage.toFixed(1)}%)
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: 12, border: '1px solid #e5e7eb', borderRadius: 10 }}>
          <h3 style={{ margin: '0 0 8px 0' }}>Yearly trend</h3>
          {!yearly ? (
            <div style={{ color: '#6b7280' }}>Loading…</div>
          ) : yearly.year_over_year.length === 0 ? (
            <div style={{ color: '#6b7280' }}>No data yet. Run an analysis.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {yearly.year_over_year.map((y) => (
                <div key={y.year} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <div style={{ fontSize: 13, color: '#374151' }}>{y.year}</div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>{y.total_emails}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Analyze({
  accountId,
  accountConnected,
  startDate,
  endDate,
  setStartDate,
  setEndDate,
  forceReanalysis,
  setForceReanalysis,
  inboxOnly,
  setInboxOnly,
  runs,
  setRuns,
  hasMoreRuns,
  loadingMoreRuns,
  loadMoreRuns,
  processedRanges,
  gaps,
  busy,
  setBusy,
  error,
  setError,
}: {
  accountId: number | null
  accountConnected: boolean
  startDate: string
  endDate: string
  setStartDate: (v: string) => void
  setEndDate: (v: string) => void
  forceReanalysis: boolean
  setForceReanalysis: (v: boolean) => void
  inboxOnly: boolean
  setInboxOnly: (v: boolean) => void
  runs: AnalysisRun[]
  setRuns: (v: AnalysisRun[]) => void
  hasMoreRuns: boolean
  loadingMoreRuns: boolean
  loadMoreRuns: () => Promise<void>
  processedRanges: ProcessedRange[]
  gaps: ProcessedRangeGap[]
  busy: boolean
  setBusy: (v: boolean) => void
  error: string | null
  setError: (v: string | null) => void
}) {
  const running = runs.find((r) => r.status === 'pending' || r.status === 'processing') ?? null
  const latest = runs[0] ?? null

  const rawPct =
    running && running.total_emails > 0 ? (running.emails_processed / running.total_emails) * 100 : 0
  const progressPct = Math.min(100, Math.max(0, Math.round(rawPct)))

  return (
    <div style={{ marginTop: 12 }}>
      {error ? <div style={{ color: '#b91c1c', marginBottom: 8 }}>{error}</div> : null}

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <label style={{ fontSize: 13, color: '#374151' }}>Start (on and after)</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <label style={{ fontSize: 13, color: '#374151' }}>End (before, exclusive)</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
          <input
            type="checkbox"
            checked={forceReanalysis}
            disabled={busy || !!running}
            onChange={(e) => setForceReanalysis(e.target.checked)}
          />
          Force re-analysis
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
          <input
            type="checkbox"
            checked={inboxOnly}
            disabled={busy || !!running}
            onChange={(e) => setInboxOnly(e.target.checked)}
          />
          Inbox only (Gmail)
        </label>
        <button
          disabled={busy || !accountId || !accountConnected || !!running}
          onClick={async () => {
            if (!accountId) return
            setBusy(true)
            setError(null)
            try {
              const res = await api.startAnalysis({
                account_id: accountId,
                start_date: startDate,
                end_date_exclusive: endDate,
                force_reanalysis: forceReanalysis,
                inbox_only: inboxOnly,
              })
              const data = await api.getRun(res.run_id)
              setRuns([data, ...runs])
            } catch (e: any) {
              setError(e?.message ?? 'Failed to start analysis')
            } finally {
              setBusy(false)
            }
          }}
        >
          Start analysis
        </button>
        <button
          disabled={busy || !running}
          onClick={async () => {
            if (!running) return
            setBusy(true)
            setError(null)
            try {
              await api.stopRun(running.id)
            } catch (e: any) {
              setError(e?.message ?? 'Failed to stop')
            } finally {
              setBusy(false)
            }
          }}
        >
          Stop
        </button>
      </div>

      {running ? (
        <div style={{ marginTop: 12, padding: 12, border: '1px solid #e5e7eb', borderRadius: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ fontWeight: 600 }}>Running</div>
            <div style={{ color: '#6b7280', fontSize: 13 }}>
              {running.emails_processed}/{running.total_emails || '?'} • {progressPct}%
            </div>
          </div>
          <div style={{ marginTop: 8, height: 10, background: '#e5e7eb', borderRadius: 999 }}>
            <div
              style={{
                width: `${progressPct}%`,
                height: 10,
                borderRadius: 999,
                background: '#111827',
                transition: 'width 120ms linear',
              }}
            />
          </div>
        </div>
      ) : null}

      <div style={{ marginTop: 16 }}>
        <h3 style={{ margin: '0 0 0.5rem 0' }}>Recent runs</h3>
        {runs.length === 0 ? (
          <div style={{ color: '#6b7280' }}>No runs yet.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {(runs ?? []).map((r) => (
              <div key={r.id} style={{ padding: 10, border: '1px solid #e5e7eb', borderRadius: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 600 }}>#{r.id}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                    <div
                      style={{
                        fontSize: 12,
                        padding: '2px 8px',
                        borderRadius: 999,
                        border: '1px solid #e5e7eb',
                        background:
                          r.status === 'completed'
                            ? '#ecfdf5'
                            : r.status === 'failed'
                              ? '#fef2f2'
                              : r.status === 'cancelled'
                                ? '#fffbeb'
                                : '#eff6ff',
                        color:
                          r.status === 'completed'
                            ? '#065f46'
                            : r.status === 'failed'
                              ? '#b91c1c'
                              : r.status === 'cancelled'
                                ? '#92400e'
                                : '#1d4ed8',
                      }}
                    >
                      {r.status}
                    </div>
                    {(r.status === 'failed' || r.status === 'cancelled') ? (
                      <button
                        disabled={busy || !!running}
                        onClick={async () => {
                          setBusy(true)
                          setError(null)
                          try {
                            const res = await api.retryRun(r.id)
                            const data = await api.getRun(res.run_id)
                            setRuns([data, ...runs])
                          } catch (e: any) {
                            setError(e?.message ?? 'Failed to retry')
                          } finally {
                            setBusy(false)
                          }
                        }}
                      >
                        Retry
                      </button>
                    ) : null}
                  </div>
                </div>
                <div style={{ marginTop: 6, fontSize: 13, color: '#374151' }}>
                  {r.start_date} → {r.end_date_exclusive} (end exclusive)
                </div>
                {r.error_message ? <div style={{ marginTop: 6, fontSize: 13, color: '#b91c1c' }}>{r.error_message}</div> : null}
              </div>
            ))}
          </div>
        )}
        {hasMoreRuns ? (
          <div style={{ marginTop: 10 }}>
            <button disabled={loadingMoreRuns} onClick={() => void loadMoreRuns()}>
              {loadingMoreRuns ? 'Loading…' : 'Load more'}
            </button>
          </div>
        ) : null}
        {latest && latest.status === 'failed' ? (
          <div style={{ marginTop: 8, color: '#6b7280', fontSize: 13 }}>Next: add retry endpoint.</div>
        ) : null}
      </div>

      <div style={{ marginTop: 16 }}>
        <h3 style={{ margin: '0 0 0.25rem 0' }}>Processed ranges</h3>
        <p style={{ margin: '0 0 0.5rem 0', fontSize: 12, color: '#6b7280', lineHeight: 1.4 }}>
          Each row is one analysis you ran (the dates you picked), not each internal fetch chunk. Older data without
          run linkage may appear as merged bands.
        </p>
        {processedRanges.length === 0 ? (
          <div style={{ color: '#6b7280' }}>No processed ranges yet.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {processedRanges.map((pr, idx) => (
              <div
                key={pr.analysis_run_id != null ? `run-${pr.analysis_run_id}` : `legacy-${pr.start_date}-${pr.end_date_exclusive}-${idx}`}
                style={{ padding: 10, border: '1px solid #e5e7eb', borderRadius: 10 }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 600 }}>
                    {pr.start_date} → {pr.end_date_exclusive} (end exclusive)
                  </div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>{pr.emails_count} emails</div>
                </div>
                <div style={{ marginTop: 6, fontSize: 13, color: '#6b7280' }}>
                  processed_at: {pr.processed_at}
                  {pr.analysis_run_id != null ? (
                    <span style={{ marginLeft: 8 }}>(run #{pr.analysis_run_id})</span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ marginTop: 16 }}>
        <h3 style={{ margin: '0 0 0.5rem 0' }}>Unprocessed gaps (last 365 days)</h3>
        {gaps.length === 0 ? (
          <div style={{ color: '#6b7280' }}>No gaps detected in the last 365 days.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {gaps.map((g, idx) => (
              <button
                key={`${g.start_date}-${g.end_date_exclusive}-${idx}`}
                onClick={() => {
                  setStartDate(g.start_date)
                  setEndDate(g.end_date_exclusive)
                }}
                style={{
                  textAlign: 'left',
                  padding: 10,
                  border: '1px solid #e5e7eb',
                  borderRadius: 10,
                  background: 'white',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 600 }}>
                    {g.start_date} → {g.end_date_exclusive} (end exclusive)
                  </div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>{g.days} days</div>
                </div>
                <div style={{ marginTop: 6, fontSize: 13, color: '#6b7280' }}>
                  Click to set Start/End for analysis
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Settings({
  username,
  accounts,
  selectedAccountId,
  banner,
  clearBanner,
  onAccountsChange,
}: {
  username: string
  accounts: EmailAccount[]
  selectedAccountId: number | null
  banner: string | null
  clearBanner: () => void
  onAccountsChange: (accounts: EmailAccount[]) => void
}) {
  const [provider, setProvider] = useState<'gmail' | 'yahoo'>('gmail')
  const [email, setEmail] = useState('')
  const [yahooAppPassword, setYahooAppPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const providerChosenManually = useRef(false)

  useEffect(() => {
    if (providerChosenManually.current) return
    const s = suggestedProviderFromEmail(email)
    if (s) setProvider(s)
  }, [email])

  const refresh = async () => {
    const data = await api.listAccounts(username)
    onAccountsChange(data)
  }

  useEffect(() => {
    void refresh()
  }, [])

  return (
    <div style={{ marginTop: 12 }}>
      <h3 style={{ margin: '0 0 0.5rem 0' }}>Account Management</h3>
      {banner ? (
        <div
          style={{
            marginBottom: 8,
            padding: 10,
            border: '1px solid #e5e7eb',
            borderRadius: 10,
            background: '#f9fafb',
            display: 'flex',
            justifyContent: 'space-between',
            gap: 12,
            flexWrap: 'wrap',
          }}
        >
          <div style={{ fontSize: 13, color: '#374151' }}>{banner}</div>
          <button onClick={clearBanner}>Dismiss</button>
        </div>
      ) : null}
      {error ? <div style={{ color: '#b91c1c', marginBottom: 8 }}>{error}</div> : null}
      <p style={{ margin: '0 0 0.5rem 0', fontSize: 13, color: '#4b5563' }}>
        Provider is how Mail Mind connects (Gmail OAuth vs Yahoo app password), not a guess from the address alone. For
        @yahoo.com / @ymail.com we preselect Yahoo until you change it.
      </p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <select
          value={provider}
          onChange={(e) => {
            providerChosenManually.current = true
            setProvider(e.target.value as 'gmail' | 'yahoo')
          }}
        >
          <option value="gmail">Gmail</option>
          <option value="yahoo">Yahoo</option>
        </select>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          style={{ flex: 1, minWidth: 240, padding: '0.5rem 0.75rem' }}
        />
        <button
          disabled={busy || email.trim().length === 0}
          onClick={async () => {
            setBusy(true)
            setError(null)
            try {
              await api.createAccount({ username, provider, email })
              setEmail('')
              providerChosenManually.current = false
              await refresh()
            } catch (e: any) {
              setError(e?.message ?? 'Failed')
            } finally {
              setBusy(false)
            }
          }}
        >
          Add account
        </button>
      </div>

      <div style={{ marginTop: 14 }}>
        <h4 style={{ margin: '0 0 0.5rem 0' }}>Your accounts</h4>
        {accounts.length === 0 ? (
          <div style={{ color: '#6b7280' }}>No accounts yet.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {accounts.map((a) => (
              <div
                key={a.id}
                style={{
                  padding: 10,
                  border: '1px solid #e5e7eb',
                  borderRadius: 10,
                  background: a.id === selectedAccountId ? '#f9fafb' : 'white',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 600 }}>
                    {providerLabel(a.provider)} • {a.email}
                  </div>
                  <div style={{ fontSize: 13, color: a.is_connected ? '#065f46' : '#92400e' }}>
                    {a.is_connected ? 'connected' : 'not connected'}
                  </div>
                </div>
                <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {a.provider === 'gmail' ? (
                    <button
                      disabled={busy}
                      onClick={async () => {
                        setBusy(true)
                        setError(null)
                        try {
                          const { auth_url } = await api.startGmailOAuth(a.id)
                          window.location.href = auth_url
                        } catch (e: any) {
                          setError(e?.message ?? 'Failed to start Gmail OAuth')
                        } finally {
                          setBusy(false)
                        }
                      }}
                    >
                      {a.is_active ? 'Reconnect Gmail' : 'Connect Gmail'}
                    </button>
                  ) : null}
                  {a.provider === 'yahoo' ? (
                    <>
                      <p
                        style={{
                          margin: '0 0 6px 0',
                          maxWidth: 560,
                          fontSize: 12,
                          color: '#374151',
                          lineHeight: 1.45,
                        }}
                      >
                        <strong>Not your usual Yahoo login password.</strong> In Yahoo (Account security), create a
                        one-time <strong>app password</strong> for “Mail” or another label—Yahoo shows a long code.
                        Paste that code here; Mail Mind stores it encrypted and uses it for IMAP only.
                      </p>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                      <input
                        type="password"
                        value={yahooAppPassword}
                        onChange={(e) => setYahooAppPassword(e.target.value)}
                        placeholder="Paste app password from Yahoo (spaces OK)"
                        style={{ minWidth: 240, padding: '0.5rem 0.75rem' }}
                      />
                      <button
                        disabled={busy || yahooAppPassword.replace(/\s+/g, '').length < 8}
                        onClick={async () => {
                          setBusy(true)
                          setError(null)
                          try {
                            const pw = yahooAppPassword.replace(/\s+/g, '')
                            await api.connectYahooAppPassword(a.id, pw)
                            setYahooAppPassword('')
                            await refresh()
                          } catch (e: any) {
                            setError(e?.message ?? 'Failed to save Yahoo app password')
                          } finally {
                            setBusy(false)
                          }
                        }}
                      >
                        {a.is_active ? 'Update app password' : 'Connect Yahoo'}
                      </button>
                      </div>
                    </>
                  ) : null}
                  {a.is_active ? (
                    <button
                      disabled={busy}
                      onClick={async () => {
                        setBusy(true)
                        setError(null)
                        try {
                          await api.deactivateAccount(a.id)
                          await refresh()
                        } catch (e: any) {
                          setError(e?.message ?? 'Failed')
                        } finally {
                          setBusy(false)
                        }
                      }}
                    >
                      Deactivate
                    </button>
                  ) : null}
                  {a.is_connected ? (
                    <button
                      disabled={busy}
                      onClick={async () => {
                        if (!window.confirm('Disconnect this account? This removes stored credentials and deactivates the account.')) return
                        setBusy(true)
                        setError(null)
                        try {
                          if (a.provider === 'gmail') await api.disconnectGmailAccount(a.id)
                          else await api.disconnectAccount(a.id)
                          await refresh()
                        } catch (e: any) {
                          setError(e?.message ?? 'Failed to disconnect')
                        } finally {
                          setBusy(false)
                        }
                      }}
                    >
                      Disconnect
                    </button>
                  ) : null}
                  <button
                    disabled={busy}
                    onClick={async () => {
                      if (!window.confirm('Reset local analysis data for this account? This deletes runs/messages/ranges but keeps credentials.')) return
                      setBusy(true)
                      setError(null)
                      try {
                        await api.resetAccountData(a.id)
                        await refresh()
                      } catch (e: any) {
                        setError(e?.message ?? 'Failed to reset local data')
                      } finally {
                        setBusy(false)
                      }
                    }}
                  >
                    Reset local data
                  </button>
                  <button
                    disabled={busy}
                    onClick={async () => {
                      if (!window.confirm('Delete this account? This deletes the account, credentials, and all local data.')) return
                      setBusy(true)
                      setError(null)
                      try {
                        await api.deleteAccount(a.id)
                        await refresh()
                      } catch (e: any) {
                        setError(e?.message ?? 'Failed')
                      } finally {
                        setBusy(false)
                      }
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

