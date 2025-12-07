import { useState } from 'react'
import { EmailAccount } from '../api/client'
import ConfirmModal from './ConfirmModal'
import './AddAccountModal.css'

interface DeleteAccountModalProps {
  isOpen: boolean
  onClose: () => void
  accounts: EmailAccount[]
  onDelete: (accountId: number) => void
  loading?: boolean
}

export default function DeleteAccountModal({
  isOpen,
  onClose,
  accounts,
  onDelete,
  loading = false,
}: DeleteAccountModalProps) {
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)

  if (!isOpen) return null

  const selectedAccount = accounts.find(a => a.id === selectedAccountId)

  const handleDeleteClick = () => {
    if (selectedAccountId) {
      setShowConfirm(true)
    }
  }

  const handleConfirmDelete = () => {
    if (selectedAccountId) {
      onDelete(selectedAccountId)
      setShowConfirm(false)
      setSelectedAccountId(null)
      onClose()
    }
  }

  const handleClose = () => {
    setSelectedAccountId(null)
    setShowConfirm(false)
    onClose()
  }

  return (
    <>
      <div className="modal-overlay" onClick={(e) => {
        if (e.target === e.currentTarget && !loading) {
          handleClose()
        }
      }}>
        <div className="modal-content">
          <div className="modal-header">
            <h2>Delete Account</h2>
            <button
              className="modal-close"
              onClick={handleClose}
              disabled={loading}
              type="button"
            >
              ×
            </button>
          </div>
          <div className="modal-body">
            <div className="form-group">
              <label className="label">Select Account to Delete</label>
              <select
                className="input"
                value={selectedAccountId || ''}
                onChange={(e) => setSelectedAccountId(Number(e.target.value))}
                disabled={loading}
              >
                <option value="">-- Select an account --</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.email} ({account.provider}){!account.is_active ? ' - ⚠️ Needs Reconnection' : ''}
                  </option>
                ))}
              </select>
            </div>
            {selectedAccount && (
              <div style={{
                marginTop: '1rem',
                padding: '1rem',
                backgroundColor: '#fff3cd',
                border: '1px solid #ffc107',
                borderRadius: '4px',
                fontSize: '0.9rem',
                color: '#856404'
              }}>
                <strong>⚠️ Warning:</strong> Deleting this account will remove all associated email data and analysis results. This action cannot be undone.
              </div>
            )}
            <div className="modal-actions">
              <button
                onClick={handleClose}
                disabled={loading}
                type="button"
                className="btn"
                style={{
                  background: 'none',
                  border: '1px solid #ddd',
                  color: '#333',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontWeight: '500',
                  opacity: loading ? 0.6 : 1,
                }}
                onMouseEnter={(e) => {
                  if (!loading) {
                    e.currentTarget.style.backgroundColor = '#f8f9fa'
                    e.currentTarget.style.borderColor = '#bbb'
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                  e.currentTarget.style.borderColor = '#ddd'
                }}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={handleDeleteClick}
                disabled={!selectedAccountId || loading}
                type="button"
              >
                Delete Account
              </button>
            </div>
          </div>
        </div>
      </div>

      <ConfirmModal
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleConfirmDelete}
        title="Confirm Deletion"
        message={`Are you sure you want to delete ${selectedAccount?.email}? This action cannot be undone and will remove all associated email data and analysis results.`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmButtonStyle="danger"
        loading={loading}
      />
    </>
  )
}

