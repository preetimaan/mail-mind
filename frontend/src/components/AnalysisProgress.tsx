import './AnalysisProgress.css'

interface AnalysisProgressProps {
  emailsProcessed: number
  totalEmails: number | null
  status: 'processing' | 'completed' | 'failed'
  message?: string
  currentChunk?: number | null
  totalChunks?: number | null
}

export default function AnalysisProgress({ emailsProcessed, totalEmails, status, message, currentChunk, totalChunks }: AnalysisProgressProps) {
  const isProcessing = status === 'processing'
  const progressPercent = totalEmails && totalEmails > 0 
    ? Math.min(100, Math.round((emailsProcessed / totalEmails) * 100))
    : null
  
  const progressLabel = isProcessing
    ? totalEmails && totalEmails > 0
      ? `Analyzing emails: ${emailsProcessed.toLocaleString()} of ${totalEmails.toLocaleString()} (${progressPercent}%)`
      : emailsProcessed === 0
        ? 'Starting analysis...'
        : `Analyzing emails: ${emailsProcessed.toLocaleString()} processed`
    : status === 'completed'
      ? 'Analysis completed'
      : 'Analysis failed'

  return (
    <div className="analysis-progress-container">
      <div className="analysis-progress-header">
        <span className="analysis-progress-label">
          {progressLabel}
          {isProcessing && currentChunk && totalChunks && totalChunks > 1 && (
            <span style={{ fontSize: '0.85rem', color: '#6b7280', marginLeft: '0.5rem' }}>
              (Chunk {currentChunk}/{totalChunks})
            </span>
          )}
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

