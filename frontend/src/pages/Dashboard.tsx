import { useState, useEffect } from 'react'
import { api, EmailAccount, AnalysisRun } from '../api/client'
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
import AnalysisRunsList from '../components/AnalysisRunsList'
import DashboardHeader from '../components/DashboardHeader'
import UsernameForm from '../components/UsernameForm'
import { useUsername } from '../hooks/useUsername'
import { useOAuthCallback } from '../hooks/useOAuthCallback'
import { useAccounts } from '../hooks/useAccounts'
import { useInsights } from '../hooks/useInsights'
import { useAnalysisPolling } from '../hooks/useAnalysisPolling'
import './Dashboard.css'

export default function Dashboard() {
  const [showAddAccountModal, setShowAddAccountModal] = useState(false)
  const [analysisRuns, setAnalysisRuns] = useState<AnalysisRun[]>([])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [processedRangesRefresh, setProcessedRangesRefresh] = useState(0)
  const [selectedGapStart, setSelectedGapStart] = useState<Date | undefined>()
  const [selectedGapEnd, setSelectedGapEnd] = useState<Date | undefined>()

  const {
    usernameInput,
    setUsernameInput,
    username,
    setUsername,
    handleUsernameSubmit,
    handleUsernameKeyPress,
    handleLogout,
  } = useUsername()

  const {
    accounts,
    selectedAccount,
    setSelectedAccount,
    error: accountsError,
    loadAccounts,
    handleAccountAdded,
    handleDeleteAccount,
  } = useAccounts(username)

  const {
    summary,
    senderInsights,
    categoryInsights,
    frequencyInsights,
    yearlyFrequencyInsights,
    loadSummary,
    loadInsights,
  } = useInsights(username, selectedAccount)

  const {
    loading,
    setLoading,
    pollAnalysisRun,
  } = useAnalysisPolling({
    username,
    selectedAccount,
    onComplete: () => {
      loadInsights()
      loadSummary()
      loadAnalysisRuns()
      setProcessedRangesRefresh(prev => prev + 1)
    },
    onError: (errorMsg) => {
      setError(errorMsg)
    },
    onSuccess: (message) => {
      setSuccess(message)
    },
    checkAccountStatus: async (accountId) => {
      try {
        const accountsResponse = await api.get(`/api/emails/accounts?username=${username}`)
        const updatedAccounts = accountsResponse.data || []
        const account = updatedAccounts.find((a: EmailAccount) => a.id === accountId)
        return account?.is_active ?? true
      } catch {
        return true
      }
    },
  })

  // Handle OAuth callbacks
  useOAuthCallback({
    onSuccess: (oauthUsername) => {
      setSuccess('Gmail account added successfully!')
      setUsername(oauthUsername)
      setUsernameInput(oauthUsername)
      localStorage.setItem('mailmind_username', oauthUsername)
      setTimeout(() => {
        loadAccounts()
      }, 500)
    },
    onError: (errorMsg) => {
      setError(errorMsg)
    },
  })

  // Clear error/success when username changes, but don't reset selectedAccount
  // (useAccounts hook will handle account selection)
  useEffect(() => {
    if (username) {
      setError(null)
      setSuccess(null)
    }
  }, [username])

  // Load analysis runs when account is selected
  useEffect(() => {
    if (username && selectedAccount) {
      loadAnalysisRuns()
    } else {
      setAnalysisRuns([])
    }
  }, [username, selectedAccount])

  const loadAnalysisRuns = async () => {
    if (!selectedAccount || !username) {
      setAnalysisRuns([])
      return
    }
    
    try {
      const response = await api.get(`/api/analysis/runs?username=${username}&account_id=${selectedAccount}`)
      setAnalysisRuns(response.data)
    } catch (err: any) {
      console.error('Failed to load analysis runs:', err)
    }
  }

  const handleRetryAnalysis = async (runId: number) => {
    if (!username) {
      setError('Please enter a username')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await api.post(`/api/analysis/runs/${runId}/retry?username=${username}`)
      setSuccess(`Analysis retry started! Run ID: ${response.data.run_id}`)
      
      loadAnalysisRuns()
      
      const newRunId = response.data.run_id
      await pollAnalysisRun(newRunId)
    } catch (err: any) {
      setLoading(false)
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to retry analysis'
      setError(errorMessage)
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
      
      const runId = response.data.run_id
      await pollAnalysisRun(runId)
    } catch (err: any) {
      setLoading(false)
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to start analysis'
      setError(errorMessage)
    }
  }

  const handleAccountAddedWithSuccess = () => {
    handleAccountAdded()
    setSuccess('Account added successfully!')
  }

  const handleGapSelect = (startDate: Date, endDate: Date) => {
    setSelectedGapStart(startDate)
    setSelectedGapEnd(endDate)
    setSuccess(`Gap selected: ${startDate.toLocaleDateString()} to ${endDate.toLocaleDateString()}. Dates filled in above - click "Analyze" to process this gap.`)
    setTimeout(() => {
      const datePicker = document.querySelector('.card h2')?.parentElement
      if (datePicker) {
        datePicker.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 100)
  }

  return (
    <div className="dashboard">
      <DashboardHeader username={username} onLogout={handleLogout} />

      <div className="container">
        {error && !username && <div className="error" style={{ marginBottom: '1rem' }}>{error}</div>}
        <UsernameForm
          usernameInput={usernameInput}
          onUsernameInputChange={setUsernameInput}
          onUsernameSubmit={handleUsernameSubmit}
          onUsernameKeyPress={handleUsernameKeyPress}
        />

        {username && (
          <>
            {accountsError && <div className="error" style={{ marginTop: '1rem' }}>{accountsError}</div>}
            <AccountSelector
              accounts={accounts}
              selectedAccount={selectedAccount}
              onSelect={setSelectedAccount}
              onAddAccount={() => setShowAddAccountModal(true)}
              onDeleteAccount={handleDeleteAccount}
              onReconnectAccount={(accountId) => {
                setSelectedAccount(accountId)
                setShowAddAccountModal(true)
              }}
            />

            <AddAccountModal
              isOpen={showAddAccountModal}
              onClose={() => setShowAddAccountModal(false)}
              username={username}
              onAccountAdded={handleAccountAddedWithSuccess}
              reconnectAccount={selectedAccount && accounts.find(a => a.id === selectedAccount && !a.is_active) ? {
                email: accounts.find(a => a.id === selectedAccount)!.email,
                provider: accounts.find(a => a.id === selectedAccount)!.provider
              } : undefined}
            />

            {summary && (
              <StatsGrid summary={summary} selectedAccount={selectedAccount} />
            )}

            {accounts.length > 0 && !selectedAccount && (
              <div className="card" style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: '#fff3cd', border: '1px solid #ffc107' }}>
                <p style={{ margin: 0, fontSize: '1rem' }}>
                  <strong>Please select an account</strong> from the dropdown above to view insights and start analyzing emails.
                </p>
              </div>
            )}

            {selectedAccount ? (
              <>
                {(error || success) && (
                  <div style={{ marginTop: '1rem' }}>
                    {error && <div className="error">{error}</div>}
                    {success && <div className="success">{success}</div>}
                  </div>
                )}
                <div className="card" style={{ marginTop: '2rem' }}>
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
                    initialStartDate={selectedGapStart}
                    initialEndDate={selectedGapEnd}
                  />
                </div>

                <ProcessedRanges
                  username={username}
                  accountId={selectedAccount}
                  refreshTrigger={processedRangesRefresh}
                  onSelectGap={handleGapSelect}
                />

                <div className="card">
                  <h2>Recent Analysis Runs</h2>
                  <AnalysisRunsList
                    runs={analysisRuns}
                    loading={loading}
                    onRetry={handleRetryAnalysis}
                  />
                </div>

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
            ) : null}
          </>
        )}
      </div>
    </div>
  )
}
