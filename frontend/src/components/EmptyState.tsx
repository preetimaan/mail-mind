import './EmptyState.css'

interface EmptyStateProps {
  title: string
  message: string
  icon?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export default function EmptyState({ title, message, icon, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-state-icon">{icon}</div>}
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-message">{message}</p>
      {action && (
        <button className="empty-state-action btn btn-primary" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  )
}

