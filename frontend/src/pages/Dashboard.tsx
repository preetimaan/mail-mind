import { useState, useEffect } from 'react'
import { api, EmailAccount, AnalysisRun } from '../api/client'
import DashboardHeader from '../components/DashboardHeader'
import DateRangePicker from '../components/DateRangePicker'
import AccountSelector from '../components/AccountSelector'
import CurrentAccountSummary from '../components/CurrentAccountSummary'
import AllAccountsSummary from '../components/AllAccountsSummary'
import SenderChart from '../components/SenderChart'
import CategoryChart from '../components/CategoryChart'
import FrequencyChart from '../components/FrequencyChart'
import YearlyFrequencyChart from '../components/YearlyFrequencyChart'
import ProcessedRanges from '../components/ProcessedRanges'
import AddAccountModal from '../components/AddAccountModal'
import LoadingSpinner from '../components/LoadingSpinner'
import AnalysisProgress from '../components/AnalysisProgress'
import EmptyState from '../components/EmptyState'
import AnalysisRunsList from '../components/AnalysisRunsList'
import Tabs, { TabType } from '../components/Tabs'
import UsernameForm from '../components/UsernameForm'
import { useUsername } from '../hooks/useUsername'
import { useOAuthCallback } from '../hooks/useOAuthCallback'
import { useAccounts } from '../hooks/useAccounts'
import { useInsights } from '../hooks/useInsights'
import { useAnalysisPolling } from '../hooks/useAnalysisPolling'
import './Dashboard.css'

