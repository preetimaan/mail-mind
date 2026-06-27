import { useEffect, useMemo, useRef, useState } from 'react'
import {
  api,
  type AIStatus,
  type AnalysisRun,
  type CategoryInsights,
  type ClassifiedSender,
  type EmailAccount,
  type FilterQuery,
  type GmailFilterRule,
  type GmailLabel,
  type InsightsSummary,
  type LabelSummary,
  type ProcessedRange,
  type ProcessedRangeGap,
  type SenderInsights,
  type SenderMessageSample,
  type UnclassifiedSender,
  type YearlyFrequencyInsights,
} from '../api/client'

type Tab = 'analysis' | 'insights' | 'labels' | 'filters' | 'settings'

const TAB_LABELS: Record<Tab, string> = {
  analysis: 'Analyze',
  insights: 'Insights',
  labels: 'Label Suggestions',
  filters: 'Gmail Labels',
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

  const [labelSummary, setLabelSummary] = useState<LabelSummary | null>(null)
  const [labelError, setLabelError] = useState<string | null>(null)
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null)
  const [filterQueries, setFilterQueries] = useState<FilterQuery[] | null>(null)

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
    if (selectedAccountId !== null) {
      localStorage.setItem('mailmind_account_id', String(selectedAccountId))
    }
  }, [selectedAccountId])

  useEffect(() => {
    if (!loggedIn) return
    void (async () => {
      const data = await api.listAccounts(username)
      setAccounts(data)
      if (data.length > 0 && selectedAccountId === null) {
        const saved = localStorage.getItem('mailmind_account_id')
        const savedId = saved ? Number(saved) : null
        const preferred = savedId && data.some((a) => a.id === savedId) ? savedId : data[0].id
        setSelectedAccountId(preferred)
      }
    })()
  }, [loggedIn, username])

  useEffect(() => {
    if (tab === 'filters' && selectedAccount?.provider !== 'gmail') setTab('analysis')
  }, [selectedAccount])

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
    setGmailFiltersError(null)
    void (async () => {
      try {
        const [data, fq] = await Promise.all([
          api.getLabelsFilters(selectedAccountId),
          api.getFilterQueries(selectedAccountId),
        ])
        setGmailLabels(data.labels)
        setGmailFilters(data.filters)
        setGmailFiltersError(data.filters_error)
        setFilterQueries(fq.queries)
      } catch (e: any) {
        setGmailLabels(null)
        setGmailFilters(null)
        setGmailFiltersError(e?.message ?? 'Failed to load Gmail labels')
      }
    })()
  }, [loggedIn, selectedAccountId, tab, selectedAccount?.provider])

  useEffect(() => {
    if (!loggedIn || !selectedAccountId || tab !== 'labels') return
    setLabelError(null)
    void (async () => {
      try {
        const calls: Promise<any>[] = [
          api.getLabelSummary(selectedAccountId),
          api.getAIStatus(),
          api.getFilterQueries(selectedAccountId),
        ]
        if (selectedAccount?.provider === 'gmail') {
          calls.push(api.getLabelsFilters(selectedAccountId))
        }
        const [summary, aiStat, fq, labelsData] = await Promise.all(calls)
        setLabelSummary(summary)
        setAiStatus(aiStat)
        setFilterQueries(fq.queries)
        if (labelsData) setGmailLabels(labelsData.labels)
      } catch (e: any) {
        setLabelError(e?.message ?? 'Failed to load label suggestions')
        setLabelSummary(null)
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
          <nav style={{ display: 'flex', gap: 8, marginTop: '1.25rem', flexWrap: 'wrap' }}>
            {(['analysis', 'insights', 'labels', 'filters', 'settings'] as const).filter((t) => t !== 'filters' || selectedAccount?.provider === 'gmail').map((t) => (
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
            ) : tab === 'labels' ? (
              <LabelSuggestions
                accountId={selectedAccountId}
                summary={labelSummary}
                error={labelError}
                aiStatus={aiStatus}
                filterQueries={filterQueries}
                gmailLabels={selectedAccount?.provider === 'gmail' ? (gmailLabels ?? []) : []}
                onRefresh={async () => {
                  if (!selectedAccountId) return
                  setLabelError(null)
                  try {
                    const [s, fq] = await Promise.all([
                      api.getLabelSummary(selectedAccountId),
                      api.getFilterQueries(selectedAccountId),
                    ])
                    setLabelSummary(s)
                    setFilterQueries(fq.queries)
                  } catch (e: any) {
                    setLabelError(e?.message ?? 'Failed to refresh')
                  }
                }}
              />
            ) : tab === 'filters' ? (
              <GmailLabels
                account={selectedAccount}
                labels={gmailLabels}
                filters={gmailFilters}
                filtersError={gmailFiltersError}
                filterQueries={filterQueries}
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

const CUSTOM_LABELS = ['Career', 'Job Search', 'Study', 'Software Learning', 'Life Admin', 'Shopping', 'Services', 'Money', 'Health', 'Gov & Tax', 'Personal']
const LABEL_COLORS: Record<string, string> = {
  Career: '#dbeafe',
  'Job Search': '#bfdbfe',
  Study: '#ede9fe',
  'Software Learning': '#ccfbf1',
  'Life Admin': '#d1fae5',
  Shopping: '#fde68a',
  Services: '#fed7aa',
  Money: '#fef9c3',
  Health: '#fee2e2',
  'Gov & Tax': '#e0e7ff',
  Personal: '#fce7f3',
}

function LabelBadge({ label }: { label: string }) {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: 12,
        fontSize: 11,
        fontWeight: 600,
        background: LABEL_COLORS[label] ?? '#f3f4f6',
        color: '#111827',
        marginRight: 4,
      }}
    >
      {label}
    </span>
  )
}

function LabelBadgeWithSource({ label, source }: { label: string; source?: string }) {
  const isManual = source === 'manual'
  return (
    <span
      title={source ?? undefined}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 3,
        padding: '2px 8px',
        borderRadius: 12,
        fontSize: 11,
        fontWeight: 600,
        background: LABEL_COLORS[label] ?? '#f3f4f6',
        color: '#111827',
        marginRight: 4,
      }}
    >
      {isManual && <span style={{ fontSize: 10, opacity: 0.7 }}>✎</span>}
      {label}
    </span>
  )
}

const SOURCE_META: Record<string, { label: string; bg: string; color: string }> = {
  manual:        { label: '✎ manual',  bg: '#dcfce7', color: '#166534' },
  tier1_domain:  { label: 'domain',   bg: '#dbeafe', color: '#1d4ed8' },
  tier2_keyword: { label: 'keyword',  bg: '#cffafe', color: '#0e7490' },
  ai:            { label: 'AI',       bg: '#ede9fe', color: '#6d28d9' },
}

function SourceBadge({ source }: { source: string | null }) {
  if (!source) return <span style={{ fontSize: 11, color: '#9ca3af' }}>—</span>
  const meta = SOURCE_META[source]
  if (!meta) return <span style={{ fontSize: 11, color: '#9ca3af' }}>{source}</span>
  return (
    <span style={{
      display: 'inline-block',
      padding: '1px 7px',
      borderRadius: 10,
      fontSize: 11,
      fontWeight: source === 'manual' ? 700 : 500,
      background: meta.bg,
      color: meta.color,
    }}>
      {meta.label}
    </span>
  )
}

function LabelSuggestions({
  accountId,
  summary,
  error,
  aiStatus,
  filterQueries,
  gmailLabels,
  onRefresh,
}: {
  accountId: number | null
  summary: LabelSummary | null
  error: string | null
  aiStatus: AIStatus | null
  filterQueries: FilterQuery[] | null
  gmailLabels: GmailLabel[]
  onRefresh: () => Promise<void>
}) {
  const [running, setRunning] = useState(false)
  const [runResult, setRunResult] = useState<string | null>(null)
  const [expandedLabel, setExpandedLabel] = useState<string | null>(null)
  const [labelSenders, setLabelSenders] = useState<ClassifiedSender[]>([])
  const [loadingLabel, setLoadingLabel] = useState(false)
  const [unclassified, setUnclassified] = useState<UnclassifiedSender[] | null>(null)
  const [loadingUnclassified, setLoadingUnclassified] = useState(false)
  const [assigning, setAssigning] = useState<string | null>(null)
  const [aiRunning, setAiRunning] = useState(false)
  const [aiResult, setAiResult] = useState<string | null>(null)
  const [editingSender, setEditingSender] = useState<string | null>(null)
  const [editingLabels, setEditingLabels] = useState<string[]>([])
  const [subjectsModal, setSubjectsModal] = useState<{ name: string; subjects: string[] } | null>(null)
  const [gmailLabelDropdown, setGmailLabelDropdown] = useState<string | null>(null)

  const userGmailLabels = gmailLabels.filter((l) => l.type === 'user')

  async function handleRunClassification() {
    if (!accountId) return
    setRunning(true)
    setRunResult(null)
    try {
      const res = await api.runLabelClassification(accountId)
      setRunResult(`Classified ${res.classified} of ${res.total_senders} senders (${res.unclassified} need review).`)
      await onRefresh()
    } catch (e: any) {
      setRunResult(`Error: ${e?.message ?? 'Failed'}`)
    } finally {
      setRunning(false)
    }
  }

  async function handleExpandLabel(label: string) {
    if (expandedLabel === label) {
      setExpandedLabel(null)
      return
    }
    if (!accountId) return
    setExpandedLabel(label)
    setLoadingLabel(true)
    try {
      const res = await api.getSendersForLabel(accountId, label)
      setLabelSenders(res.senders)
    } catch {
      setLabelSenders([])
    } finally {
      setLoadingLabel(false)
    }
  }

  async function handleLoadUnclassified() {
    if (!accountId) return
    setLoadingUnclassified(true)
    try {
      const res = await api.getUnclassifiedSenders(accountId)
      setUnclassified(res.senders)
    } catch {
      setUnclassified([])
    } finally {
      setLoadingUnclassified(false)
    }
  }

  async function handleManualAssign(senderEmail: string, labels: string[]) {
    if (!accountId) return
    setAssigning(senderEmail)
    try {
      await api.manualClassifySender(accountId, senderEmail, labels)
      setUnclassified((prev) => (prev ? prev.filter((s) => s.sender_email !== senderEmail) : prev))
      await onRefresh()
    } catch (e: any) {
      alert(`Failed to assign: ${e?.message ?? 'Unknown error'}`)
    } finally {
      setAssigning(null)
    }
  }

  async function handleGmailLabelSave(senderEmail: string, gmailLabelName: string, currentLabels: string[]) {
    if (!accountId) return
    const next = currentLabels.includes(gmailLabelName)
      ? currentLabels.filter((l) => l !== gmailLabelName)
      : [...currentLabels, gmailLabelName]
    try {
      await api.setGmailLabelsForSender(accountId, senderEmail, next)
      if (expandedLabel) {
        const res = await api.getSendersForLabel(accountId, expandedLabel)
        setLabelSenders(res.senders)
      }
    } catch (e: any) {
      alert(`Failed: ${e?.message}`)
    }
  }

  async function handleEditSave(senderEmail: string, labels: string[]) {
    if (!accountId) return
    try {
      await api.manualClassifySender(accountId, senderEmail, labels)
      setEditingSender(null)
      if (expandedLabel) {
        const res = await api.getSendersForLabel(accountId, expandedLabel)
        setLabelSenders(res.senders)
      }
      await onRefresh()
    } catch (e: any) {
      alert(`Failed to update: ${e?.message ?? 'Unknown error'}`)
    }
  }

  async function handleAIEnhance() {
    if (!accountId) return
    setAiRunning(true)
    setAiResult(null)
    try {
      const res = await api.runAIEnhance(accountId)
      setAiResult(`AI classified ${res.processed} senders via ${res.provider}${res.errors ? ` (${res.errors} errors)` : ''}.`)
      await onRefresh()
      if (unclassified !== null) {
        const fresh = await api.getUnclassifiedSenders(accountId)
        setUnclassified(fresh.senders)
      }
    } catch (e: any) {
      setAiResult(`Error: ${e?.message ?? 'Failed'}`)
    } finally {
      setAiRunning(false)
    }
  }

  if (!accountId) {
    return <div style={{ marginTop: 12, color: '#6b7280' }}>Select an account to view label suggestions.</div>
  }

  return (
    <div style={{ marginTop: 12 }}>
      {subjectsModal && (
        <SubjectsModal
          senderName={subjectsModal.name}
          subjects={subjectsModal.subjects}
          onClose={() => setSubjectsModal(null)}
        />
      )}
      {/* Run + AI controls */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <button onClick={handleRunClassification} disabled={running}>
          {running ? 'Running…' : 'Run Classification'}
        </button>
        {aiStatus?.configured ? (
          <button onClick={handleAIEnhance} disabled={aiRunning}>
            {aiRunning ? 'Enhancing…' : `Enhance with AI (${aiStatus.provider})`}
          </button>
        ) : (
          <span style={{ fontSize: 12, color: '#9ca3af' }}>
            AI not configured — set MAILMIND_AI_PROVIDER + MAILMIND_AI_API_KEY in .env
          </span>
        )}
      </div>
      {runResult && <div style={{ marginTop: 8, fontSize: 13, color: '#374151' }}>{runResult}</div>}
      {aiResult && <div style={{ marginTop: 8, fontSize: 13, color: '#374151' }}>{aiResult}</div>}
      {error && <div style={{ marginTop: 8, fontSize: 13, color: '#dc2626' }}>{error}</div>}

      {/* Coverage summary */}
      {summary && (
        <>
          <div
            style={{
              marginTop: 16,
              padding: 12,
              background: '#f9fafb',
              border: '1px solid #e5e7eb',
              borderRadius: 10,
              display: 'flex',
              gap: 24,
              flexWrap: 'wrap',
              alignItems: 'center',
            }}
          >
            <div>
              <span style={{ fontWeight: 700, fontSize: 22 }}>{summary.coverage_percent}%</span>
              <span style={{ fontSize: 13, color: '#6b7280', marginLeft: 6 }}>of emails from labelled senders</span>
            </div>
            <div style={{ fontSize: 13, color: '#374151' }}>
              <strong>{summary.total_emails.toLocaleString()}</strong> total emails
            </div>
            <div style={{ fontSize: 13, color: '#374151' }}>
              <strong>{summary.classified_senders.toLocaleString()}</strong> senders classified
            </div>
            <div style={{ fontSize: 13, color: '#374151' }}>
              <strong>{summary.unclassified.sender_count.toLocaleString()}</strong> senders unclassified
            </div>
          </div>

          {/* Per-label cards */}
          <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {summary.labels.map((stat) => (
              <div key={stat.label} style={{ border: '1px solid #e5e7eb', borderRadius: 10, overflow: 'hidden' }}>
                <button
                  onClick={() => handleExpandLabel(stat.label)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '10px 14px',
                    background: expandedLabel === stat.label ? '#f3f4f6' : 'white',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <LabelBadge label={stat.label} />
                  <span style={{ fontSize: 13, color: '#374151' }}>
                    <strong>{stat.email_count.toLocaleString()}</strong> emails &middot;{' '}
                    <strong>{stat.sender_count}</strong> senders
                  </span>
                  <span style={{ marginLeft: 'auto', fontSize: 12, color: '#9ca3af' }}>
                    {expandedLabel === stat.label ? '▲' : '▼'}
                  </span>
                </button>

                {expandedLabel === stat.label && (
                  <div style={{ padding: '0 14px 12px', borderTop: '1px solid #f3f4f6' }}>
                    {loadingLabel ? (
                      <div style={{ fontSize: 13, color: '#9ca3af', marginTop: 8 }}>Loading…</div>
                    ) : labelSenders.length === 0 ? (
                      <div style={{ fontSize: 13, color: '#9ca3af', marginTop: 8 }}>
                        No senders found. Run classification first.
                      </div>
                    ) : (
                      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8, fontSize: 13 }}>
                        <thead>
                          <tr style={{ color: '#6b7280', textAlign: 'left' }}>
                            <th style={{ paddingBottom: 4, fontWeight: 500 }}>Sender</th>
                            <th style={{ paddingBottom: 4, fontWeight: 500 }}>Emails</th>
                            <th style={{ paddingBottom: 4, fontWeight: 500 }}>Labels</th>
                            <th style={{ paddingBottom: 4, fontWeight: 500 }}></th>
                          </tr>
                        </thead>
                        <tbody>
                          {labelSenders.map((s) =>
                            editingSender === s.sender_email ? (
                              <tr key={s.sender_email} style={{ borderTop: '1px solid #f3f4f6', background: '#f9fafb' }}>
                                <td colSpan={4} style={{ padding: '8px 0' }}>
                                  <div style={{ fontWeight: 500, marginBottom: 2 }}>{s.sender_name ?? s.sender_email}</div>
                                  <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 4 }}>{s.sender_domain}</div>
                                  {s.sample_subjects.length > 0 && (
                                    <button
                                      style={{ fontSize: 11, padding: '1px 6px', marginBottom: 8, color: '#6b7280', cursor: 'pointer' }}
                                      onClick={() => setSubjectsModal({ name: s.sender_name ?? s.sender_email, subjects: s.sample_subjects })}
                                    >
                                      {s.sample_subjects.length} subject{s.sample_subjects.length !== 1 ? 's' : ''} — view to decide
                                    </button>
                                  )}
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
                                    {CUSTOM_LABELS.map((label) => (
                                      <button
                                        key={label}
                                        onClick={() =>
                                          setEditingLabels((prev) =>
                                            prev.includes(label)
                                              ? prev.filter((l) => l !== label)
                                              : prev.length < 3 ? [...prev, label] : prev
                                          )
                                        }
                                        style={{
                                          padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600, cursor: 'pointer',
                                          border: editingLabels.includes(label) ? '2px solid #111827' : '1px solid #e5e7eb',
                                          background: editingLabels.includes(label) ? (LABEL_COLORS[label] ?? '#f3f4f6') : 'white',
                                        }}
                                      >
                                        {label}
                                      </button>
                                    ))}
                                  </div>
                                  <div style={{ display: 'flex', gap: 6 }}>
                                    <button style={{ fontSize: 12 }} onClick={() => void handleEditSave(s.sender_email, editingLabels)}>
                                      Save
                                    </button>
                                    <button style={{ fontSize: 12 }} onClick={() => setEditingSender(null)}>
                                      Cancel
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ) : (
                              <tr key={s.sender_email} style={{ borderTop: '1px solid #f3f4f6' }}>
                                <td style={{ padding: '6px 0' }}>
                                  <div style={{ fontWeight: 500 }}>{s.sender_name ?? s.sender_email}</div>
                                  <div style={{ fontSize: 11, color: '#9ca3af' }}>{s.sender_domain}</div>
                                  {s.sample_subjects.length > 0 && (
                                    <button
                                      style={{ fontSize: 11, padding: '1px 6px', marginTop: 3, color: '#6b7280', cursor: 'pointer' }}
                                      onClick={() => setSubjectsModal({ name: s.sender_name ?? s.sender_email, subjects: s.sample_subjects })}
                                    >
                                      {s.sample_subjects.length} subject{s.sample_subjects.length !== 1 ? 's' : ''}
                                    </button>
                                  )}
                                </td>
                                <td style={{ padding: '6px 8px' }}>{s.email_count}</td>
                                <td style={{ padding: '6px 0' }}>
                                  {s.custom_labels.map((l) => (
                                    <LabelBadgeWithSource key={l} label={l} source={s.label_sources[l]} />
                                  ))}
                                </td>
                                <td style={{ padding: '6px 0', minWidth: 120 }}>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-start' }}>
                                    <button
                                      style={{ fontSize: 11, padding: '2px 6px' }}
                                      onClick={() => {
                                        setEditingSender(s.sender_email)
                                        setEditingLabels([...s.custom_labels])
                                      }}
                                    >
                                      Edit
                                    </button>
                                    {userGmailLabels.length > 0 && (
                                      gmailLabelDropdown === s.sender_email ? (
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                          {userGmailLabels.map((gl) => (
                                            <label key={gl.id} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, cursor: 'pointer' }}>
                                              <input
                                                type="checkbox"
                                                checked={s.suggested_gmail_labels.includes(gl.name ?? '')}
                                                onChange={() => void handleGmailLabelSave(s.sender_email, gl.name ?? '', s.suggested_gmail_labels)}
                                              />
                                              {gl.name}
                                            </label>
                                          ))}
                                          <button style={{ fontSize: 11, padding: '1px 4px', marginTop: 2 }} onClick={() => setGmailLabelDropdown(null)}>Done</button>
                                        </div>
                                      ) : (
                                        <button
                                          style={{ fontSize: 11, padding: '2px 6px', color: '#6b7280' }}
                                          onClick={() => setGmailLabelDropdown(s.sender_email)}
                                        >
                                          {s.suggested_gmail_labels.length > 0
                                            ? `Gmail: ${s.suggested_gmail_labels.join(', ')}`
                                            : '+ Gmail label'}
                                        </button>
                                      )
                                    )}
                                  </div>
                                </td>
                              </tr>
                            )
                          )}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Unclassified senders */}
          <div style={{ marginTop: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h3 style={{ margin: 0, fontSize: 15 }}>
                Unclassified senders ({summary.unclassified.sender_count})
              </h3>
              <button
                onClick={handleLoadUnclassified}
                disabled={loadingUnclassified}
                style={{ fontSize: 12 }}
              >
                {loadingUnclassified ? 'Loading…' : unclassified === null ? 'Load' : 'Refresh'}
              </button>
            </div>
            <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 2 }}>
              Assign a label to cover all emails from that sender. Life Admin senders (utilities, landlord) are common here.
            </div>

            {unclassified !== null && (
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {unclassified.length === 0 ? (
                  <div style={{ fontSize: 13, color: '#6b7280' }}>All senders are classified.</div>
                ) : (
                  unclassified.map((s) => (
                    <UnclassifiedSenderRow
                      key={s.sender_email}
                      sender={s}
                      busy={assigning === s.sender_email}
                      onAssign={(labels) => handleManualAssign(s.sender_email, labels)}
                    />
                  ))
                )}
              </div>
            )}
          </div>

          {/* Filter suggestions */}
          {filterQueries && filterQueries.some((fq) => fq.query) && (
            <FilterSuggestionsPanel filterQueries={filterQueries} onRefresh={onRefresh} />
          )}
        </>
      )}

      {!summary && !error && (
        <div style={{ marginTop: 16, fontSize: 13, color: '#9ca3af' }}>
          Click "Run Classification" to analyze your senders and generate label suggestions.
        </div>
      )}
    </div>
  )
}

function SubjectsModal({
  senderName,
  subjects,
  onClose,
}: {
  senderName: string
  subjects: string[]
  onClose: () => void
}) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'white', borderRadius: 12, padding: '1.25rem',
          maxWidth: 540, width: '90%', maxHeight: '70vh',
          display: 'flex', flexDirection: 'column', boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{senderName}</div>
            <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 2 }}>{subjects.length} sample subjects</div>
          </div>
          <button
            onClick={onClose}
            style={{ fontSize: 16, border: 'none', background: 'none', cursor: 'pointer', color: '#6b7280', padding: '2px 6px' }}
          >
            ✕
          </button>
        </div>
        <div style={{ overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {subjects.map((s, i) => (
            <div
              key={i}
              style={{
                padding: '7px 10px', borderRadius: 6, background: '#f9fafb',
                fontSize: 13, color: '#374151', fontStyle: 'italic',
              }}
            >
              "{s}"
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function FilterSuggestionsPanel({ filterQueries, onRefresh }: { filterQueries: FilterQuery[], onRefresh: () => Promise<void> }) {
  const [copied, setCopied] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  async function copyQuery(label: string, query: string) {
    try {
      await navigator.clipboard.writeText(query)
      setCopied(label)
      window.setTimeout(() => setCopied((cur) => (cur === label ? null : cur)), 1500)
    } catch {
      // ignore
    }
  }

  async function handleRefresh() {
    setRefreshing(true)
    try { await onRefresh() } finally { setRefreshing(false) }
  }

  const active = filterQueries.filter((fq) => fq.query)

  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <div style={{ fontWeight: 600, fontSize: 14 }}>Filter Suggestions for Gmail</div>
        <button
          style={{ fontSize: 11, padding: '2px 8px', marginLeft: 'auto', color: '#6b7280' }}
          onClick={() => void handleRefresh()}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 10 }}>
        Paste a query into Gmail's filter creation dialog (Search → Show search options → Create filter).
        Each query covers all senders classified under that label.
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {active.map((fq) => (
          <div
            key={fq.label}
            style={{ padding: '10px 12px', border: '1px solid #e5e7eb', borderRadius: 10, background: '#f9fafb' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <LabelBadge label={fq.label} />
              <span style={{ fontSize: 12, color: '#9ca3af' }}>{fq.sender_count} sender{fq.sender_count !== 1 ? 's' : ''}</span>
              {copied === fq.label && (
                <span style={{ fontSize: 12, color: '#059669', marginLeft: 'auto' }}>Copied!</span>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <code
                style={{
                  flex: 1,
                  fontSize: 11,
                  padding: '6px 8px',
                  background: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: 6,
                  wordBreak: 'break-all',
                  fontFamily: 'ui-monospace, monospace',
                  color: '#374151',
                }}
              >
                {fq.query}
              </code>
              <button style={{ fontSize: 12, flexShrink: 0 }} onClick={() => void copyQuery(fq.label, fq.query)}>
                Copy
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function UnclassifiedSenderRow({
  sender,
  busy,
  onAssign,
}: {
  sender: UnclassifiedSender
  busy: boolean
  onAssign: (labels: string[]) => void
}) {
  const [selected, setSelected] = useState<string[]>([])

  function toggle(label: string) {
    setSelected((prev) =>
      prev.includes(label) ? prev.filter((l) => l !== label) : prev.length < 3 ? [...prev, label] : prev,
    )
  }

  return (
    <div
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        padding: '8px 12px',
        background: 'white',
        display: 'flex',
        gap: 12,
        flexWrap: 'wrap',
        alignItems: 'flex-start',
      }}
    >
      <div style={{ flex: 1, minWidth: 160 }}>
        <div style={{ fontWeight: 500, fontSize: 13 }}>{sender.sender_name ?? sender.sender_email}</div>
        <div style={{ fontSize: 11, color: '#9ca3af' }}>{sender.sender_domain}</div>
        <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
          {sender.email_count} emails
        </div>
        {sender.sample_subjects.length > 0 && (
          <div style={{ marginTop: 4 }}>
            {sender.sample_subjects.slice(0, 2).map((s, i) => (
              <div key={i} style={{ fontSize: 11, color: '#6b7280', fontStyle: 'italic' }}>"{s}"</div>
            ))}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {CUSTOM_LABELS.map((label) => (
            <button
              key={label}
              onClick={() => toggle(label)}
              style={{
                padding: '2px 8px',
                borderRadius: 12,
                fontSize: 11,
                fontWeight: 600,
                border: selected.includes(label) ? '2px solid #111827' : '1px solid #e5e7eb',
                background: selected.includes(label) ? (LABEL_COLORS[label] ?? '#f3f4f6') : 'white',
                cursor: 'pointer',
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            disabled={busy || selected.length === 0}
            onClick={() => onAssign(selected)}
            style={{ fontSize: 12 }}
          >
            {busy ? 'Saving…' : 'Assign'}
          </button>
          <button
            disabled={busy}
            onClick={() => onAssign([])}
            style={{ fontSize: 12 }}
          >
            Skip
          </button>
        </div>
      </div>
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

function GmailLabels({
  account,
  labels,
  filters,
  filtersError,
  filterQueries,
}: {
  account: EmailAccount | null
  labels: GmailLabel[] | null
  filters: GmailFilterRule[] | null
  filtersError: string | null
  filterQueries: FilterQuery[] | null
}) {
  const [copied, setCopied] = useState<string | null>(null)

  async function copyQuery(key: string, text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(key)
      window.setTimeout(() => setCopied((cur) => (cur === key ? null : cur)), 1500)
    } catch {
      // ignore
    }
  }

  if (!account) return <div style={{ marginTop: 12, color: '#6b7280' }}>Select an account.</div>

  const queryByLabel = new Map((filterQueries ?? []).map((fq) => [fq.label.toLowerCase(), fq]))

  // Build a map from label id → list of filters that apply it
  const filtersByLabelId = new Map<string, GmailFilterRule[]>()
  for (const f of filters ?? []) {
    for (const lid of f.action.add_label_ids ?? []) {
      if (!filtersByLabelId.has(lid)) filtersByLabelId.set(lid, [])
      filtersByLabelId.get(lid)!.push(f)
    }
  }

  const userLabels = (labels ?? []).filter((l) => l.type === 'user')
  const systemLabels = (labels ?? []).filter((l) => l.type !== 'user')

  return (
    <div style={{ marginTop: 12 }}>
      {filtersError ? <div style={{ color: '#b91c1c', marginBottom: 8, fontSize: 13 }}>{filtersError}</div> : null}
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 10 }}>
        Your Gmail labels. User-defined labels show their associated filters and suggested filter query.
        Paste a suggested query into Gmail → Search options → Create filter to apply the label automatically.
      </div>

      {!labels ? (
        <div style={{ color: '#6b7280' }}>Loading…</div>
      ) : (
        <>
          {userLabels.length > 0 && (
            <>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Your labels</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
                {userLabels.map((l) => {
                  const match = queryByLabel.get((l.name ?? '').toLowerCase())
                  const existingFilters = filtersByLabelId.get(l.id) ?? []
                  const copyKey = `q-${l.id}`
                  return (
                    <div
                      key={l.id}
                      style={{ padding: '10px 12px', border: '1px solid #e5e7eb', borderRadius: 10, background: '#f9fafb' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>
                          {match ? <LabelBadge label={l.name ?? ''} /> : l.name}
                        </div>
                        <div style={{ fontSize: 12, color: '#6b7280' }}>
                          {l.messages_total == null ? '—' : l.messages_total.toLocaleString()}
                          {l.messages_unread ? ` (${l.messages_unread} unread)` : ''}
                        </div>
                      </div>

                      {/* Suggested filter query from label suggestions */}
                      {match?.query ? (
                        <div style={{ marginTop: 8 }}>
                          <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 4 }}>Suggested filter query</div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <code style={{
                              flex: 1, fontSize: 11, padding: '4px 8px', background: 'white',
                              border: '1px solid #e5e7eb', borderRadius: 6, wordBreak: 'break-all',
                              fontFamily: 'ui-monospace, monospace', color: '#374151',
                            }}>
                              {match.query}
                            </code>
                            <button style={{ fontSize: 11, flexShrink: 0 }} onClick={() => void copyQuery(copyKey, match.query)}>
                              {copied === copyKey ? 'Copied!' : 'Copy'}
                            </button>
                          </div>
                        </div>
                      ) : null}

                      {/* Existing Gmail filters that apply this label */}
                      {existingFilters.length > 0 ? (
                        <div style={{ marginTop: 8 }}>
                          <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 4 }}>
                            Existing filter{existingFilters.length !== 1 ? 's' : ''} ({existingFilters.length})
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            {existingFilters.map((f) => {
                              const parts: string[] = []
                              if (f.criteria.from) parts.push(`from:${f.criteria.from}`)
                              if (f.criteria.to) parts.push(`to:${f.criteria.to}`)
                              if (f.criteria.subject) parts.push(`subject:(${f.criteria.subject})`)
                              if (f.criteria.query) parts.push(f.criteria.query)
                              const query = parts.join(' ').trim() || '(no criteria)'
                              const fCopyKey = `f-${f.id}`
                              return (
                                <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                  <code style={{
                                    flex: 1, fontSize: 11, padding: '4px 8px', background: 'white',
                                    border: '1px solid #e5e7eb', borderRadius: 6, wordBreak: 'break-all',
                                    fontFamily: 'ui-monospace, monospace', color: '#6b7280',
                                  }}>
                                    {query}
                                  </code>
                                  <button style={{ fontSize: 11, flexShrink: 0 }} onClick={() => void copyQuery(fCopyKey, query)}>
                                    {copied === fCopyKey ? 'Copied!' : 'Copy'}
                                  </button>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  )
                })}
              </div>
            </>
          )}

          {systemLabels.length > 0 && (
            <>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6, color: '#6b7280' }}>System labels</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {systemLabels.map((l) => (
                  <div key={l.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 12px', fontSize: 13, color: '#9ca3af' }}>
                    <span>{l.name}</span>
                    <span>{l.messages_total == null ? '—' : l.messages_total.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </>
          )}
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

