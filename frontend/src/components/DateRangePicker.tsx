import { useState, useEffect } from 'react'

interface DateRangePickerProps {
  onAnalyze: (startDate: Date, endDate: Date, forceReanalysis?: boolean) => void
  onStop?: () => void
  loading: boolean
  disabled: boolean
  hasRunningAnalysis: boolean
  initialStartDate?: Date
  initialEndDate?: Date
}

export default function DateRangePicker({ onAnalyze, onStop, loading, disabled, hasRunningAnalysis, initialStartDate, initialEndDate }: DateRangePickerProps) {
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

  const validateDateInput = (value: string, currentValue: string): string => {
    // Empty value is allowed
    if (!value) {
      return value
    }
    
    // If the value is in YYYY-MM-DD format, check if year exceeds 4 digits
    const isoMatch = value.match(/^(\d+)-(\d{2})-(\d{2})$/)
    if (isoMatch) {
      const year = isoMatch[1]
      // If year is longer than 4 digits, reject the input (return previous value)
      if (year.length > 4) {
        return currentValue
      }
    }
    
    // Check for partial input patterns
    // Pattern: YYYY-MM (year might be too long)
    const partialWithMonth = value.match(/^(\d+)-(\d{1,2})$/)
    if (partialWithMonth) {
      const year = partialWithMonth[1]
      if (year.length > 4) {
        return currentValue
      }
    }
    
    // Pattern: YYYY- (just year and dash)
    const partialWithDash = value.match(/^(\d+)-$/)
    if (partialWithDash) {
      const year = partialWithDash[1]
      if (year.length > 4) {
        return currentValue
      }
    }
    
    // Pattern: Just digits (user typing year)
    const justDigits = value.match(/^(\d+)$/)
    if (justDigits) {
      const year = justDigits[1]
      // If more than 4 digits, reject
      if (year.length > 4) {
        return currentValue
      }
    }
    
    return value
  }

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    const validated = validateDateInput(value, startDate)
    setStartDate(validated)
  }

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    const validated = validateDateInput(value, endDate)
    setEndDate(validated)
  }

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
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto auto', gap: '1rem', alignItems: 'end' }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="label">Start Date</label>
          <input
            type="date"
            className="input"
            value={startDate}
            onChange={handleStartDateChange}
            disabled={disabled}
            required
            max="9999-12-31"
          />
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="label">End Date</label>
          <input
            type="date"
            className="input"
            value={endDate}
            onChange={handleEndDateChange}
            disabled={disabled}
            required
            max="9999-12-31"
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
        <button
          type="button"
          className="button"
          onClick={onStop}
          disabled={!hasRunningAnalysis || !onStop}
          style={{ 
            marginBottom: 0,
            backgroundColor: hasRunningAnalysis ? '#dc3545' : '#6c757d',
            color: 'white',
            border: 'none',
            opacity: hasRunningAnalysis ? 1 : 0.6
          }}
        >
          Stop
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

