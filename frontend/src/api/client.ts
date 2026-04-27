export type Provider = 'gmail' | 'yahoo'

export type EmailAccount = {
  id: number
  username: string
  provider: Provider
  email: string
  is_active: boolean
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
  startAnalysis: async (body: { account_id: number; start_date: string; end_date_exclusive: string }) => {
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
}

