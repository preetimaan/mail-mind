import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { SenderInsights } from '../api/client'

interface SenderChartProps {
  insights: SenderInsights
}

export default function SenderChart({ insights }: SenderChartProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const [copiedAll, setCopiedAll] = useState(false)

  const data = insights.top_senders.slice(0, 10).map((sender) => ({
    name: sender.name || sender.email.split('@')[0],
    count: sender.count,
    percentage: sender.percentage,
  }))

  const topSenders = insights.top_senders.slice(0, 10)

  const copyEmail = async (email: string, index: number) => {
    try {
      await navigator.clipboard.writeText(email)
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const copyAllEmails = async () => {
    const allEmails = topSenders.map(s => s.email).join(', ')
    try {
      await navigator.clipboard.writeText(allEmails)
      setCopiedAll(true)
      setTimeout(() => setCopiedAll(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

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
      
      <div style={{ marginTop: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0 }}>Top Senders</h3>
          <button
            onClick={copyAllEmails}
            type="button"
            style={{
              background: 'none',
              border: '1px solid #667eea',
              color: '#667eea',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              fontSize: '0.9rem',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.2s',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#667eea'
              e.currentTarget.style.color = '#fff'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent'
              e.currentTarget.style.color = '#667eea'
            }}
          >
            {copiedAll ? '✓ Copied!' : '📋 Copy All Emails'}
          </button>
        </div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {topSenders.map((sender, index) => (
            <li 
              key={sender.email} 
              style={{ 
                padding: '0.75rem', 
                background: '#f8f9fa', 
                marginBottom: '0.5rem', 
                borderRadius: '4px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '1rem'
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: '500', marginBottom: '0.25rem' }}>
                  {sender.name || sender.email.split('@')[0]}
                </div>
                <div style={{ fontSize: '0.9rem', color: '#666', wordBreak: 'break-all' }}>
                  {sender.email}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#999', marginTop: '0.25rem' }}>
                  {sender.count} emails ({sender.percentage.toFixed(1)}%)
                </div>
              </div>
              <button
                onClick={() => copyEmail(sender.email, index)}
                type="button"
                style={{
                  background: copiedIndex === index ? '#28a745' : 'none',
                  border: copiedIndex === index ? '1px solid #28a745' : '1px solid #ddd',
                  color: copiedIndex === index ? '#fff' : '#333',
                  padding: '0.5rem 1rem',
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  fontWeight: '500',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap',
                  flexShrink: 0,
                }}
                onMouseEnter={(e) => {
                  if (copiedIndex !== index) {
                    e.currentTarget.style.backgroundColor = '#f8f9fa'
                    e.currentTarget.style.borderColor = '#bbb'
                  }
                }}
                onMouseLeave={(e) => {
                  if (copiedIndex !== index) {
                    e.currentTarget.style.backgroundColor = 'transparent'
                    e.currentTarget.style.borderColor = '#ddd'
                  }
                }}
              >
                {copiedIndex === index ? '✓ Copied' : '📋 Copy'}
              </button>
            </li>
          ))}
        </ul>
      </div>
      
      <div style={{ marginTop: '2rem' }}>
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

