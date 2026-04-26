export type Provider = 'gmail' | 'yahoo'

export type EmailAccount = {
  id: number
  username: string
  provider: Provider
  email: string
  is_active: boolean
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
}

