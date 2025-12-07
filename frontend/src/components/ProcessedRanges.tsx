import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import { format } from 'date-fns'
import ProcessedRangesChart from './ProcessedRangesChart'

interface ProcessedRangesProps {
  username: string
  accountId: number
  refreshTrigger?: number // When this changes, component will refresh
  onSelectGap?: (startDate: Date, endDate: Date) => void // Callback when user clicks a gap
}

interface ProcessedRange {
  start_date: string
  end_date: string
  emails_count: number
  processed_at: string
}

interface Gap {
  start_date: string
  end_date: string
  days: number
}

export default function ProcessedRanges({ username, accountId, refreshTrigger, onSelectGap }: ProcessedRangesProps) {
  const [ranges, setRanges] = useState<ProcessedRange[]>([])
  const [gaps, setGaps] = useState<Gap[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadRanges = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [rangesResponse, gapsResponse] = await Promise.all([
        api.get(`/api/insights/processed-ranges?username=${username}&account_id=${accountId}`),
        api.get(`/api/insights/processed-ranges/gaps?username=${username}&account_id=${accountId}`).catch(() => ({ data: [] }))
      ])
      // Ensure response.data is an array
      const data = Array.isArray(rangesResponse.data) ? rangesResponse.data : []
      setRanges(data)
      
      const gapsData = Array.isArray(gapsResponse.data) ? gapsResponse.data : []
      setGaps(gapsData)
    } catch (err: any) {
      console.error('Failed to load processed ranges:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load processed ranges'
      setError(errorMessage)
      setRanges([])
      setGaps([])
    } finally {
      setLoading(false)
    }
  }, [username, accountId])

  useEffect(() => {
    loadRanges()
  }, [loadRanges, refreshTrigger])

  if (loading) {
    return (
      <div className="card">
        <h2>Processed Date Ranges</h2>
        <p>Loading processed ranges...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <h2>Processed Date Ranges</h2>
        <div className="error" style={{ marginTop: '1rem' }}>
          {error}
        </div>
        <button 
          onClick={loadRanges} 
          className="button" 
          style={{ marginTop: '1rem' }}
        >
          Retry
        </button>
      </div>
    )
  }

  if (ranges.length === 0) {
    return (
      <div className="card">
        <h2>Processed Date Ranges</h2>
        <p>No date ranges have been processed yet.</p>
        <button 
          onClick={loadRanges} 
          className="button" 
          style={{ marginTop: '1rem' }}
        >
          Refresh
        </button>
      </div>
    )
  }

  return (
    <div className="card">
      <h2>Processed Date Ranges</h2>
      
      {/* Chart showing coverage and gaps */}
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Coverage Timeline</h3>
        <ProcessedRangesChart ranges={ranges} />
      </div>
      
      {/* Gaps section - unprocessed date ranges */}
      {gaps.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Unprocessed Gaps ({gaps.length})</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {gaps.map((gap, idx) => (
              <div
                key={idx}
                onClick={() => {
                  if (onSelectGap) {
                    onSelectGap(new Date(gap.start_date), new Date(gap.end_date))
                  }
                }}
                style={{
                  padding: '0.75rem',
                  backgroundColor: onSelectGap ? '#fff' : 'transparent',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  cursor: onSelectGap ? 'pointer' : 'default',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (onSelectGap) {
                    e.currentTarget.style.backgroundColor = '#f5f5f5'
                    e.currentTarget.style.borderColor = '#bbb'
                  }
                }}
                onMouseLeave={(e) => {
                  if (onSelectGap) {
                    e.currentTarget.style.backgroundColor = '#fff'
                    e.currentTarget.style.borderColor = '#ddd'
                  }
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{format(new Date(gap.start_date), 'MMM d, yyyy')}</strong> -{' '}
                    <strong>{format(new Date(gap.end_date), 'MMM d, yyyy')}</strong>
                    <div style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.25rem' }}>
                      {gap.days} {gap.days === 1 ? 'day' : 'days'} unprocessed
                    </div>
                  </div>
                  {onSelectGap && (
                    <button
                      className="button"
                      style={{ 
                        marginLeft: '1rem',
                        padding: '0.5rem 1rem',
                        fontSize: '0.9rem'
                      }}
                      onClick={(e) => {
                        e.stopPropagation()
                        onSelectGap(new Date(gap.start_date), new Date(gap.end_date))
                      }}
                    >
                      Analyze This Gap
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Table with processed ranges */}
      <div>
        <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Processed Ranges</h3>
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>Start Date</th>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>End Date</th>
                <th style={{ padding: '0.75rem', textAlign: 'right' }}>Emails</th>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>Processed</th>
              </tr>
            </thead>
            <tbody>
              {ranges.map((range, idx) => (
                <tr 
                  key={idx} 
                  style={{ 
                    borderBottom: '1px solid #eee',
                    backgroundColor: '#fff'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f9f9f9'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#fff'
                  }}
                >
                  <td style={{ padding: '0.75rem', color: '#333' }}>
                    {format(new Date(range.start_date), 'MMM d, yyyy')}
                  </td>
                  <td style={{ padding: '0.75rem', color: '#333' }}>
                    {format(new Date(range.end_date), 'MMM d, yyyy')}
                  </td>
                  <td style={{ padding: '0.75rem', textAlign: 'right', color: '#333' }}>
                    {range.emails_count.toLocaleString()}
                  </td>
                  <td style={{ padding: '0.75rem', color: '#333' }}>
                    {format(new Date(range.processed_at), 'MMM d, yyyy HH:mm')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

