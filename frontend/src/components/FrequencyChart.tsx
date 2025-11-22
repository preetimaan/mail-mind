import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import { FrequencyInsights } from '../api/client'

interface FrequencyChartProps {
  insights: FrequencyInsights
}

export default function FrequencyChart({ insights }: FrequencyChartProps) {
  const hourlyData = Object.entries(insights.hourly_distribution)
    .map(([hour, count]) => ({
      hour: `${hour}:00`,
      hourNum: parseInt(hour),
      count,
    }))
    .sort((a, b) => a.hourNum - b.hourNum)
    .map(({ hourNum, ...rest }) => rest)

  // Weekday order: Monday through Sunday
  const weekdayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  const weekdayData = weekdayOrder
    .map(day => ({
      day,
      count: insights.weekday_distribution[day] || 0,
    }))
    .filter(item => item.count > 0 || weekdayOrder.includes(item.day))

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h3>Daily Average: {insights.daily_average.toFixed(2)} emails/day</h3>
        <p>Total: {insights.total_emails} emails over {insights.unique_days} days</p>
        {insights.peak_hour !== null && (
          <p>Peak Hour: {insights.peak_hour}:00</p>
        )}
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <h3>Hourly Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={hourlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#667eea" name="Emails" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h3>Weekday Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={weekdayData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#764ba2" name="Emails" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

