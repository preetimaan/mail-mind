import { EmailAccount } from '../api/client'

interface AccountSelectorProps {
  accounts: EmailAccount[]
  selectedAccount: number | null
  onSelect: (accountId: number) => void
}

export default function AccountSelector({ accounts, selectedAccount, onSelect }: AccountSelectorProps) {
  if (accounts.length === 0) {
    return (
      <div className="card">
        <h2>Email Accounts</h2>
        <p>No email accounts configured for this username.</p>
        <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#666' }}>
          To add an account, use the API or see <code>ACCOUNT_SETUP.md</code> for instructions.
        </p>
        <div style={{ marginTop: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
          <strong>Quick start:</strong>
          <pre style={{ marginTop: '0.5rem', fontSize: '0.85rem', overflow: 'auto' }}>
{`cd backend
python3 add_gmail_account.py`}
          </pre>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <h2>Email Accounts</h2>
      <div className="form-group">
        <label className="label">Select Account</label>
        <select
          className="input"
          value={selectedAccount || ''}
          onChange={(e) => onSelect(Number(e.target.value))}
        >
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.email} ({account.provider})
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

