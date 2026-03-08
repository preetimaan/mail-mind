import { useMemo } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format, parseISO, differenceInDays, eachMonthOfInterval } from 'date-fns'

interface ProcessedRange {
  start_date: string
  end_date: string
  emails_count: number
  processed_at: string
}

interface ProcessedRangesChartProps {
  ranges: ProcessedRange[]
}

export default function ProcessedRangesChart({ ranges }: ProcessedRangesChartProps) {
  const chartData = useMemo(() => {
    // If no ranges, show last 12 months
    if (ranges.length === 0) {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setMonth(startDate.getMonth() - 12)
      const months = eachMonthOfInterval({ start: startDate, end: endDate })
      return months.map(month => ({
        month: format(month, 'MMM yyyy'),
        year: month.getFullYear().toString(),
        processed: 0, // 0 = No, 1 = Yes
        processedDays: 0,
        totalDays: new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate(),
        emails: 0,
        hasGap: true
      }))
    }

    // Find the overall date range from processed ranges
    const allDates = ranges.flatMap(r => [
      parseISO(r.start_date),
      parseISO(r.end_date)
    ])
    const minDate = new Date(Math.min(...allDates.map(d => d.getTime())))
    const maxDate = new Date(Math.max(...allDates.map(d => d.getTime())))
    
    // Extend range to include current month and a bit before first processed date
    const chartStart = new Date(minDate)
    chartStart.setMonth(chartStart.getMonth() - 1)
    chartStart.setDate(1) // Start of month
    const chartEnd = new Date()
    chartEnd.setMonth(chartEnd.getMonth() + 1)
    chartEnd.setDate(0) // End of current month
    
    // Create monthly buckets
    const months = eachMonthOfInterval({ start: chartStart, end: chartEnd })
    
    return months.map(month => {
      // Get first and last day of the month
      const monthStart = new Date(month.getFullYear(), month.getMonth(), 1)
      const monthEnd = new Date(month.getFullYear(), month.getMonth() + 1, 0)
      const year = month.getFullYear()
      
      // Check if this month has any processed ranges
      let processedDays = 0
      let totalEmails = 0
      
      ranges.forEach(range => {
        const rangeStart = parseISO(range.start_date)
        const rangeEnd = parseISO(range.end_date)
        
        // Check if range overlaps with this month
        if (rangeStart <= monthEnd && rangeEnd >= monthStart) {
          const overlapStart = rangeStart > monthStart ? rangeStart : monthStart
          const overlapEnd = rangeEnd < monthEnd ? rangeEnd : monthEnd
          const days = differenceInDays(overlapEnd, overlapStart) + 1
          processedDays += days
          totalEmails += range.emails_count
        }
      })
      
      const totalDaysInMonth = differenceInDays(monthEnd, monthStart) + 1
      const coveragePercent = totalDaysInMonth > 0 ? (processedDays / totalDaysInMonth) * 100 : 0
      
      return {
        month: format(month, 'MMM yyyy'),
        year: year.toString(),
        coverage: Math.min(100, Math.round(coveragePercent)),
        processedDays,
        totalDays: totalDaysInMonth,
        emails: totalEmails
      }
    })
  }, [ranges])

  if (chartData.length === 0) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>No data to display</div>
  }

  // Calculate dynamic interval based on time range
  const calculateInterval = () => {
    if (chartData.length === 0) return 0
    const totalMonths = chartData.length
    // Show all labels if <= 12 months
    if (totalMonths <= 12) return 0
    // Show every 2nd month if 13-24 months
    if (totalMonths <= 24) return 1
    // Show every 3rd month if 25-36 months
    if (totalMonths <= 36) return 2
    // Show every 6th month if 37-60 months
    if (totalMonths <= 60) return 5
    // Show every 12th month (yearly) if > 60 months
    return 11
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div style={{
          backgroundColor: 'white',
          padding: '12px',
          border: '1px solid #ccc',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 600, color: '#2c3e50' }}>{label}</p>
          <p style={{ margin: '4px 0', fontSize: '0.9rem', color: '#667eea' }}>
            Coverage: <strong>{data.coverage}%</strong>
          </p>
          <p style={{ margin: '4px 0', fontSize: '0.85rem', color: '#666' }}>
            {data.processedDays} of {data.totalDays} days processed
          </p>
          {data.emails > 0 && (
            <p style={{ margin: '4px 0', fontSize: '0.85rem', color: '#666' }}>
              {data.emails.toLocaleString()} emails
            </p>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div>
      <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #e9ecef' }}>
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#666' }}>
          📊 Timeline shows continuous coverage of analyzed email data. Gaps indicate unprocessed date ranges.
        </p>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <defs>
            <linearGradient id="coverageGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#667eea" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#667eea" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="month" 
            angle={-45}
            textAnchor="end"
            height={80}
            interval={calculateInterval()}
            tick={{ fontSize: 12, fill: '#666' }}
          />
          <YAxis 
            domain={[0, 100]}
            ticks={[0, 25, 50, 75, 100]}
            tickFormatter={(value) => `${value}%`}
            tick={{ fontSize: 12, fill: '#666' }}
            label={{ value: 'Coverage', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#666' } }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="coverage" 
            stroke="#667eea" 
            strokeWidth={2}
            fill="url(#coverageGradient)"
            dot={false}
            activeDot={{ r: 5, fill: '#667eea' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

