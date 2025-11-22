import { Summary } from '../api/client'

interface StatsGridProps {
  summary: Summary
  selectedAccount: number | null
}

export default function StatsGrid({ summary, selectedAccount }: StatsGridProps) {
  const account = selectedAccount
    ? summary.accounts.find((a) => a.id === selectedAccount)
    : null

  // Total stats (across all accounts)
  const totalStats = [
    {
      label: 'Total Accounts',
      value: summary.total_accounts,
    },
    {
      label: 'Total Emails (All Accounts)',
      value: summary.total_emails.toLocaleString(),
    },
    {
      label: 'Total Senders (All Accounts)',
      value: summary.total_senders.toLocaleString(),
    },
  ]

  // Current account stats (if account is selected)
  const accountStats = account
    ? [
        {
          label: 'Current Account Emails',
          value: account.email_count.toLocaleString(),
        },
        {
          label: 'Current Account Senders',
          value: account.sender_count.toLocaleString(),
        },
        {
          label: 'Processed Ranges',
          value: account.processed_ranges,
        },
      ]
    : []

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

      {account && (
        <div>
          <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: '600' }}>
            Current Account: {account.email}
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

