import { useState } from 'react'
import { api, CustomCategory } from '../api/client'
import ConfirmModal from './ConfirmModal'

interface CustomCategoriesManagerProps {
  username: string
  customCategories: CustomCategory[]
  onUpdate: () => void
}

export default function CustomCategoriesManager({
  username,
  customCategories,
  onUpdate,
}: CustomCategoriesManagerProps) {
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: number; name: string } | null>(null)

  const handleCreate = async () => {
    const name = newName.trim()
    if (!name) return
    setCreating(true)
    try {
      await api.post(`/api/insights/custom-categories?username=${username}`, { name })
      setNewName('')
      onUpdate()
    } catch (err: any) {
      console.error('Create category failed:', err)
      alert(err.response?.data?.detail || err.userMessage || 'Failed to create category')
    } finally {
      setCreating(false)
    }
  }

  const startEdit = (c: CustomCategory) => {
    setEditingId(c.id)
    setEditName(c.name)
  }

  const handleSaveEdit = async () => {
    if (editingId == null) return
    const name = editName.trim()
    if (!name) return
    try {
      await api.patch(`/api/insights/custom-categories/${editingId}?username=${username}`, { name })
      setEditingId(null)
      setEditName('')
      onUpdate()
    } catch (err: any) {
      console.error('Update category failed:', err)
      alert(err.response?.data?.detail || err.userMessage || 'Failed to update category')
    }
  }

  const handleDelete = async () => {
    if (!deleteConfirm) return
    try {
      await api.delete(`/api/insights/custom-categories/${deleteConfirm.id}?username=${username}`)
      setDeleteConfirm(null)
      onUpdate()
    } catch (err: any) {
      console.error('Delete category failed:', err)
      alert(err.response?.data?.detail || err.userMessage || 'Failed to delete category')
    }
  }

  return (
    <div style={{ marginTop: '1rem' }}>
      <h4 style={{ marginBottom: '0.75rem' }}>Custom categories</h4>
      <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem' }}>
        Create categories (e.g. Finance, Urgent) and assign senders from the Top Senders list in Insights.
        Filter the email list by these categories in the Emails tab.
      </p>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="New category name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          style={{ padding: '0.5rem', width: 200, borderRadius: 4, border: '1px solid #ccc' }}
        />
        <button
          type="button"
          className="button"
          onClick={handleCreate}
          disabled={creating || !newName.trim()}
          style={{ padding: '0.5rem 1rem' }}
        >
          {creating ? 'Creating...' : 'Create'}
        </button>
      </div>

      {customCategories.length === 0 ? (
        <p style={{ color: '#666', fontStyle: 'italic' }}>No custom categories yet.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {customCategories.map((c) => (
            <li
              key={c.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 0.75rem',
                background: '#f8f9fa',
                marginBottom: '0.25rem',
                borderRadius: 4,
              }}
            >
              {editingId === c.id ? (
                <>
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit()}
                    style={{ padding: '0.35rem', flex: 1, maxWidth: 200, borderRadius: 4, border: '1px solid #ccc' }}
                    autoFocus
                  />
                  <button type="button" className="button" onClick={handleSaveEdit} style={{ padding: '0.35rem 0.75rem', fontSize: '0.85rem' }}>
                    Save
                  </button>
                  <button type="button" onClick={() => { setEditingId(null); setEditName('') }} style={{ background: 'none', border: '1px solid #999', padding: '0.35rem 0.75rem', borderRadius: 4, cursor: 'pointer', fontSize: '0.85rem' }}>
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <span style={{ fontWeight: 500, flex: 1 }}>{c.name}</span>
                  <button type="button" onClick={() => startEdit(c)} style={{ background: 'none', border: '1px solid #667eea', color: '#667eea', padding: '0.25rem 0.5rem', borderRadius: 4, cursor: 'pointer', fontSize: '0.85rem' }}>
                    Rename
                  </button>
                  <button type="button" onClick={() => setDeleteConfirm({ id: c.id, name: c.name })} style={{ background: 'none', border: '1px solid #dc3545', color: '#dc3545', padding: '0.25rem 0.5rem', borderRadius: 4, cursor: 'pointer', fontSize: '0.85rem' }}>
                    Delete
                  </button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}

      <ConfirmModal
        isOpen={deleteConfirm != null}
        title="Delete category"
        message={`Delete "${deleteConfirm?.name}"? Sender assignments to this category will be removed.`}
        confirmText="Delete"
        confirmButtonStyle="danger"
        onConfirm={handleDelete}
        onClose={() => setDeleteConfirm(null)}
      />
    </div>
  )
}