export default function Dashboard() {
  // Check localStorage to determine initial tab
  const hasSavedUsername = typeof window !== 'undefined' && localStorage.getItem('mailmind_username')
  const [currentTab, setCurrentTab] = useState<TabType>(hasSavedUsername ? 'analysis' : 'settings')
  const [showAddAccountModal, setShowAddAccountModal] = useState(false)
  const [analysisRuns, setAnalysisRuns] = useState<AnalysisRun[]>([])
  const [analysisRunsOffset, setAnalysisRunsOffset] = useState(0)
  const [hasMoreRuns, setHasMoreRuns] = useState(false)
  const [loadingMoreRuns, setLoadingMoreRuns] = useState(false)
  const [currentRunningRunId, setCurrentRunningRunId] = useState<number | null>(null)
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
    loading: accountsLoading,
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
    progress,
  } = useAnalysisPolling({
    username,
    selectedAccount,
    onComplete: () => {
      // Clear running run ID
      setCurrentRunningRunId(null)
      // Add a small delay to ensure database transaction is committed
      setTimeout(() => {
        loadSummary()
        loadInsights()
        loadAnalysisRuns(true)
        setProcessedRangesRefresh(prev => prev + 1)
      }, 500) // 500ms delay to allow database to commit
    },
    onError: (errorMsg) => {
      setError(errorMsg)
    },
    onSuccess: (message) => {
      setSuccess(message)
    },
    checkAccountStatus: async (accountId) => {
      try {
        const accountsResponse = await api.get(`/api/emails/accounts?username=${username}`, {
          timeout: 60000, // 60 seconds timeout
        })
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
      loadAnalysisRuns(true)
    } else {
      setAnalysisRuns([])
      setAnalysisRunsOffset(0)
      setHasMoreRuns(false)
      setCurrentRunningRunId(null)
    }
  }, [username, selectedAccount])

  // Check for running analysis when runs are loaded
  useEffect(() => {
    const runningRun = analysisRuns.find(run => run.status === 'pending' || run.status === 'processing')
    if (runningRun) {
      setCurrentRunningRunId(currentId => {
        // Only update if we don't already have a running run, or if the current one is no longer running
        if (!currentId || !analysisRuns.find(r => r.id === currentId && (r.status === 'pending' || r.status === 'processing'))) {
          return runningRun.id
        }
        return currentId
      })
    } else {
      // Clear if no running runs found
      setCurrentRunningRunId(null)
    }
  }, [analysisRuns])

  const loadAnalysisRuns = async (reset: boolean = false) => {
    if (!selectedAccount || !username) {
      setAnalysisRuns([])
      setAnalysisRunsOffset(0)
      setHasMoreRuns(false)
      return
    }
    
    const offset = reset ? 0 : analysisRunsOffset
    const limit = 5
    
    try {
      const response = await api.get(`/api/analysis/runs?username=${username}&account_id=${selectedAccount}&limit=${limit}&offset=${offset}`)
      const data = response.data
      
      if (reset) {
        setAnalysisRuns(data.runs || [])
        setAnalysisRunsOffset(limit)
      } else {
        setAnalysisRuns(prev => [...prev, ...(data.runs || [])])
        setAnalysisRunsOffset(prev => prev + limit)
      }
      setHasMoreRuns(data.has_more || false)
    } catch (err: any) {
      console.error('Failed to load analysis runs:', err)
    }
  }

  const loadMoreRuns = async () => {
    if (loadingMoreRuns || !hasMoreRuns) return
    
    setLoadingMoreRuns(true)
    try {
      await loadAnalysisRuns(false)
    } finally {
      setLoadingMoreRuns(false)
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
      
      loadAnalysisRuns(true)
      
      const newRunId = response.data.run_id
      await pollAnalysisRun(newRunId)
    } catch (err: any) {
      setLoading(false)
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to retry analysis'
      setError(errorMessage)
    }
  }

  const handleStopAnalysis = async () => {
    if (!username || !currentRunningRunId) {
      setError('No analysis running')
      return
    }

    setError(null)
    setSuccess(null)

    try {
      const response = await api.post(`/api/analysis/runs/${currentRunningRunId}/stop?username=${username}`)
      setSuccess(response.data.message || 'Analysis stopped successfully')
      
      setCurrentRunningRunId(null)
      setLoading(false)
      
      // Reload analysis runs to show updated status
      loadAnalysisRuns(true)
      
      // Refresh insights and summary
      setTimeout(() => {
        loadSummary()
        loadInsights()
        setProcessedRangesRefresh(prev => prev + 1)
      }, 500)
    } catch (err: any) {
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to stop analysis'
      setError(errorMessage)
    }
  }

  const handleAnalyze = async (startDate: Date, endDate: Date, forceReanalysis: boolean = false) => {
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
        force_reanalysis: forceReanalysis,
      }, {
        timeout: 60000, // 60 seconds for analysis start request
      })

      setSuccess(`Analysis started! Run ID: ${response.data.run_id}${forceReanalysis ? ' (re-analyzing existing ranges)' : ''}`)
      
      const runId = response.data.run_id
      setCurrentRunningRunId(runId)
      // Reload runs to show the new one
      loadAnalysisRuns(true)
      await pollAnalysisRun(runId)
      // Clear running run ID after completion
      setCurrentRunningRunId(null)
    } catch (err: any) {
      setLoading(false)
      setCurrentRunningRunId(null)
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

  // Auto-switch to settings tab only if no username (after load) or no accounts
  useEffect(() => {
    // Only switch to settings if there's truly no username (check after a brief delay to allow localStorage load)
    if (!username) {
      const savedUsername = localStorage.getItem('mailmind_username')
      if (!savedUsername) {
        setCurrentTab('settings')
      }
    } else if (username && accounts.length === 0 && currentTab !== 'settings') {
      // Switch to settings if logged in but no accounts
      setCurrentTab('settings')
    }
  }, [username, accounts.length])

  return (
    <div className="dashboard">
      <DashboardHeader
        username={username}
        onLogout={handleLogout}
        accounts={accounts}
        selectedAccount={selectedAccount}
        onSelectAccount={setSelectedAccount}
        onReload={() => {
          if (username) {
            loadAccounts()
            if (selectedAccount) {
              loadSummary()
              loadInsights()
            }
          }
        }}
        reloading={accountsLoading}
      />

      <div className="container">
        {username && (
          <>
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

            {/* Current Account Summary - always visible above tabs */}
            {selectedAccount && (
              <div className="card" style={{ marginTop: '0.75rem' }}>
                <CurrentAccountSummary summary={summary} selectedAccount={selectedAccount} accounts={accounts} />
              </div>
            )}
          </>
        )}

        {/* Tabs - always visible so users can access Settings */}
        <Tabs
          currentTab={currentTab}
          onTabChange={setCurrentTab}
          hasAccounts={accounts.length > 0}
        />

        {/* Tab-specific content */}
        {username && (
          <>
            {currentTab === 'analysis' && selectedAccount && (
              <>


                {(error || success) && (
                  <div style={{ marginTop: '1rem' }}>
                    {error && <div className="error">{error}</div>}
                    {success && <div className="success">{success}</div>}
                  </div>
                )}
                <div className="card" style={{ marginTop: '1.5rem' }}>
                  <h2>Batch Analysis</h2>
                  {loading && progress && (
                    <div style={{ marginBottom: '1rem' }}>
                      <AnalysisProgress 
                        emailsProcessed={progress.emailsProcessed}
                        totalEmails={progress.totalEmails}
                        status={progress.status as 'processing' | 'completed' | 'failed'}
                      />
                    </div>
                  )}
                  {loading && !progress && (
                    <div style={{ marginBottom: '1rem' }}>
                      <LoadingSpinner message="Starting analysis..." size="small" />
                    </div>
                  )}
                  <DateRangePicker
                    onAnalyze={handleAnalyze}
                    onStop={handleStopAnalysis}
                    loading={loading}
                    disabled={loading}
                    hasRunningAnalysis={currentRunningRunId !== null}
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

                <div className="card" style={{ marginTop: '1.5rem' }}>
                  <h2>Recent Analysis Runs</h2>
                  <AnalysisRunsList
                    runs={analysisRuns}
                    loading={loading}
                    onRetry={handleRetryAnalysis}
                  />
                  {hasMoreRuns && (
                    <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                      <button
                        onClick={loadMoreRuns}
                        className="button"
                        disabled={loadingMoreRuns}
                        style={{
                          padding: '0.75rem 1.5rem',
                          fontSize: '0.9rem'
                        }}
                      >
                        {loadingMoreRuns ? 'Loading...' : 'Load More (5 previous runs)'}
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}

            {currentTab === 'analysis' && !selectedAccount && accounts.length > 0 && (
              <div className="card" style={{ marginTop: '1.5rem', padding: '1.5rem', backgroundColor: '#fff3cd', border: '1px solid #ffc107' }}>
                <p style={{ margin: 0, fontSize: '1rem' }}>
                  <strong>Please select an account</strong> from the header above to run analysis.
                </p>
              </div>
            )}

            {currentTab === 'insights' && selectedAccount && (
              <>
                {senderInsights ? (
                  senderInsights.total_emails > 0 ? (
                    <div className="card" style={{ marginTop: '1.5rem' }}>
                      <h2>Top Senders</h2>
                      <SenderChart insights={senderInsights} username={username || ''} accountId={selectedAccount || 0} />
                    </div>
                  ) : (
                    <div className="card" style={{ marginTop: '1.5rem' }}>
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
                    <div className="card" style={{ marginTop: '1.5rem' }}>
                      <h2>Email Categories</h2>
                      <CategoryChart insights={categoryInsights} />
                    </div>
                  ) : (
                    <div className="card" style={{ marginTop: '1.5rem' }}>
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
                      <div className="card" style={{ marginTop: '1.5rem' }}>
                        <h2>Email Frequency</h2>
                        <FrequencyChart insights={frequencyInsights} />
                      </div>
                      {yearlyFrequencyInsights && yearlyFrequencyInsights.years && yearlyFrequencyInsights.years.length > 0 && (
                        <div className="card" style={{ marginTop: '1.5rem' }}>
                          <h2>Yearly Frequency Analysis</h2>
                          <YearlyFrequencyChart insights={yearlyFrequencyInsights} />
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="card" style={{ marginTop: '1.5rem' }}>
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

            {currentTab === 'insights' && !selectedAccount && accounts.length > 0 && (
              <div className="card" style={{ marginTop: '1.5rem', padding: '1.5rem', backgroundColor: '#fff3cd', border: '1px solid #ffc107' }}>
                <p style={{ margin: 0, fontSize: '1rem' }}>
                  <strong>Please select an account</strong> from the header above to view insights.
                </p>
              </div>
            )}

          </>
        )}

        {/* Settings tab - accessible without username for login */}
        {currentTab === 'settings' && (
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <h2>Settings</h2>
            
            {!username && (
              <>
                <h3 style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>Login</h3>
                {error && <div className="error" style={{ marginBottom: '1rem' }}>{error}</div>}
                <UsernameForm
                  usernameInput={usernameInput}
                  onUsernameInputChange={setUsernameInput}
                  onUsernameSubmit={handleUsernameSubmit}
                  onUsernameKeyPress={handleUsernameKeyPress}
                />
              </>
            )}

            {username && (
              <>
                {/* All Accounts Summary */}
                {accounts.length > 0 && (
                  <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
                    <AllAccountsSummary summary={summary} />
                  </div>
                )}

                <h3 style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>Account Management</h3>
                {accountsLoading && <div style={{ marginBottom: '1rem', color: '#666' }}>Loading accounts...</div>}
                {accountsError && <div className="error" style={{ marginBottom: '1rem' }}>{accountsError}</div>}
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
              </>
            )}
          </div>
        )}

        {/* Message for non-logged-in users on other tabs */}
        {!username && currentTab !== 'settings' && (
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <p style={{ color: '#666', margin: '1rem 0' }}>
              Please go to <strong>Settings</strong> to log in.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

