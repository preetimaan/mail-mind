import { useState } from 'react'
import { api, AnalysisRun } from '../api/client'

interface UseAnalysisPollingOptions {
  username: string | null
  selectedAccount: number | null
  onComplete: () => void
  onError: (error: string) => void
  onSuccess: (message: string) => void
  checkAccountStatus?: (accountId: number) => Promise<boolean>
  onProgress?: (emailsProcessed: number, status: string) => void
}

export function useAnalysisPolling({
  username,
  selectedAccount,
  onComplete,
  onError,
  onSuccess,
  checkAccountStatus,
  onProgress,
}: UseAnalysisPollingOptions) {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<{ emailsProcessed: number; totalEmails: number | null; status: string } | null>(null)

  const pollAnalysisRun = (runId: number): Promise<void> => {
    if (!username) return Promise.resolve()

    // Set loading and initial progress state
    setLoading(true)
    setProgress({ emailsProcessed: 0, totalEmails: null, status: 'processing' })

    return new Promise((resolve) => {
      const pollInterval = setInterval(async () => {
        try {
          const runResponse = await api.get(`/api/analysis/runs/${runId}?username=${username}`)
          const run = runResponse.data
          
          // Update progress - always update if status is processing
          const emailsProcessed = run.emails_processed ?? 0
          const totalEmails = run.total_emails ?? null
          
          // Update progress state whenever status is processing or pending
          if (run.status === 'processing' || run.status === 'pending') {
            // Always create a new object to ensure React detects the change
            // This is important because emails_processed increments during processing
            console.log(`[Progress] Polling: ${emailsProcessed}${totalEmails ? `/${totalEmails}` : ''} emails, status: ${run.status}`)
            setProgress({ emailsProcessed, totalEmails, status: run.status })
            if (onProgress) {
              onProgress(emailsProcessed, run.status)
            }
          }
          
          if (run.status === 'completed' || run.status === 'failed' || run.status === 'cancelled') {
            clearInterval(pollInterval)
            setLoading(false)
            setProgress(null)
          
            if (run.status === 'completed') {
              const emailCount = run.emails_processed ?? 0
              onSuccess(`Analysis completed! Processed ${emailCount} emails.`)
              onComplete()
            } else if (run.status === 'cancelled') {
              onSuccess('Analysis stopped successfully.')
              onComplete()
            } else {
              // Check if account is inactive (token expired)
              if (checkAccountStatus && selectedAccount) {
                const isActive = await checkAccountStatus(selectedAccount)
                if (!isActive) {
                  onError('Analysis failed: Your email account credentials have expired or been revoked. Please reconnect your account using the "Reconnect" button, then try again.')
                } else {
                  const errorMsg = run.error_message || 'Analysis failed. Possible causes: Expired credentials, network issues, or email service unavailable. Check your account status and try again, or use the "Retry" button.'
                  onError(errorMsg)
                }
              } else {
                const errorMsg = run.error_message || 'Analysis failed. Please check your account credentials and try again.'
                onError(errorMsg)
              }
            }
            resolve()
          }
        } catch (err) {
          clearInterval(pollInterval)
          setLoading(false)
          setProgress(null)
          onError('Failed to check analysis status')
          resolve()
        }
    }, 2000)
    })
  }

  return {
    loading,
    setLoading,
    pollAnalysisRun,
    progress,
  }
}

