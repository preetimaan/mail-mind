import { useState, useEffect } from 'react'
import { api, CustomCategory, AISuggestResponse } from '../api/client'
import LoadingSpinner from './LoadingSpinner'

interface SenderInput {
  email: string
  name?: string | null
  count?: number
}

interface AISuggestModalProps {
  isOpen: boolean
  onClose: () => void
  username: string
  senders: SenderInput[]
  customCategories: CustomCategory[]
  onApplied: () => void
}

export default function AISuggestModal({
  isOpen,
  onClose,
  username,
  senders,
  customCategories,
  onApplied,
}: AISuggestModalProps) {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<AISuggestResponse | null>(null)
  const [applyTarget, setApplyTarget] = useState<Record<number, number | 'new'>>({})
  const [newCategoryName, setNewCategoryName] = useState<Record<number, string>>({})
  const [applying, setApplying] = useState(false)

  useEffect(() => {
    if (!isOpen || senders.length === 0) {
      setData(null)
      setApplyTarget({})
      return
    }
    setLoading(true)
    api
      .post<AISuggestResponse>('/api/insights/ai-suggest-categories', {
        senders: senders.map((s) => ({ email: s.email, name: s.name ?? undefined, count: s.count })),
      })
      .then((res) => {
        setData(res.data)
        setApplyTarget({})
      })
      .catch((err) => {
        console.error('AI suggest failed:', err)
        setData({ suggestions: [], provider: 'rules' })
      })
      .finally(() => setLoading(false))
  }, [isOpen, username, senders])

  const applyOne = async (index: number) => {
    const target = applyTarget[index]
    const sug = data?.suggestions?.[index]
    if (!sug) return
    setApplying(true)
    try {
      let categoryId: number
      if (target === 'new') {
        const name = (newCategoryName[index] || sug.suggested_category).trim() || sug.suggested_category
        const createRes = await api.post<CustomCategory>('/api/insights/custom-categories', { name })
        categoryId = createRes.data.id
      } else if (typeof target === 'number') {
        categoryId = target
      } else {
        setApplying(false)
        return
      }
      await api.post(`/api/insights/custom-categories/${categoryId}/senders`, {
        sender_emails: [sug.sender_email],
      })
      onApplied()
    } catch (err: any) {
      alert(err.response?.data?.detail || err.userMessage || 'Failed to apply')
    } finally {
      setApplying(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content" style={{ maxWidth: 640, maxHeight: '90vh', overflow: 'auto' }}>
        <div className="modal-header">
          <h2>Suggest categories</h2>
          <button type="button" className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-body">
          {loading ? (
            <LoadingSpinner message="Analyzing senders..." size="small" />
          ) : data ? (
            <>
              <p style={{ fontSize: '0.9rem', color: '#555', marginBottom: '1rem' }}>
                Provider: <strong>{data.provider === 'openai' ? 'OpenAI' : 'Rule-based'}</strong>. Apply suggestions to your custom categories below.
              </p>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #eee' }}>
                      <th style={{ textAlign: 'left', padding: '0.5rem' }}>Sender</th>
                      <th style={{ textAlign: 'left', padding: '0.5rem' }}>Suggested</th>
                      <th style={{ textAlign: 'left', padding: '0.5rem' }}>Apply to</th>
                      <th style={{ padding: '0.5rem' }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.suggestions.map((s, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '0.5rem' }} title={s.sender_email}>
                          {s.sender_name || s.sender_email}
                        </td>
                        <td style={{ padding: '0.5rem' }}>
                          {s.suggested_category}
                          {s.suggested_subcategory ? ` / ${s.suggested_subcategory}` : ''}
                        </td>
                        <td style={{ padding: '0.5rem' }}>
                          <select
                            value={applyTarget[i] === undefined ? '' : applyTarget[i]}
                            onChange={(e) => {
                              const v = e.target.value
                              if (v === 'new') setApplyTarget((prev) => ({ ...prev, [i]: 'new' }))
                              else if (v) setApplyTarget((prev) => ({ ...prev, [i]: Number(v) }))
                            }}
                            style={{ padding: '0.35rem', minWidth: 140, borderRadius: 4 }}
                          >
                            <option value="">—</option>
                            {customCategories.map((c) => (
                              <option key={c.id} value={c.id}>
                                {c.name}
                              </option>
                            ))}
                            <option value="new">Create new...</option>
                          </select>
                          {applyTarget[i] === 'new' && (
                            <input
                              type="text"
                              placeholder="Category name"
                              value={newCategoryName[i] ?? ''}
                              onChange={(e) => setNewCategoryName((prev) => ({ ...prev, [i]: e.target.value }))}
                              style={{ marginLeft: '0.5rem', padding: '0.35rem', width: 120, borderRadius: 4, border: '1px solid #ccc' }}
                            />
                          )}
                        </td>
                        <td style={{ padding: '0.5rem' }}>
                          <button
                            type="button"
                            className="button"
                            disabled={applying || applyTarget[i] === undefined || (applyTarget[i] === 'new' && !(newCategoryName[i] || data.suggestions[i]?.suggested_category)?.trim())}
                            onClick={() => applyOne(i)}
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.85rem' }}
                          >
                            Apply
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
