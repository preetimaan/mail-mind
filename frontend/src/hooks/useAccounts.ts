import { useState, useEffect } from 'react'
import { api, EmailAccount } from '../api/client'

export function useAccounts(username: string | null) {
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadAccounts = async () => {
    if (!username) {
      return
    }
    
    try {
      setError(null)
      const response = await api.get(`/api/emails/accounts?username=${username}`)
      const loadedAccounts = response.data || []
      setAccounts(loadedAccounts)
      
      // Auto-select first account if we have accounts and no account is selected
      if (loadedAccounts.length > 0) {
        // Only auto-select if no account is currently selected, or if the selected account is not in the new list
        const currentAccountExists = selectedAccount && loadedAccounts.some(a => a.id === selectedAccount)
        if (!currentAccountExists) {
          setSelectedAccount(loadedAccounts[0].id)
        }
      } else {
        // No accounts, clear selection
        setSelectedAccount(null)
      }
    } catch (err: any) {
      console.error('Error loading accounts:', err)
      setAccounts([])
      setSelectedAccount(null)
      if (err.response?.status === 404) {
        setError(null)
        setAccounts([])
      } else {
        const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || err.message || 'Failed to load accounts'
        setError(`Failed to load accounts: ${errorMessage}`)
      }
    }
  }

  useEffect(() => {
    if (username) {
      loadAccounts()
    } else {
      setAccounts([])
      setSelectedAccount(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username])

  const handleAccountAdded = () => {
    loadAccounts()
  }

  const handleDeleteAccount = async (accountId: number) => {
    if (!username) return
    
    if (!window.confirm('Are you sure you want to delete this account? This action cannot be undone.')) {
      return
    }

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
    loadAccounts,
    handleAccountAdded,
    handleDeleteAccount,
  }
}

