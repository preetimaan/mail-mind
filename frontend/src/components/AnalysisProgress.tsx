import './AnalysisProgress.css'

interface AnalysisProgressProps {
  emailsProcessed: number
  totalEmails: number | null
  status: 'processing' | 'completed' | 'failed'
  message?: string
}

export default function AnalysisProgress({ emailsProcessed, totalEmails, status, message }: AnalysisProgressProps) {
  const isProcessing = status === 'processing'
  const progressPercent = totalEmails && totalEmails > 0 
    ? Math.min(100, Math.round((emailsProcessed / totalEmails) * 100))
    : null
  
  // Debug log to verify component is receiving updates
  console.log(`[AnalysisProgress] Render: ${emailsProcessed}${totalEmails ? `/${totalEmails}` : ''} (${progressPercent}%)`)
  
  return (
    <div className="analysis-progress-container">
      <div className="analysis-progress-header">
        <span className="analysis-progress-label">
          {isProcessing ? 'Processing emails...' : status === 'completed' ? 'Analysis completed' : 'Analysis failed'}
        </span>
        <span className="analysis-progress-count">
          {totalEmails 
            ? `${emailsProcessed.toLocaleString()} / ${totalEmails.toLocaleString()} emails`
            : `${emailsProcessed.toLocaleString()} ${emailsProcessed === 1 ? 'email' : 'emails'} processed`}
        </span>
      </div>
      {isProcessing && (
        <div className="analysis-progress-bar-container">
          <div className="analysis-progress-bar">
            <div 
              className="analysis-progress-bar-fill"
              style={{ 
                width: progressPercent !== null ? `${progressPercent}%` : '100%',
              }}
            />
          </div>
          <div className="analysis-progress-text">
            {emailsProcessed === 0 
              ? 'Starting analysis...' 
              : totalEmails
                ? `Processing... ${emailsProcessed.toLocaleString()} of ${totalEmails.toLocaleString()} emails (${progressPercent}%)`
                : `Processing... ${emailsProcessed.toLocaleString()} ${emailsProcessed === 1 ? 'email' : 'emails'} processed so far`}
          </div>
        </div>
      )}
      {message && (
        <div className="analysis-progress-message">
          {message}
        </div>
      )}
    </div>
  )
}

