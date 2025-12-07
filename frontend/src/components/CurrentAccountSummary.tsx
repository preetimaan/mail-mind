import { Summary, EmailAccount } from '../api/client'

interface CurrentAccountSummaryProps {
  summary: Summary | null
  selectedAccount: number | null
  accounts?: EmailAccount[]
}

export default function CurrentAccountSummary({ summary, selectedAccount, accounts = [] }: CurrentAccountSummaryProps) {
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

  // Current account stats (if account is selected)
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

  if (!selectedAccount) {
    return null
  }

  return (
    <div>
      <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: '600' }}>
        Current Email Summary
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
  )
}

