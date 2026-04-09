import { useState, useEffect } from 'react'
import { login, ACCESS_TOKEN_KEY } from '../api/client'

export function useUsername() {
  const [usernameInput, setUsernameInput] = useState('')
  const [username, setUsername] = useState('')
  const [authError, setAuthError] = useState<string | null>(null)
  const [loginSubmitting, setLoginSubmitting] = useState(false)

  // Restore session from localStorage
  useEffect(() => {
    const savedUsername = localStorage.getItem('mailmind_username')
    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (savedUsername && token) {
      setUsernameInput(savedUsername)
      setUsername(savedUsername)
    }
  }, [])

  const handleUsernameSubmit = async () => {
    const trimmed = usernameInput.trim()
    if (!trimmed) return
    setAuthError(null)
    setLoginSubmitting(true)
    try {
      await login(trimmed)
      setUsername(trimmed)
      localStorage.setItem('mailmind_username', trimmed)
    } catch (err: unknown) {
      const e = err as { userMessage?: string; response?: { data?: { detail?: string } } }
      setAuthError(
        e.userMessage || e.response?.data?.detail || 'Login failed. Check JWT_SECRET on the server.',
      )
    } finally {
      setLoginSubmitting(false)
    }
  }

  const handleUsernameKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      void handleUsernameSubmit()
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('mailmind_username')
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    setUsername('')
    setUsernameInput('')
    setAuthError(null)
  }

  return {
    usernameInput,
    setUsernameInput,
    username,
    setUsername,
    handleUsernameSubmit,
    handleUsernameKeyPress,
    handleLogout,
    authError,
    loginSubmitting,
  }
}
