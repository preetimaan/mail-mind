interface DashboardHeaderProps {
  username: string | null
  onLogout: () => void
}

export default function DashboardHeader({ username, onLogout }: DashboardHeaderProps) {
  return (
    <header className="dashboard-header">
      <div className="header-content">
        <div>
          <h1>Mail Mind</h1>
          <p>Email Analysis and Classifier Tool</p>
        </div>
        {username && (
          <div className="user-info">
            <span className="current-user">Logged in as: <strong>{username}</strong></span>
            <button 
              onClick={onLogout} 
              className="logout-button"
              title="Log out"
            >
              Log Out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}

