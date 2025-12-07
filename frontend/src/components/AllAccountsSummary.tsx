import { Summary } from '../api/client'

interface AllAccountsSummaryProps {
  summary: Summary | null
}

export default function AllAccountsSummary({ summary }: AllAccountsSummaryProps) {
  // Default to 0 values if summary is null
  const safeSummary: Summary = summary || {
    total_accounts: 0,
    total_emails: 0,
    total_senders: 0,
    accounts: []
  }

  // Total stats (across all accounts)
  const totalStats = [
    {
      label: 'Total Email Accounts',
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

  return (
    <div>
      <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: '600' }}>Account Summary</h2>
      <div className="grid">
        {totalStats.map((stat) => (
          <div key={stat.label} className="stat-card">
            <h3>{stat.label}</h3>
            <div className="value">{stat.value}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

