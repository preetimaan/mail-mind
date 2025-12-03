import { useState, useEffect } from 'react'
import { api, EmailAccount } from '../api/client'

export function useAccounts(username: string | null) {
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const loadAccounts = async (retryCount = 0) => {
    if (!username) {
      return
    }
    
    // Don't retry more than 2 times
    if (retryCount > 2) {
      setError('Failed to load accounts after multiple attempts. Please refresh the page.')
      setLoading(false)
      return
    }
    
    try {
      setError(null)
      setLoading(true)
      const response = await api.get(`/api/emails/accounts?username=${username}`, {
        timeout: 30000, // 30 seconds timeout (reduced from 60)
      })
      const loadedAccounts = response.data || []
      setAccounts(loadedAccounts)
      setLoading(false)
      
      // Auto-select first account if we have accounts and no account is selected
      if (loadedAccounts.length > 0) {
        // Only auto-select if no account is currently selected, or if the selected account is not in the new list
        const currentAccountExists = selectedAccount && loadedAccounts.some((a: { id: number }) => a.id === selectedAccount)
        if (!currentAccountExists) {
          setSelectedAccount(loadedAccounts[0].id)
        }
      } else {
        // No accounts, clear selection
        setSelectedAccount(null)
      }
    } catch (err: any) {
      console.error('Error loading accounts:', err)
      setLoading(false)
      
      // Handle timeout errors with automatic retry
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout') || err.userMessage?.includes('timeout')) {
        // Timeout error - retry automatically after a short delay
        if (retryCount < 2) {
          setError(`Request timed out. Retrying... (${retryCount + 1}/2)`)
          setTimeout(() => {
            loadAccounts(retryCount + 1)
          }, 2000) // Wait 2 seconds before retry
        } else {
          // Don't clear accounts on timeout - keep existing accounts if available
          setError('Request timed out. Please refresh the page or try again later.')
          if (accounts.length === 0) {
            setAccounts([])
            setSelectedAccount(null)
          }
        }
      } else if (err.response?.status === 404) {
        // User not found - this is expected for new users
        setError(null)
        setAccounts([])
        setSelectedAccount(null)
      } else {
        // Other errors - clear accounts
        setAccounts([])
        setSelectedAccount(null)
        const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || err.message || 'Failed to load accounts'
        setError(`Failed to load accounts: ${errorMessage}`)
      }
    }
  }

  useEffect(() => {
    if (username) {
      // Clear any previous errors when username changes or on mount
      setError(null)
      loadAccounts()
    } else {
      setAccounts([])
      setSelectedAccount(null)
      setError(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username])

  const handleAccountAdded = () => {
    loadAccounts()
  }

  const handleDeleteAccount = async (accountId: number) => {
    if (!username) return
    
    // Note: Confirmation is handled in AccountSelector component before calling this function
    try {
      await api.delete(`/api/emails/accounts/${accountId}?username=${username}`)
      loadAccounts()
      if (selectedAccount === accountId) {
        setSelectedAccount(null)
      }
    } catch (err: any) {
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || err.message || 'Failed to delete account'
      setError(`Failed to delete account: ${errorMessage}`)
    }
  }

  return {
    accounts,
    selectedAccount,
    setSelectedAccount,
    error,
    loading,
    loadAccounts,
    handleAccountAdded,
    handleDeleteAccount,
  }
}

