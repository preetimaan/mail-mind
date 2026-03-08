import { FrequencyInsights } from '../api/client'

interface FrequencyChartProps {
  insights: FrequencyInsights
}

export default function FrequencyChart({ insights }: FrequencyChartProps) {
  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Daily Average: {insights.daily_average.toFixed(2)} emails/day</h3>
        <p>Total: {insights.total_emails} emails over {insights.unique_days} days</p>
      </div>
    </div>
  )
}

