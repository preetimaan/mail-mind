import HeaderAccountSelector from './HeaderAccountSelector'
import { EmailAccount } from '../api/client'

interface DashboardHeaderProps {
  username: string | null
  onLogout: () => void
  accounts: EmailAccount[]
  selectedAccount: number | null
  onSelectAccount: (accountId: number) => void
  onReload?: () => void
  reloading?: boolean
}

export default function DashboardHeader({ 
  username, 
  onLogout,
  accounts,
  selectedAccount,
  onSelectAccount,
  onReload,
  reloading = false
}: DashboardHeaderProps) {
  return (
    <header className="dashboard-header">
      <div className="header-content">
        <div className="header-title">
          <h1>Mail Mind</h1>
        </div>
        {username && (
          <div className="user-info">
            <HeaderAccountSelector
              accounts={accounts}
              selectedAccount={selectedAccount}
              onSelect={onSelectAccount}
              username={username}
            />
            {onReload && (
              <button 
                onClick={onReload} 
                className="reload-button"
                title="Reload user data"
                disabled={reloading}
              >
                ↻
              </button>
            )}
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

