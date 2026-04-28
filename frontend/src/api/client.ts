export type Provider = 'gmail' | 'yahoo'

export type EmailAccount = {
  id: number
  username: string
  provider: Provider
  email: string
  is_active: boolean
  is_connected: boolean
}

export type AnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'

export type AnalysisRun = {
  id: number
  account_id: number
  start_date: string
  end_date_exclusive: string
  status: AnalysisStatus
  emails_processed: number
  total_emails: number
  error_message: string | null
}

export type ProcessedRange = {
  start_date: string
  end_date_exclusive: string
  emails_count: number
  processed_at: string
  /** Present when this row is a completed analysis run; omitted for merged legacy chunks. */
  analysis_run_id?: number | null
}

export type ProcessedRangeGap = {
  start_date: string
  end_date_exclusive: string
  days: number
}

export type InsightsSummary = {
  all_accounts: { total_accounts: number; total_emails: number; total_senders: number }
  current_account: { account_emails: number; account_senders: number; processed_ranges: number }
}

export type SenderInsights = {
  total_emails: number
  top_senders: Array<{ email: string; name: string | null; count: number }>
  top_domains: Array<{ domain: string; count: number }>
}

export type SenderMessageSample = {
  received_at: string
  subject: string
  sender_name: string | null
  headers: Record<string, string> | null
}

export type SenderSamplesResponse = {
  sender_email: string
  samples: SenderMessageSample[]
}

export type CategoryInsights = {
  total: number
  categories: Array<{ category: string; count: number; percentage: number }>
}

export type YearlyFrequencyInsights = {
  years: number[]
  year_over_year: Array<{
    year: number
    total_emails: number
    daily_average: number
    change_from_previous: number | null
    change_percent: number | null
  }>
}

const API_BASE = 'http://localhost:8000/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `HTTP ${res.status}`)
  }
  return (await res.json()) as T
}

export const api = {
  listAccounts: async (username: string) => {
    const qs = new URLSearchParams({ username })
    return await request<EmailAccount[]>(`/emails/accounts?${qs.toString()}`)
  },
  createAccount: async (body: { username: string; provider: Provider; email: string }) => {
    return await request<EmailAccount>(`/emails/accounts`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  deleteAccount: async (accountId: number) => {
    return await request<{ message: string }>(`/emails/accounts/${accountId}`, { method: 'DELETE' })
  },
  deactivateAccount: async (accountId: number) => {
    return await request<EmailAccount>(`/emails/accounts/${accountId}/deactivate`, { method: 'POST' })
  },
  disconnectAccount: async (accountId: number) => {
    return await request<{ message: string }>(`/emails/accounts/${accountId}/disconnect`, { method: 'POST' })
  },
  disconnectGmailAccount: async (accountId: number) => {
    return await request<{ message: string; revoke_error?: string }>(`/emails/accounts/${accountId}/disconnect-gmail`, {
      method: 'POST',
    })
  },
  resetAccountData: async (accountId: number) => {
    return await request<{ message: string }>(`/emails/accounts/${accountId}/reset-data`, { method: 'POST' })
  },
  startAnalysis: async (body: { account_id: number; start_date: string; end_date_exclusive: string; force_reanalysis?: boolean }) => {
    return await request<{ run_id: number }>(`/analysis/batch`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
  listRuns: async (accountId: number, limit: number = 5, offset: number = 0) => {
    const qs = new URLSearchParams({
      account_id: String(accountId),
      limit: String(limit),
      offset: String(offset),
    })
    return await request<{ runs: AnalysisRun[]; has_more: boolean }>(`/analysis/runs?${qs.toString()}`)
  },
  getRun: async (runId: number) => {
    return await request<AnalysisRun>(`/analysis/runs/${runId}`)
  },
  stopRun: async (runId: number) => {
    return await request<{ message: string }>(`/analysis/runs/${runId}/stop`, { method: 'POST' })
  },
  retryRun: async (runId: number) => {
    return await request<{ run_id: number }>(`/analysis/runs/${runId}/retry`, { method: 'POST' })
  },
  listProcessedRanges: async (accountId: number) => {
    const qs = new URLSearchParams({ account_id: String(accountId) })
    return await request<ProcessedRange[]>(`/insights/processed-ranges?${qs.toString()}`)
  },
  listProcessedRangeGaps: async (accountId: number) => {
    const qs = new URLSearchParams({ account_id: String(accountId) })
    return await request<ProcessedRangeGap[]>(`/insights/processed-ranges/gaps?${qs.toString()}`)
  },
  getSummary: async (username: string, accountId: number | null) => {
    const qs = new URLSearchParams({
      username,
      ...(accountId ? { account_id: String(accountId) } : {}),
    })
    return await request<InsightsSummary>(`/insights/summary?${qs.toString()}`)
  },
  getSenders: async (accountId: number) => {
    const qs = new URLSearchParams({ account_id: String(accountId) })
    return await request<SenderInsights>(`/insights/senders?${qs.toString()}`)
  },
  getSenderSamples: async (accountId: number, senderEmail: string, limit: number = 5) => {
    const qs = new URLSearchParams({
      account_id: String(accountId),
      sender_email: senderEmail,
      limit: String(limit),
    })
    return await request<SenderSamplesResponse>(`/insights/senders/samples?${qs.toString()}`)
  },
  getCategories: async (accountId: number) => {
    const qs = new URLSearchParams({ account_id: String(accountId) })
    return await request<CategoryInsights>(`/insights/categories?${qs.toString()}`)
  },
  getYearlyFrequency: async (accountId: number) => {
    const qs = new URLSearchParams({ account_id: String(accountId) })
    return await request<YearlyFrequencyInsights>(`/insights/frequency/yearly?${qs.toString()}`)
  },
  startGmailOAuth: async (accountId: number) => {
    return await request<{ auth_url: string }>(`/oauth/gmail/start`, {
      method: 'POST',
      body: JSON.stringify({ account_id: accountId }),
    })
  },
  connectYahooAppPassword: async (accountId: number, appPassword: string) => {
    return await request<{ message: string }>(`/auth/yahoo/app-password`, {
      method: 'POST',
      body: JSON.stringify({ account_id: accountId, app_password: appPassword }),
    })
  },
}

