import { useState, useEffect } from 'react'

export function useUsername() {
  const [usernameInput, setUsernameInput] = useState('')
  const [username, setUsername] = useState('')

  // Load username from localStorage on mount
  useEffect(() => {
    const savedUsername = localStorage.getItem('mailmind_username')
    if (savedUsername) {
      setUsernameInput(savedUsername)
      setUsername(savedUsername)
    }
  }, [])

  const handleUsernameSubmit = () => {
    const trimmed = usernameInput.trim()
    if (trimmed) {
      setUsername(trimmed)
      localStorage.setItem('mailmind_username', trimmed)
    }
  }

  const handleUsernameKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleUsernameSubmit()
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('mailmind_username')
    setUsername('')
    setUsernameInput('')
  }

  return {
    usernameInput,
    setUsernameInput,
    username,
    setUsername,
    handleUsernameSubmit,
    handleUsernameKeyPress,
    handleLogout,
  }
}

