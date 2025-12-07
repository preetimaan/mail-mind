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

// Response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle structured error responses
    if (error.response?.data?.error) {
      const errorData = error.response.data.error
      error.userMessage = errorData.message || error.message
      error.errorCode = errorData.code
      error.metadata = errorData.metadata || {}
    } else {
      // Fallback for non-structured errors
      error.userMessage = error.response?.data?.detail || error.message || 'An unexpected error occurred'
      error.errorCode = 'UNKNOWN_ERROR'
      error.metadata = {}
    }
    
    // Handle specific error codes
    if (error.response?.status === 429) {
      const retryAfter = error.metadata?.retry_after
      if (retryAfter) {
        error.userMessage = `Rate limit exceeded. Please try again in ${retryAfter} seconds.`
      } else {
        error.userMessage = 'Rate limit exceeded. Please try again later.'
      }
    } else if (error.response?.status === 502) {
      error.userMessage = 'Unable to connect to email service. Please check your credentials and try again.'
    } else if (error.code === 'ECONNABORTED') {
      error.userMessage = 'Request timed out. Please try again.'
    } else if (!error.response) {
      error.userMessage = 'Unable to connect to server. Please check your connection.'
    }
    
    return Promise.reject(error)
  }
)

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
  total_emails?: number | null
  start_date: string
  end_date: string
  created_at: string
  completed_at: string | null
  error_message?: string | null
}

export interface StopAnalysisResponse {
  run_id: number
  status: string
  message: string
}

export interface AnalysisRunsResponse {
  runs: AnalysisRun[]
  total: number
  has_more: boolean
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

export interface YearlyFrequencyInsights {
  years: number[]
  yearly_totals: Record<number, number>
  yearly_averages: Record<number, number>
  yearly_stats: Record<number, {
    total_emails: number
    unique_days: number
    daily_average: number
    monthly_distribution: Record<number, number>
    peak_month: number | null
    months_with_data: number
  }>
  year_over_year: Array<{
    year: number
    total_emails: number
    daily_average: number
    change_from_previous: number | null
    change_percent: number | null
  }>
}

export interface OAuthAuthorizeResponse {
  authorization_url: string
  state: string
}

export interface TestConnectionResponse {
  success: boolean
  message: string
}

