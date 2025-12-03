import { useState, useEffect } from 'react'
import { api, Summary, SenderInsights, CategoryInsights, FrequencyInsights } from '../api/client'

export function useInsights(username: string | null, selectedAccount: number | null) {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [senderInsights, setSenderInsights] = useState<SenderInsights | null>(null)
  const [categoryInsights, setCategoryInsights] = useState<CategoryInsights | null>(null)
  const [frequencyInsights, setFrequencyInsights] = useState<FrequencyInsights | null>(null)
  const [yearlyFrequencyInsights, setYearlyFrequencyInsights] = useState<any>(null)

  const loadSummary = async () => {
    if (!username) return
    
    try {
      const response = await api.get(`/api/insights/summary?username=${username}`)
      setSummary(response.data)
    } catch (err: any) {
      if (err.response?.status === 404) {
        setSummary({
          total_accounts: 0,
          total_emails: 0,
          total_senders: 0,
          accounts: []
        })
      } else {
        console.error('Failed to load summary:', err)
        // Don't clear summary on error - keep existing data
        // This prevents counts from disappearing on transient errors
      }
    }
  }

  const loadInsights = async () => {
    if (!selectedAccount || !username) return
    
    try {
      const [senders, categories, frequency, yearlyFrequency] = await Promise.all([
        api.get(`/api/insights/senders?username=${username}&account_id=${selectedAccount}`),
        api.get(`/api/insights/categories?username=${username}&account_id=${selectedAccount}`),
        api.get(`/api/insights/frequency?username=${username}&account_id=${selectedAccount}`),
        api.get(`/api/insights/frequency/yearly?username=${username}&account_id=${selectedAccount}`).catch(() => ({ data: null }))
      ])
      
      setSenderInsights(senders.data)
      setCategoryInsights(categories.data)
      setFrequencyInsights(frequency.data)
      if (yearlyFrequency && yearlyFrequency.data && yearlyFrequency.data.years && yearlyFrequency.data.years.length > 0) {
        setYearlyFrequencyInsights(yearlyFrequency.data)
      } else {
        setYearlyFrequencyInsights(null)
      }
    } catch (err: any) {
      console.error('Failed to load insights:', err)
    }
  }

  useEffect(() => {
    if (username) {
      loadSummary()
    }
  }, [username])

  useEffect(() => {
    if (username && selectedAccount) {
      loadInsights()
    }
  }, [username, selectedAccount])

  return {
    summary,
    senderInsights,
    categoryInsights,
    frequencyInsights,
    yearlyFrequencyInsights,
    loadSummary,
    loadInsights,
  }
}

