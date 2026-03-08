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

  if (!selectedAccount) {
    return null
  }

  const emails = account ? account.email_count.toLocaleString() : '0'
  const senders = account ? account.sender_count.toLocaleString() : '0'
  const ranges = account ? account.processed_ranges : 0

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '1rem',
    }}>
      <span style={{ fontWeight: '600', color: 'var(--color-gray-800)' }}>
        Email Summary
      </span>
      <div style={{
        display: 'flex',
        gap: '1.5rem',
        flexWrap: 'wrap',
      }}>
        <span style={{ color: 'var(--color-gray-600)' }}>
          <strong style={{ color: 'var(--color-accent)' }}>{emails}</strong> emails
        </span>
        <span style={{ color: 'var(--color-gray-600)' }}>
          <strong style={{ color: 'var(--color-accent)' }}>{senders}</strong> senders
        </span>
        <span style={{ color: 'var(--color-gray-600)' }}>
          <strong style={{ color: 'var(--color-accent)' }}>{ranges}</strong> processed ranges
        </span>
      </div>
    </div>
  )
}

