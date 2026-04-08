import { useMemo } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import {
  format,
  parseISO,
  differenceInDays,
  differenceInMonths,
  eachMonthOfInterval,
  eachYearOfInterval,
  startOfMonth,
  endOfMonth,
  startOfYear,
  endOfYear,
} from 'date-fns'

interface ProcessedRange {
  start_date: string
  end_date: string
  emails_count: number
  processed_at: string
}

interface ProcessedRangesChartProps {
  ranges: ProcessedRange[]
}

type BucketGranularity = 'month' | 'year'

export default function ProcessedRangesChart({ ranges }: ProcessedRangesChartProps) {
  const chartData = useMemo(() => {
    // If no ranges, show last 12 months (all unprocessed)
    if (ranges.length === 0) {
      const endDate = endOfMonth(new Date())
      const startDate = startOfMonth(new Date(new Date().getFullYear(), new Date().getMonth() - 11, 1))
      const months = eachMonthOfInterval({ start: startDate, end: endDate })

      return months.map((monthStart) => {
        const bucketStart = startOfMonth(monthStart)
        const bucketEnd = endOfMonth(monthStart)
        const totalDays = differenceInDays(bucketEnd, bucketStart) + 1
        return {
          x: bucketStart.getTime(),
          label: format(bucketStart, 'MMM yyyy'),
          processed: 0,
          coveragePercent: 0,
          processedDays: 0,
          totalDays,
          emails: 0,
        }
      })
    }

    // Find the overall date range from processed ranges
    const allDates = ranges.flatMap(r => [
      parseISO(r.start_date),
      parseISO(r.end_date)
    ])
    const minDate = new Date(Math.min(...allDates.map(d => d.getTime())))
    const maxDate = new Date(Math.max(...allDates.map(d => d.getTime())))
    
    // Decide whether to render monthly or yearly buckets.
    // If we have many data points / long spans, show years to keep axis readable.
    const spanMonths = Math.max(1, differenceInMonths(maxDate, minDate) + 1)
    const granularity: BucketGranularity = spanMonths > 36 ? 'year' : 'month'

    // X-axis bounds: round DOWN to start of month or Jan 1 (avoid weird "Dec" starts)
    // and round UP to end of month/year, including "now" so the timeline reaches current time.
    const now = new Date()
    const effectiveMax = maxDate > now ? maxDate : now

    const chartStart = granularity === 'year' ? startOfYear(minDate) : startOfMonth(minDate)
    const chartEnd = granularity === 'year' ? endOfYear(effectiveMax) : endOfMonth(effectiveMax)

    const buckets =
      granularity === 'year'
        ? eachYearOfInterval({ start: chartStart, end: chartEnd }).map((d) => ({
            bucketStart: startOfYear(d),
            bucketEnd: endOfYear(d),
            label: format(d, 'yyyy'),
          }))
        : eachMonthOfInterval({ start: chartStart, end: chartEnd }).map((d) => ({
            bucketStart: startOfMonth(d),
            bucketEnd: endOfMonth(d),
            label: format(d, 'MMM yyyy'),
          }))

    return buckets.map(({ bucketStart, bucketEnd, label }) => {
      let processedDays = 0
      let totalEmails = 0

      ranges.forEach((range) => {
        const rangeStart = parseISO(range.start_date)
        const rangeEnd = parseISO(range.end_date)

        if (rangeStart <= bucketEnd && rangeEnd >= bucketStart) {
          const overlapStart = rangeStart > bucketStart ? rangeStart : bucketStart
          const overlapEnd = rangeEnd < bucketEnd ? rangeEnd : bucketEnd
          const days = differenceInDays(overlapEnd, overlapStart) + 1
          processedDays += days
          totalEmails += range.emails_count
        }
      })

      const totalDays = differenceInDays(bucketEnd, bucketStart) + 1
      const coveragePercent = totalDays > 0 ? Math.min(100, Math.round((processedDays / totalDays) * 100)) : 0
      const fullyProcessed = processedDays >= totalDays && totalDays > 0

      return {
        x: bucketStart.getTime(),
        label,
        processed: fullyProcessed ? 1 : 0, // Y-axis is only "processed vs not"
        coveragePercent,
        processedDays: Math.min(processedDays, totalDays),
        totalDays,
        emails: totalEmails,
      }
    })
  }, [ranges])

  if (chartData.length === 0) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>No data to display</div>
  }

  // Calculate dynamic interval based on time range
  const calculateInterval = () => {
    if (chartData.length === 0) return 0
    const totalPoints = chartData.length
    if (totalPoints <= 12) return 0
    if (totalPoints <= 24) return 1
    if (totalPoints <= 36) return 2
    if (totalPoints <= 60) return 5
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
          <p style={{ margin: '4px 0', fontSize: '0.9rem', color: data.processed ? '#16a34a' : '#b45309' }}>
            Status: <strong>{data.processed ? 'Processed' : 'Unprocessed'}</strong>
          </p>
          <p style={{ margin: '4px 0', fontSize: '0.85rem', color: '#666' }}>
            Coverage in bucket: <strong>{data.coveragePercent}%</strong>
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
          📊 Timeline shows whether each time bucket is fully processed. Gaps indicate buckets with any unprocessed days.
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
            dataKey="label"
            angle={-45}
            textAnchor="end"
            height={80}
            interval={calculateInterval()}
            tick={{ fontSize: 12, fill: '#666' }}
          />
          <YAxis 
            domain={[0, 1]}
            ticks={[0, 1]}
            tickFormatter={(value) => (value === 1 ? 'Processed' : 'Unprocessed')}
            tick={{ fontSize: 12, fill: '#666' }}
            label={{ value: 'Status', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#666' } }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="stepAfter"
            dataKey="processed"
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

