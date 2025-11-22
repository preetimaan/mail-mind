import axios from 'axios'

// Use Vite proxy in development, or explicit URL in production
const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '' : 'http://localhost:8000')

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
})

export interface EmailAccount {
  id: number
  provider: string
  email: string
  is_active: boolean
  created_at: string
}

export interface AnalysisRequest {
  username: string
  account_id: number
  start_date: string
  end_date: string
}

export interface AnalysisRun {
  id: number
  account_id: number
  status: string
  emails_processed: number
  start_date: string
  end_date: string
  created_at: string
  completed_at: string | null
}

export interface Summary {
  total_accounts: number
  total_emails: number
  total_senders: number
  accounts: Array<{
    id: number
    email: string
    provider: string
    email_count: number
    sender_count: number
    processed_ranges: number
  }>
}

export interface SenderInsights {
  top_senders: Array<{
    email: string
    name: string | null
    count: number
    percentage: number
  }>
  top_domains: Array<{
    domain: string
    count: number
  }>
  total_emails: number
}

export interface CategoryInsights {
  categories: Array<{
    category: string
    count: number
    percentage: number
  }>
  total: number
}

export interface FrequencyInsights {
  daily_average: number
  total_emails: number
  unique_days: number
  peak_hour: number | null
  hourly_distribution: Record<number, number>
  weekday_distribution: Record<string, number>
}

