import { useEffect, useMemo, useState } from 'react'
import {
  api,
  type AnalysisRun,
  type CategoryInsights,
  type EmailAccount,
  type InsightsSummary,
  type ProcessedRange,
  type ProcessedRangeGap,
  type SenderInsights,
  type YearlyFrequencyInsights,
} from '../api/client'

type Tab = 'analysis' | 'insights' | 'settings'

const TAB_LABELS: Record<Tab, string> = {
  analysis: 'Analyze',
  insights: 'Insights',
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

function subDays(dateStr: string, days: number) {
  return addDays(dateStr, -days)
}

export default function App() {
  const [username, setUsername] = useState('')
  const [loggedIn, setLoggedIn] = useState(false)
  const [tab, setTab] = useState<Tab>('analysis')

  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null)

  const canUseAccount = useMemo(() => loggedIn && accounts.length > 0, [loggedIn, accounts.length])
  const selectedAccount = useMemo(
    () => (selectedAccountId ? accounts.find((a) => a.id === selectedAccountId) ?? null : null),
    [accounts, selectedAccountId],
  )

  const [startDate, setStartDate] = useState(yyyyMmDd(new Date(Date.now() - 1000 * 60 * 60 * 24 * 7)))
  const [endDate, setEndDate] = useState(yyyyMmDd(new Date()))
  const [runs, setRuns] = useState<AnalysisRun[]>([])
  const [runsOffset, setRunsOffset] = useState(0)
  const [hasMoreRuns, setHasMoreRuns] = useState(false)
  const [loadingMoreRuns, setLoadingMoreRuns] = useState(false)
  const [processedRanges, setProcessedRanges] = useState<ProcessedRange[]>([])
  const [gaps, setGaps] = useState<ProcessedRangeGap[]>([])
  const [runError, setRunError] = useState<string | null>(null)
  const [runBusy, setRunBusy] = useState(false)
  const [forceReanalysis, setForceReanalysis] = useState(false)

  const [summary, setSummary] = useState<InsightsSummary | null>(null)
  const [senderInsights, setSenderInsights] = useState<SenderInsights | null>(null)
  const [categoryInsights, setCategoryInsights] = useState<CategoryInsights | null>(null)
  const [yearlyInsights, setYearlyInsights] = useState<YearlyFrequencyInsights | null>(null)
  const [insightsError, setInsightsError] = useState<string | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem('mailmind_username') ?? ''
    if (saved.trim().length > 0) {
      setUsername(saved)
      setLoggedIn(true)
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
            {(['analysis', 'insights', 'settings'] as const).map((t) => (
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
                      {a.provider} • {a.email}{a.is_active ? '' : ' (inactive)'}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {selectedAccount && !selectedAccount.is_active ? (
              <div style={{ marginTop: 10, padding: 10, border: '1px solid #f59e0b', borderRadius: 10, background: '#fffbeb' }}>
                <div style={{ fontSize: 13, color: '#92400e' }}>
                  <strong>Account inactive.</strong> Reconnect it in Settings before running analysis.
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
                onAccountsChange={(a) => {
                  setAccounts(a)
                  if (a.length === 0) setSelectedAccountId(null)
                  if (selectedAccountId && !a.some((x) => x.id === selectedAccountId)) setSelectedAccountId(null)
                }}
              />
            ) : tab === 'analysis' ? (
              <Analyze
                accountId={selectedAccountId}
                startDate={startDate}
                endDate={endDate}
                setStartDate={setStartDate}
                setEndDate={setEndDate}
                forceReanalysis={forceReanalysis}
                setForceReanalysis={setForceReanalysis}
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
          {!senders ? (
            <div style={{ color: '#6b7280' }}>Loading…</div>
          ) : senders.total_emails === 0 ? (
            <div style={{ color: '#6b7280' }}>No data yet. Run an analysis.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {senders.top_senders.map((s) => (
                <div key={s.email} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <div style={{ fontSize: 13, color: '#374151' }}>{s.email}</div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>{s.count}</div>
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
  startDate,
  endDate,
  setStartDate,
  setEndDate,
  forceReanalysis,
  setForceReanalysis,
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
  startDate: string
  endDate: string
  setStartDate: (v: string) => void
  setEndDate: (v: string) => void
  forceReanalysis: boolean
  setForceReanalysis: (v: boolean) => void
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

  const progressPct =
    running && running.total_emails > 0 ? Math.round((running.emails_processed / running.total_emails) * 100) : 0

  return (
    <div style={{ marginTop: 12 }}>
      {error ? <div style={{ color: '#b91c1c', marginBottom: 8 }}>{error}</div> : null}

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <label style={{ fontSize: 13, color: '#374151' }}>Start</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <label style={{ fontSize: 13, color: '#374151' }}>End (inclusive)</label>
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
        <button
          disabled={busy || !accountId || !!running}
          onClick={async () => {
            if (!accountId) return
            setBusy(true)
            setError(null)
            try {
              const endExclusive = addDays(endDate, 1)
              const res = await api.startAnalysis({
                account_id: accountId,
                start_date: startDate,
                end_date_exclusive: endExclusive,
                force_reanalysis: forceReanalysis,
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
                    <div style={{ fontSize: 13, color: '#6b7280' }}>{r.status}</div>
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
        <h3 style={{ margin: '0 0 0.5rem 0' }}>Processed ranges</h3>
        {processedRanges.length === 0 ? (
          <div style={{ color: '#6b7280' }}>No processed ranges yet.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {processedRanges.map((pr, idx) => (
              <div key={`${pr.start_date}-${pr.end_date_exclusive}-${idx}`} style={{ padding: 10, border: '1px solid #e5e7eb', borderRadius: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ fontWeight: 600 }}>
                    {pr.start_date} → {pr.end_date_exclusive} (end exclusive)
                  </div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>{pr.emails_count} emails</div>
                </div>
                <div style={{ marginTop: 6, fontSize: 13, color: '#6b7280' }}>
                  processed_at: {pr.processed_at}
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
                  setEndDate(subDays(g.end_date_exclusive, 1))
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
  onAccountsChange,
}: {
  username: string
  accounts: EmailAccount[]
  selectedAccountId: number | null
  onAccountsChange: (accounts: EmailAccount[]) => void
}) {
  const [provider, setProvider] = useState<'gmail' | 'yahoo'>('gmail')
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
      {error ? <div style={{ color: '#b91c1c', marginBottom: 8 }}>{error}</div> : null}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <select value={provider} onChange={(e) => setProvider(e.target.value as any)}>
          <option value="gmail">gmail</option>
          <option value="yahoo">yahoo</option>
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
        <h4 style={{ margin: '0 0 0.5rem 0' }}>Existing accounts</h4>
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
                    {a.provider} • {a.email}
                  </div>
                  <div style={{ fontSize: 13, color: a.is_active ? '#065f46' : '#92400e' }}>
                    {a.is_active ? 'active' : 'inactive'}
                  </div>
                </div>
                <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
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
                  ) : (
                    <button
                      disabled={busy}
                      onClick={async () => {
                        setBusy(true)
                        setError(null)
                        try {
                          await api.reconnectAccount(a.id)
                          await refresh()
                        } catch (e: any) {
                          setError(e?.message ?? 'Failed')
                        } finally {
                          setBusy(false)
                        }
                      }}
                    >
                      Reconnect
                    </button>
                  )}
                  <button
                    disabled={busy}
                    onClick={async () => {
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

