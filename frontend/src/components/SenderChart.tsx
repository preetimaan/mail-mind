import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { SenderInsights, api } from '../api/client'

interface SenderChartProps {
  insights: SenderInsights
  username: string
  accountId: number
}

export default function SenderChart({ insights, username, accountId }: SenderChartProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const [copiedFilter, setCopiedFilter] = useState(false)
  const [senders, setSenders] = useState(insights.top_senders)
  const [offset, setOffset] = useState(insights.offset)
  const [hasMore, setHasMore] = useState(insights.has_more)
  const [loadingMore, setLoadingMore] = useState(false)
  const [selectedSenders, setSelectedSenders] = useState<Set<string>>(new Set())
  const [totalSenders, setTotalSenders] = useState(insights.total_senders)

  const data = senders.slice(0, 10).map((sender) => ({
    name: sender.name || sender.email.split('@')[0],
    count: sender.count,
    percentage: sender.percentage,
  }))

  const loadMore = async () => {
    if (loadingMore || !hasMore) return
    
    const newOffset = offset + 20
    if (newOffset >= 100) return // Cap at 100
    
    setLoadingMore(true)
    try {
      const response = await api.get(`/api/insights/senders?username=${username}&account_id=${accountId}&limit=20&offset=${newOffset}`)
      setSenders([...senders, ...response.data.top_senders])
      setOffset(newOffset)
      setHasMore(response.data.has_more && newOffset + 20 < 100)
      setTotalSenders(response.data.total_senders)
    } catch (err) {
      console.error('Failed to load more senders:', err)
    } finally {
      setLoadingMore(false)
    }
  }

  const toggleSenderSelection = (email: string) => {
    const newSelected = new Set(selectedSenders)
    if (newSelected.has(email)) {
      newSelected.delete(email)
    } else {
      newSelected.add(email)
    }
    setSelectedSenders(newSelected)
  }

  const selectAll = () => {
    const allEmails = new Set(senders.map(s => s.email))
    setSelectedSenders(allEmails)
  }

  const clearSelection = () => {
    setSelectedSenders(new Set())
  }

  const generateFilterString = () => {
    if (selectedSenders.size === 0) return ''
    const emails = Array.from(selectedSenders)
    // Gmail filter format: from:email1 OR from:email2 OR from:email3
    return emails.map(e => `from:${e}`).join(' OR ')
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

  const copyEmail = async (email: string, index: number) => {
    try {
      await navigator.clipboard.writeText(email)
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex(null), 2000)
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
      
      {/* Filter String Generator */}
      {selectedSenders.size > 0 && (
        <div style={{ 
          marginTop: '1.5rem', 
          padding: '1rem', 
          backgroundColor: '#e8f4fd', 
          borderRadius: '8px',
          border: '1px solid #b8daff'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <strong style={{ color: '#004085' }}>{selectedSenders.size} sender(s) selected</strong>
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
      
      <div style={{ marginTop: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3 style={{ margin: 0 }}>
            Top Senders ({senders.length} of {totalSenders})
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
          {senders.map((sender, index) => (
            <li 
              key={`${sender.email}-${index}`}
              style={{ 
                padding: '0.5rem 0.75rem', 
                background: selectedSenders.has(sender.email) ? '#e8f4fd' : '#f8f9fa', 
                marginBottom: '0.25rem', 
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                border: selectedSenders.has(sender.email) ? '1px solid #b8daff' : '1px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onClick={() => toggleSenderSelection(sender.email)}
            >
              <input
                type="checkbox"
                checked={selectedSenders.has(sender.email)}
                onChange={() => toggleSenderSelection(sender.email)}
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
                <span style={{ fontWeight: '500', whiteSpace: 'nowrap' }}>
                  {sender.name || sender.email.split('@')[0]}
                </span>
                <span style={{ fontSize: '0.85rem', color: '#666', wordBreak: 'break-all' }}>
                  {sender.email}
                </span>
                <span style={{ fontSize: '0.8rem', color: '#999', whiteSpace: 'nowrap' }}>
                  ({sender.count} · {sender.percentage.toFixed(1)}%)
                </span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  copyEmail(sender.email, index)
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
        
        {/* Load More Button */}
        {hasMore && senders.length < 100 && (
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <button
              onClick={loadMore}
              disabled={loadingMore}
              type="button"
              style={{
                background: '#667eea',
                border: 'none',
                color: '#fff',
                padding: '0.75rem 2rem',
                borderRadius: '4px',
                fontSize: '1rem',
                cursor: loadingMore ? 'wait' : 'pointer',
                fontWeight: '500',
                opacity: loadingMore ? 0.7 : 1,
              }}
            >
              {loadingMore ? 'Loading...' : `Load More (${Math.min(20, 100 - senders.length)} more)`}
            </button>
            <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem', color: '#666' }}>
              Showing {senders.length} of {Math.min(100, totalSenders)} senders (max 100)
            </p>
          </div>
        )}
        
        {senders.length >= 100 && (
          <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.9rem', color: '#666' }}>
            Showing top 100 senders
          </p>
        )}
      </div>
      
      <div style={{ marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Top Domains</h3>
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
