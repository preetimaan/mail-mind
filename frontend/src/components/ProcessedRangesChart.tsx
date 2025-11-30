import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
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
        coverage: 0,
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
      const hasGap = coveragePercent < 100 // Any coverage less than 100% is a gap
      
      return {
        month: format(month, 'MMM yyyy'),
        year: year.toString(),
        coverage: Math.min(100, Math.round(coveragePercent)),
        processedDays,
        totalDays: totalDaysInMonth,
        emails: totalEmails,
        hasGap: hasGap
      }
    })
  }, [ranges])

  if (chartData.length === 0) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>No data to display</div>
  }

  return (
    <div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="month" 
            angle={-45}
            textAnchor="end"
            height={80}
            interval={0}
          />
          <YAxis 
            label={{ value: 'Coverage %', angle: -90, position: 'insideLeft' }}
            domain={[0, 100]}
          />
          <Tooltip 
            formatter={(value: number, name: string) => {
              if (name === 'coverage') {
                return [`${value}%`, 'Coverage']
              }
              return [value, name]
            }}
            labelFormatter={(label) => `Month: ${label}`}
          />
          <Legend />
          <Bar dataKey="coverage" name="Coverage %" fill="#667eea">
            {chartData.map((entry, index) => {
              // Red for gaps (< 100%), green for 100% coverage
              const fillColor = entry.hasGap ? "#dc3545" : "#667eea";
              return (
                <Cell 
                  key={`cell-${index}`} 
                  fill={fillColor} 
                />
              )
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

