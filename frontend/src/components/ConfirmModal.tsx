import './AddAccountModal.css'

interface ConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmButtonStyle?: 'primary' | 'danger'
  loading?: boolean
}

export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmButtonStyle = 'primary',
  loading = false,
}: ConfirmModalProps) {
  if (!isOpen) return null

  const handleConfirm = () => {
    onConfirm()
  }

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !loading) {
      onClose()
    }
  }

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-content">
        <div className="modal-header">
          <h2>{title}</h2>
          <button
            className="modal-close"
            onClick={onClose}
            disabled={loading}
            type="button"
          >
            ×
          </button>
        </div>
        <div className="modal-body">
          <p style={{ margin: 0, fontSize: '1rem', lineHeight: '1.5', color: '#333' }}>
            {message}
          </p>
          <div className="modal-actions">
            <button
              onClick={onClose}
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
              {cancelText}
            </button>
            <button
              className={`btn ${confirmButtonStyle === 'danger' ? 'btn-danger' : 'btn-primary'}`}
              onClick={handleConfirm}
              disabled={loading}
              type="button"
            >
              {loading ? 'Processing...' : confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

