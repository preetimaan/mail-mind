import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { format } from 'date-fns'

interface ProcessedRangesProps {
  username: string
  accountId: number
}

interface ProcessedRange {
  start_date: string
  end_date: string
  emails_count: number
  processed_at: string
}

export default function ProcessedRanges({ username, accountId }: ProcessedRangesProps) {
  const [ranges, setRanges] = useState<ProcessedRange[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadRanges()
  }, [username, accountId])

  const loadRanges = async () => {
    try {
      const response = await api.get(
        `/api/insights/processed-ranges?username=${username}&account_id=${accountId}`
      )
      setRanges(response.data)
    } catch (err) {
      console.error('Failed to load processed ranges:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="card">Loading processed ranges...</div>
  }

  if (ranges.length === 0) {
    return (
      <div className="card">
        <h2>Processed Date Ranges</h2>
        <p>No date ranges have been processed yet.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2>Processed Date Ranges</h2>
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
              <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '0.75rem' }}>
                  {format(new Date(range.start_date), 'MMM d, yyyy')}
                </td>
                <td style={{ padding: '0.75rem' }}>
                  {format(new Date(range.end_date), 'MMM d, yyyy')}
                </td>
                <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                  {range.emails_count.toLocaleString()}
                </td>
                <td style={{ padding: '0.75rem' }}>
                  {format(new Date(range.processed_at), 'MMM d, yyyy HH:mm')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

