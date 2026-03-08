import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { SenderInsights, api, CustomCategory } from '../api/client'

interface SenderChartProps {
  insights: SenderInsights
  username: string
  accountId: number
  customCategories?: CustomCategory[]
  onAssignToCategory?: (senderEmail: string, categoryId: number) => Promise<void>
}

export default function SenderChart({ insights, username, accountId, customCategories = [], onAssignToCategory }: SenderChartProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const [copiedFilter, setCopiedFilter] = useState(false)
  const [selectedDomains, setSelectedDomains] = useState<Set<string>>(new Set())

  // Use top_domains instead of top_senders for the chart
  const domains = insights.top_domains || []
  const data = domains.slice(0, 10).map((domain) => ({
    name: domain.domain,
    count: domain.count,
    percentage: (domain.count / insights.total_emails) * 100,
  }))

  const toggleDomainSelection = (domain: string) => {
    const newSelected = new Set(selectedDomains)
    if (newSelected.has(domain)) {
      newSelected.delete(domain)
    } else {
      newSelected.add(domain)
    }
    setSelectedDomains(newSelected)
  }

  const selectAll = () => {
    const allDomains = new Set(domains.map(d => d.domain))
    setSelectedDomains(allDomains)
  }

  const clearSelection = () => {
    setSelectedDomains(new Set())
  }

  const generateFilterString = () => {
    if (selectedDomains.size === 0) return ''
    const domainList = Array.from(selectedDomains)
    // Gmail filter format: from:*@domain1.com OR from:*@domain2.com
    return domainList.map(d => `from:*@${d}`).join(' OR ')
  }

  const copyFilterString = async () => {
    const filterString = generateFilterString()
    if (!filterString) return
    
    try {
      await navigator.clipboard.writeText(filterString)
      setCopiedFilter(true)
      setTimeout(() => setCopiedFilter(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const copyDomain = async (domain: string, index: number) => {
    try {
      await navigator.clipboard.writeText(domain)
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const CustomTooltip = ({ active, payload }: any) => {
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
          <p style={{ margin: '0 0 8px 0', fontWeight: 600, color: '#2c3e50' }}>{data.name}</p>
          <p style={{ margin: '4px 0', fontSize: '0.9rem', color: '#667eea' }}>
            Emails: <strong>{data.count.toLocaleString()}</strong>
          </p>
          <p style={{ margin: '4px 0', fontSize: '0.85rem', color: '#666' }}>
            {data.percentage.toFixed(1)}% of total
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div>
      <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #e9ecef' }}>
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#666' }}>
          🌐 Top email domains by volume
        </p>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <defs>
            <linearGradient id="senderGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#667eea" stopOpacity={0.9}/>
              <stop offset="95%" stopColor="#667eea" stopOpacity={0.6}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="name" 
            angle={-45} 
            textAnchor="end" 
            height={100}
            tick={{ fontSize: 12, fill: '#666' }}
          />
          <YAxis tick={{ fontSize: 12, fill: '#666' }} />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="count" 
            fill="url(#senderGradient)" 
            name="Email Count"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      
      {/* Filter String Generator */}
      {selectedDomains.size > 0 && (
        <div style={{ 
          marginTop: '1.5rem', 
          padding: '1rem', 
          backgroundColor: '#e8f4fd', 
          borderRadius: '8px',
          border: '1px solid #b8daff'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <strong style={{ color: '#004085' }}>{selectedDomains.size} domain(s) selected</strong>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={clearSelection}
                type="button"
                style={{
                  background: 'none',
                  border: '1px solid #6c757d',
                  color: '#6c757d',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                }}
              >
                Clear Selection
              </button>
              <button
                onClick={copyFilterString}
                type="button"
                style={{
                  background: copiedFilter ? '#28a745' : '#007bff',
                  border: 'none',
                  color: '#fff',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  fontWeight: '500',
                }}
              >
                {copiedFilter ? '✓ Copied!' : '📋 Copy Filter String'}
              </button>
            </div>
          </div>
          <div style={{ 
            backgroundColor: '#fff', 
            padding: '0.75rem', 
            borderRadius: '4px', 
            fontFamily: 'monospace', 
            fontSize: '0.85rem',
            wordBreak: 'break-all',
            maxHeight: '100px',
            overflowY: 'auto'
          }}>
            {generateFilterString()}
          </div>
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.8rem', color: '#666' }}>
            Paste this in Gmail search or use it to create a filter
          </p>
        </div>
      )}
      
      {/* Domains List */}
      <div style={{ marginTop: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3 style={{ margin: 0 }}>
            Top Domains ({domains.length})
          </h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              onClick={selectAll}
              type="button"
              style={{
                background: 'none',
                border: '1px solid #667eea',
                color: '#667eea',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                fontSize: '0.9rem',
                cursor: 'pointer',
              }}
            >
              Select All
            </button>
          </div>
        </div>
        
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {domains.map((domain, index) => (
            <li 
              key={`${domain.domain}-${index}`}
              style={{ 
                padding: '0.5rem 0.75rem', 
                background: selectedDomains.has(domain.domain) ? '#e8f4fd' : '#f8f9fa', 
                marginBottom: '0.25rem', 
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                border: selectedDomains.has(domain.domain) ? '1px solid #b8daff' : '1px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onClick={() => toggleDomainSelection(domain.domain)}
            >
              <input
                type="checkbox"
                checked={selectedDomains.has(domain.domain)}
                onChange={() => toggleDomainSelection(domain.domain)}
                onClick={(e) => e.stopPropagation()}
                style={{ 
                  width: '16px', 
                  height: '16px', 
                  cursor: 'pointer',
                  accentColor: '#667eea',
                  flexShrink: 0
                }}
              />
              <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span style={{ fontWeight: '500', fontSize: '1rem', color: '#2c3e50' }}>
                  {domain.domain}
                </span>
                <span style={{ fontSize: '0.85rem', color: '#999', whiteSpace: 'nowrap' }}>
                  ({domain.count} · {((domain.count / insights.total_emails) * 100).toFixed(1)}%)
                </span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  copyDomain(domain.domain, index)
                }}
                type="button"
                style={{
                  background: copiedIndex === index ? '#28a745' : 'none',
                  border: copiedIndex === index ? '1px solid #28a745' : '1px solid #ddd',
                  color: copiedIndex === index ? '#fff' : '#333',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  fontWeight: '500',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap',
                  flexShrink: 0,
                }}
              >
                {copiedIndex === index ? '✓' : '📋'}
              </button>
            </li>
          ))}
        </ul>
      </div>
      
    </div>
  )
}
