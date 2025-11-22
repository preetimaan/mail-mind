import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { SenderInsights } from '../api/client'

interface SenderChartProps {
  insights: SenderInsights
}

export default function SenderChart({ insights }: SenderChartProps) {
  const data = insights.top_senders.slice(0, 10).map((sender) => ({
    name: sender.name || sender.email.split('@')[0],
    count: sender.count,
    percentage: sender.percentage,
  }))

  return (
    <div>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="count" fill="#667eea" name="Email Count" />
        </BarChart>
      </ResponsiveContainer>
      
      <div style={{ marginTop: '1rem' }}>
        <h3>Top Domains</h3>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {insights.top_domains.map((domain) => (
            <li key={domain.domain} style={{ padding: '0.5rem', background: '#f8f9fa', marginBottom: '0.5rem', borderRadius: '4px' }}>
              <strong>{domain.domain}</strong>: {domain.count} emails
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

