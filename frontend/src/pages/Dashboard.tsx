import { useState, useEffect } from 'react'
import { api, EmailAccount, Summary, SenderInsights, CategoryInsights, FrequencyInsights, AnalysisRun } from '../api/client'
import DateRangePicker from '../components/DateRangePicker'
import AccountSelector from '../components/AccountSelector'
import StatsGrid from '../components/StatsGrid'
import SenderChart from '../components/SenderChart'
import CategoryChart from '../components/CategoryChart'
import FrequencyChart from '../components/FrequencyChart'
import YearlyFrequencyChart from '../components/YearlyFrequencyChart'
import ProcessedRanges from '../components/ProcessedRanges'
import AddAccountModal from '../components/AddAccountModal'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import './Dashboard.css'

export default function Dashboard() {
  const [usernameInput, setUsernameInput] = useState('')
  const [username, setUsername] = useState('') // Submitted username
  const [showAddAccountModal, setShowAddAccountModal] = useState(false)
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [senderInsights, setSenderInsights] = useState<SenderInsights | null>(null)
  const [categoryInsights, setCategoryInsights] = useState<CategoryInsights | null>(null)
  const [frequencyInsights, setFrequencyInsights] = useState<FrequencyInsights | null>(null)
  const [yearlyFrequencyInsights, setYearlyFrequencyInsights] = useState<any>(null)
  const [analysisRuns, setAnalysisRuns] = useState<AnalysisRun[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Load username from localStorage on mount
  useEffect(() => {
    const savedUsername = localStorage.getItem('mailmind_username')
    if (savedUsername) {
      setUsernameInput(savedUsername)
      setUsername(savedUsername)
    }
  }, [])

  // Handle OAuth callbacks from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const oauthSuccess = params.get('oauth_success')
    const oauthError = params.get('oauth_error')
    const oauthUsername = params.get('username')

    if (oauthSuccess === '1' && oauthUsername) {
      setSuccess('Gmail account added successfully!')
      setUsername(oauthUsername)
      setUsernameInput(oauthUsername)
      localStorage.setItem('mailmind_username', oauthUsername)
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname)
      // Reload accounts
      setTimeout(() => {
        loadAccounts()
      }, 500)
    } else if (oauthError) {
      setError(decodeURIComponent(oauthError))
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [])

  const handleUsernameSubmit = () => {
    const trimmed = usernameInput.trim()
    if (trimmed) {
      setUsername(trimmed)
      setSelectedAccount(null) // Reset selected account when username changes
      setError(null)
      setSuccess(null)
      // Save to localStorage
      localStorage.setItem('mailmind_username', trimmed)
    }
  }

  const handleUsernameKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleUsernameSubmit()
    }
  }

  useEffect(() => {
    if (username) {
      loadAccounts()
      loadSummary()
    }
  }, [username])

  useEffect(() => {
    if (username && selectedAccount) {
      loadInsights()
      loadAnalysisRuns()
    }
  }, [username, selectedAccount])

  const loadAccounts = async () => {
    if (!username) {
      console.log('loadAccounts: No username, skipping')
      return
    }
    
    try {
      setError(null) // Clear any previous errors
      console.log(`Loading accounts for username: ${username}`)
      const response = await api.get(`/api/emails/accounts?username=${username}`)
      setAccounts(response.data || [])
      if (response.data && response.data.length > 0 && !selectedAccount) {
        setSelectedAccount(response.data[0].id)
      }
    } catch (err: any) {
      console.error('Error loading accounts:', err)
      setAccounts([]) // Clear accounts on error
      // Don't show error if it's just "no accounts" - that's normal for new users
      if (err.response?.status === 404) {
        setError(null) // 404 is fine - just means no accounts yet
        setAccounts([]) // Ensure accounts is empty array
      } else {
        const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || err.message || 'Failed to load accounts'
        setError(`Failed to load accounts: ${errorMessage}`)
      }
    }
  }

  const handleAccountAdded = () => {
    loadAccounts()
    setSuccess('Account added successfully!')
  }

  const handleDeleteAccount = async (accountId: number) => {
    if (!username) return
    
    if (!window.confirm('Are you sure you want to delete this account? This action cannot be undone.')) {
      return
    }

    try {
      await api.delete(`/api/emails/accounts/${accountId}?username=${username}`)
      setSuccess('Account deleted successfully')
      loadAccounts()
      if (selectedAccount === accountId) {
        setSelectedAccount(null)
      }
    } catch (err: any) {
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || err.message || 'Failed to delete account'
      setError(`Failed to delete account: ${errorMessage}`)
    }
  }

  const loadSummary = async () => {
    if (!username) return
    
    try {
      const response = await api.get(`/api/insights/summary?username=${username}`)
      setSummary(response.data)
    } catch (err: any) {
      // Silently handle 404 - user might not exist yet
      if (err.response?.status === 404) {
        setSummary({
          total_accounts: 0,
          total_emails: 0,
          total_senders: 0,
          accounts: []
        })
      } else {
        console.error('Failed to load summary:', err)
      }
    }
  }

  const loadInsights = async () => {
    if (!selectedAccount) return
    
    try {
      const [senders, categories, frequency, yearlyFrequency] = await Promise.all([
        api.get(`/api/insights/senders?username=${username}&account_id=${selectedAccount}`),
        api.get(`/api/insights/categories?username=${username}&account_id=${selectedAccount}`),
        api.get(`/api/insights/frequency?username=${username}&account_id=${selectedAccount}`),
        api.get(`/api/insights/frequency/yearly?username=${username}&account_id=${selectedAccount}`).catch(() => ({ data: null }))
      ])
      
      setSenderInsights(senders.data)
      setCategoryInsights(categories.data)
      setFrequencyInsights(frequency.data)
      if (yearlyFrequency && yearlyFrequency.data && yearlyFrequency.data.years && yearlyFrequency.data.years.length > 0) {
        setYearlyFrequencyInsights(yearlyFrequency.data)
      } else {
        setYearlyFrequencyInsights(null)
      }
    } catch (err: any) {
      console.error('Failed to load insights:', err)
    }
  }

  const loadAnalysisRuns = async () => {
    if (!selectedAccount) return
    
    try {
      const response = await api.get(`/api/analysis/runs?username=${username}&account_id=${selectedAccount}`)
      setAnalysisRuns(response.data)
    } catch (err: any) {
      console.error('Failed to load analysis runs:', err)
    }
  }

  const handleAnalyze = async (startDate: Date, endDate: Date) => {
    if (!selectedAccount || !username) {
      setError('Please select an account')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await api.post('/api/analysis/batch', {
        username,
        account_id: selectedAccount,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      })

      setSuccess(`Analysis started! Run ID: ${response.data.run_id}`)
      
      // Poll for completion
      const runId = response.data.run_id
      const pollInterval = setInterval(async () => {
        try {
          const runResponse = await api.get(`/api/analysis/runs/${runId}?username=${username}`)
          const run = runResponse.data
          
          if (run.status === 'completed' || run.status === 'failed') {
            clearInterval(pollInterval)
            setLoading(false)
            if (run.status === 'completed') {
              setSuccess(`Analysis completed! Processed ${run.emails_processed} emails.`)
              loadInsights()
              loadSummary()
              loadAnalysisRuns()
            } else {
              setError('Analysis failed')
            }
          }
        } catch (err) {
          clearInterval(pollInterval)
          setLoading(false)
          setError('Failed to check analysis status')
        }
      }, 2000)
    } catch (err: any) {
      setLoading(false)
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to start analysis'
      setError(errorMessage)
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Mail Mind</h1>
        <p>Email Analysis and Classifier Tool</p>
      </header>

      <div className="container">
        <div className="card">
          <div className="form-group">
            <label className="label">Username</label>
            <div className="username-form">
              <input
                type="text"
                className="input username-input"
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                onKeyPress={handleUsernameKeyPress}
                placeholder="Enter your username"
              />
              <button
                onClick={handleUsernameSubmit}
                className="submit-button"
                disabled={!usernameInput.trim()}
              >
                Load
              </button>
            </div>
          </div>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}

        {username && (
          <>
            <AccountSelector
              accounts={accounts}
              selectedAccount={selectedAccount}
              onSelect={setSelectedAccount}
              onAddAccount={() => setShowAddAccountModal(true)}
              onDeleteAccount={handleDeleteAccount}
            />

            <AddAccountModal
              isOpen={showAddAccountModal}
              onClose={() => setShowAddAccountModal(false)}
              username={username}
              onAccountAdded={handleAccountAdded}
            />

            {summary && (
              <StatsGrid summary={summary} selectedAccount={selectedAccount} />
            )}

            {selectedAccount && (
              <>
                <div className="card">
                  <h2>Batch Analysis</h2>
                  {loading && (
                    <div style={{ marginBottom: '1rem' }}>
                      <LoadingSpinner message="Processing emails..." size="small" />
                    </div>
                  )}
                  <DateRangePicker
                    onAnalyze={handleAnalyze}
                    loading={loading}
                    disabled={loading}
                  />
                </div>

                <ProcessedRanges
                  username={username}
                  accountId={selectedAccount}
                />

                {analysisRuns.length > 0 ? (
                  <div className="card">
                    <h2>Recent Analysis Runs</h2>
                    <div className="runs-list">
                      {analysisRuns.slice(0, 5).map((run) => (
                        <div key={run.id} className="run-item">
                          <div>
                            <strong>{new Date(run.start_date).toLocaleDateString()}</strong> -{' '}
                            {new Date(run.end_date).toLocaleDateString()}
                          </div>
                          <div className="run-status">
                            <span className={`status-badge status-${run.status}`}>
                              {run.status}
                            </span>
                            {run.emails_processed > 0 && (
                              <span>{run.emails_processed} emails</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="card">
                    <h2>Recent Analysis Runs</h2>
                    <EmptyState
                      title="No analysis runs yet"
                      message="Start your first analysis to see results here."
                      icon="🔍"
                    />
                  </div>
                )}

                {senderInsights ? (
                  senderInsights.total_emails > 0 ? (
                    <div className="card">
                      <h2>Top Senders</h2>
                      <SenderChart insights={senderInsights} />
                    </div>
                  ) : (
                    <div className="card">
                      <h2>Top Senders</h2>
                      <EmptyState
                        title="No email data yet"
                        message="Run an analysis to see your top senders and email patterns."
                        icon="📧"
                      />
                    </div>
                  )
                ) : null}

                {categoryInsights ? (
                  categoryInsights.total > 0 ? (
                    <div className="card">
                      <h2>Email Categories</h2>
                      <CategoryChart insights={categoryInsights} />
                    </div>
                  ) : (
                    <div className="card">
                      <h2>Email Categories</h2>
                      <EmptyState
                        title="No categories yet"
                        message="Analyze your emails to see how they're categorized."
                        icon="📊"
                      />
                    </div>
                  )
                ) : null}

                {frequencyInsights ? (
                  frequencyInsights.total_emails > 0 ? (
                    <>
                      <div className="card">
                        <h2>Email Frequency</h2>
                        <FrequencyChart insights={frequencyInsights} />
                      </div>
                      {yearlyFrequencyInsights && yearlyFrequencyInsights.years && yearlyFrequencyInsights.years.length > 0 && (
                        <div className="card">
                          <h2>Yearly Frequency Analysis</h2>
                          <YearlyFrequencyChart insights={yearlyFrequencyInsights} />
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="card">
                      <h2>Email Frequency</h2>
                      <EmptyState
                        title="No frequency data yet"
                        message="Run an analysis to see your email frequency patterns."
                        icon="⏰"
                      />
                    </div>
                  )
                ) : null}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

