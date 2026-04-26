import { useEffect, useMemo, useState } from 'react'
import { api, type EmailAccount } from '../api/client'

type Tab = 'analysis' | 'insights' | 'settings'

const TAB_LABELS: Record<Tab, string> = {
  analysis: 'Analyze',
  insights: 'Insights',
  settings: 'Settings',
}

export default function App() {
  const [username, setUsername] = useState('')
  const [loggedIn, setLoggedIn] = useState(false)
  const [tab, setTab] = useState<Tab>('analysis')

  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null)

  const canUseAccount = useMemo(() => loggedIn && accounts.length > 0, [loggedIn, accounts.length])

  useEffect(() => {
    const saved = localStorage.getItem('mailmind_username') ?? ''
    if (saved.trim().length > 0) {
      setUsername(saved)
      setLoggedIn(true)
    }
  }, [])

  useEffect(() => {
    if (!loggedIn) return
    void (async () => {
      const data = await api.listAccounts(username)
      setAccounts(data)
      if (data.length > 0 && selectedAccountId === null) setSelectedAccountId(data[0].id)
    })()
  }, [loggedIn, username])

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Arial', padding: '1.5rem', maxWidth: 1000, margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <h1 style={{ margin: 0 }}>Mail Mind</h1>
        {loggedIn ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 600 }}>{username}</span>
            <button
              onClick={() => {
                localStorage.removeItem('mailmind_username')
                setLoggedIn(false)
                setUsername('')
                setAccounts([])
                setSelectedAccountId(null)
              }}
            >
              Log out
            </button>
          </div>
        ) : null}
      </header>

      {!loggedIn ? (
        <div style={{ marginTop: '1.5rem', border: '1px solid #e5e7eb', borderRadius: 12, padding: '1rem' }}>
          <h2 style={{ marginTop: 0 }}>Login</h2>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="username"
              style={{ flex: 1, padding: '0.5rem 0.75rem' }}
            />
            <button
              onClick={() => {
                const u = username.trim()
                if (u.length === 0) return
                localStorage.setItem('mailmind_username', u)
                setUsername(u)
                setLoggedIn(true)
              }}
              disabled={username.trim().length === 0}
            >
              Continue
            </button>
          </div>
        </div>
      ) : (
        <>
          <nav style={{ display: 'flex', gap: 8, marginTop: '1.25rem' }}>
            {(['analysis', 'insights', 'settings'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: 10,
                  border: '1px solid #e5e7eb',
                  background: tab === t ? '#111827' : 'white',
                  color: tab === t ? 'white' : '#111827',
                  cursor: 'pointer',
                }}
              >
                {TAB_LABELS[t]}
              </button>
            ))}
          </nav>

          <section style={{ marginTop: '1.25rem', border: '1px solid #e5e7eb', borderRadius: 12, padding: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
              <h2 style={{ margin: 0 }}>{TAB_LABELS[tab]}</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <label style={{ fontSize: 14, color: '#374151' }}>Account</label>
                <select
                  value={selectedAccountId ?? ''}
                  onChange={(e) => setSelectedAccountId(Number(e.target.value))}
                  disabled={!canUseAccount}
                >
                  <option value="" disabled>
                    {accounts.length === 0 ? 'No accounts' : 'Select'}
                  </option>
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.provider} • {a.email}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {tab === 'settings' ? (
              <Settings username={username} onAccountsChange={(a) => { setAccounts(a); if (a.length === 0) setSelectedAccountId(null) }} />
            ) : (
              <div style={{ marginTop: 12, color: '#6b7280' }}>
                Stub UI. Next: wire analysis runs + insights.
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}

function Settings({
  username,
  onAccountsChange,
}: {
  username: string
  onAccountsChange: (accounts: EmailAccount[]) => void
}) {
  const [provider, setProvider] = useState<'gmail' | 'yahoo'>('gmail')
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = async () => {
    const data = await api.listAccounts(username)
    onAccountsChange(data)
  }

  useEffect(() => {
    void refresh()
  }, [])

  return (
    <div style={{ marginTop: 12 }}>
      <h3 style={{ margin: '0 0 0.5rem 0' }}>Account Management</h3>
      {error ? <div style={{ color: '#b91c1c', marginBottom: 8 }}>{error}</div> : null}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <select value={provider} onChange={(e) => setProvider(e.target.value as any)}>
          <option value="gmail">gmail</option>
          <option value="yahoo">yahoo</option>
        </select>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          style={{ flex: 1, minWidth: 240, padding: '0.5rem 0.75rem' }}
        />
        <button
          disabled={busy || email.trim().length === 0}
          onClick={async () => {
            setBusy(true)
            setError(null)
            try {
              await api.createAccount({ username, provider, email })
              setEmail('')
              await refresh()
            } catch (e: any) {
              setError(e?.message ?? 'Failed')
            } finally {
              setBusy(false)
            }
          }}
        >
          Add account
        </button>
      </div>
    </div>
  )
}

