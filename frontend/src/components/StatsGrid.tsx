import { Summary, EmailAccount } from '../api/client'

interface StatsGridProps {
  summary: Summary | null
  selectedAccount: number | null
  accounts?: EmailAccount[]
}

export default function StatsGrid({ summary, selectedAccount, accounts = [] }: StatsGridProps) {
  // Default to 0 values if summary is null
  const safeSummary: Summary = summary || {
    total_accounts: 0,
    total_emails: 0,
    total_senders: 0,
    accounts: []
  }

  const account = selectedAccount
    ? safeSummary.accounts.find((a) => a.id === selectedAccount)
    : null

  // Get account email from accounts list if not in summary
  const accountFromList = selectedAccount
    ? accounts.find((a) => a.id === selectedAccount)
    : null

  // Total stats (across all accounts)
  const totalStats = [
    {
      label: 'Total Accounts',
      value: safeSummary.total_accounts,
    },
    {
      label: 'Total Emails (All Accounts)',
      value: safeSummary.total_emails.toLocaleString(),
    },
    {
      label: 'Total Senders (All Accounts)',
      value: safeSummary.total_senders.toLocaleString(),
    },
  ]

  // Current account stats (if account is selected)
  // Show stats even if account not found in summary (will show 0 values)
  const accountStats = selectedAccount
    ? [
        {
          label: 'Current Account Emails',
          value: account ? account.email_count.toLocaleString() : '0',
        },
        {
          label: 'Current Account Senders',
          value: account ? account.sender_count.toLocaleString() : '0',
        },
        {
          label: 'Processed Ranges',
          value: account ? account.processed_ranges : 0,
        },
      ]
    : []

  // Get account email for display (from summary, accounts list, or fallback)
  const accountEmail = account?.email || accountFromList?.email || (selectedAccount ? `Account #${selectedAccount}` : null)

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: '600' }}>All Accounts Summary</h2>
        <div className="grid">
          {totalStats.map((stat) => (
            <div key={stat.label} className="stat-card">
              <h3>{stat.label}</h3>
              <div className="value">{stat.value}</div>
            </div>
          ))}
        </div>
      </div>

      {selectedAccount && (
        <div>
          <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: '600' }}>
            Current Account: {accountEmail}
          </h2>
          <div className="grid">
            {accountStats.map((stat) => (
              <div key={stat.label} className="stat-card">
                <h3>{stat.label}</h3>
                <div className="value">{stat.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

