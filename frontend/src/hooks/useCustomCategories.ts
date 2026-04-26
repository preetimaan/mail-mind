import { useState, useEffect, useCallback } from 'react'
import { api, CustomCategory } from '../api/client'

export function useCustomCategories(username: string | null) {
  const [customCategories, setCustomCategories] = useState<CustomCategory[]>([])
  const [loading, setLoading] = useState(false)

  const loadCustomCategories = useCallback(async () => {
    if (!username) return
    setLoading(true)
    try {
      const res = await api.get<CustomCategory[]>(`/api/insights/custom-categories?username=${username}`)
      setCustomCategories(Array.isArray(res.data) ? res.data : [])
    } catch (err) {
      console.error('Failed to load custom categories:', err)
      setCustomCategories([])
    } finally {
      setLoading(false)
    }
  }, [username])

  useEffect(() => {
    if (username) {
      loadCustomCategories()
    } else {
      setCustomCategories([])
    }
  }, [username, loadCustomCategories])

  return { customCategories, loadCustomCategories, loading }
}
