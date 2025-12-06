import { useState, useEffect } from 'react'

interface DateRangePickerProps {
  onAnalyze: (startDate: Date, endDate: Date, forceReanalysis?: boolean) => void
  loading: boolean
  disabled: boolean
  initialStartDate?: Date
  initialEndDate?: Date
}

export default function DateRangePicker({ onAnalyze, loading, disabled, initialStartDate, initialEndDate }: DateRangePickerProps) {
  const formatDateForInput = (date: Date) => {
    return date.toISOString().split('T')[0]
  }
  
  const [startDate, setStartDate] = useState(initialStartDate ? formatDateForInput(initialStartDate) : '')
  const [endDate, setEndDate] = useState(initialEndDate ? formatDateForInput(initialEndDate) : '')
  const [forceReanalysis, setForceReanalysis] = useState(false)
  
  // Update when initial dates change
  useEffect(() => {
    if (initialStartDate) {
      setStartDate(formatDateForInput(initialStartDate))
    }
    if (initialEndDate) {
      setEndDate(formatDateForInput(initialEndDate))
    }
  }, [initialStartDate, initialEndDate])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!startDate || !endDate) {
      alert('Please select both start and end dates')
      return
    }

    const start = new Date(startDate)
    const end = new Date(endDate)

    if (start > end) {
      alert('Start date must be before end date')
      return
    }

    onAnalyze(start, end, forceReanalysis)
  }

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '1rem', alignItems: 'end' }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="label">Start Date</label>
          <input
            type="date"
            className="input"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            disabled={disabled}
            required
          />
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="label">End Date</label>
          <input
            type="date"
            className="input"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            disabled={disabled}
            required
          />
        </div>
        <button
          type="submit"
          className="button"
          disabled={disabled || loading || !startDate || !endDate}
          style={{ marginBottom: 0 }}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
      <div style={{ marginTop: '0.5rem' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
          <input
            type="checkbox"
            checked={forceReanalysis}
            onChange={(e) => setForceReanalysis(e.target.checked)}
            disabled={disabled || loading}
            style={{ cursor: 'pointer' }}
          />
          <span>Force re-analysis (overwrite existing processed ranges)</span>
        </label>
      </div>
    </form>
  )
}

