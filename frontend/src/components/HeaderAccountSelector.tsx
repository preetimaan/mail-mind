import { EmailAccount } from '../api/client'

interface HeaderAccountSelectorProps {
  accounts: EmailAccount[]
  selectedAccount: number | null
  onSelect: (accountId: number) => void
  username: string | null
}

export default function HeaderAccountSelector({ 
  accounts, 
  selectedAccount, 
  onSelect,
  username 
}: HeaderAccountSelectorProps) {
  if (!username) return null

  const selectedAccountData = selectedAccount 
    ? accounts.find(a => a.id === selectedAccount)
    : null

  return (
    <div className="header-account-selector">
      <span className="header-username">{username}</span>
      {accounts.length > 1 && (
        <>
          <span className="header-separator">•</span>
          <select
            className="header-account-select"
            value={selectedAccount || ""}
            onChange={(e) => onSelect(Number(e.target.value))}
          >
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.email} ({account.provider})
              </option>
            ))}
          </select>
        </>
      )}
    </div>
  )
}

