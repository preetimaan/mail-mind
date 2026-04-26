import { useState, useRef, useEffect } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { CategoryInsights, api } from '../api/client'

interface CategoryChartProps {
  insights: CategoryInsights
  username: string
  accountId: number
}

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b', '#fa709a']

export default function CategoryChart({ insights, username, accountId }: CategoryChartProps) {
  const [hoveredCategory, setHoveredCategory] = useState<string | null>(null)
  const [categoryDomains, setCategoryDomains] = useState<Array<{ domain: string; count: number }>>([])
  const [loadingDomains, setLoadingDomains] = useState(false)
  const [modalPosition, setModalPosition] = useState({ x: 0, y: 0 })
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const leaveTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const data = insights.categories.map((cat) => ({
    name: cat.category.charAt(0).toUpperCase() + cat.category.slice(1),
    value: cat.count,
    percentage: cat.percentage,
    category: cat.category,
  }))

  const handleCategoryHover = async (category: string, event: any) => {
    // Clear any pending leave timeout
    if (leaveTimeoutRef.current) {
      clearTimeout(leaveTimeoutRef.current)
      leaveTimeoutRef.current = null
    }

    // Clear any pending hover timeout
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
    }

    // Set position based on mouse event
    if (event && event.clientX && event.clientY) {
      setModalPosition({ x: event.clientX, y: event.clientY })
    }

    // Delay showing modal slightly to avoid flickering
    hoverTimeoutRef.current = setTimeout(async () => {
      setHoveredCategory(category)
      setLoadingDomains(true)
      
      try {
        const response = await api.get(`/api/insights/category-domains?username=${username}&account_id=${accountId}&category=${category}`)
        setCategoryDomains(response.data.domains || [])
      } catch (err) {
        console.error('Failed to load category domains:', err)
        setCategoryDomains([])
      } finally {
        setLoadingDomains(false)
      }
    }, 300)
  }

  const handleCategoryLeave = () => {
    // Clear hover timeout if still pending
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
      hoverTimeoutRef.current = null
    }

    // Delay hiding to allow moving to modal
    leaveTimeoutRef.current = setTimeout(() => {
      setHoveredCategory(null)
      setCategoryDomains([])
    }, 200)
  }

  const handleModalEnter = () => {
    // Clear leave timeout when entering modal
    if (leaveTimeoutRef.current) {
      clearTimeout(leaveTimeoutRef.current)
      leaveTimeoutRef.current = null
    }
  }

  const handleModalLeave = () => {
    setHoveredCategory(null)
    setCategoryDomains([])
  }

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current)
      if (leaveTimeoutRef.current) clearTimeout(leaveTimeoutRef.current)
    }
  }, [])

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
            Emails: <strong>{data.value.toLocaleString()}</strong>
          </p>
          <p style={{ margin: '4px 0', fontSize: '0.9rem', color: '#666' }}>
            Percentage: <strong>{data.percentage.toFixed(1)}%</strong>
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
          📊 Distribution of emails by category • Hover over a segment to see top domains
        </p>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <defs>
            {COLORS.map((color, index) => (
              <linearGradient key={`gradient-${index}`} id={`categoryGradient${index}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.9}/>
                <stop offset="95%" stopColor={color} stopOpacity={0.6}/>
              </linearGradient>
            ))}
          </defs>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={80}
            outerRadius={130}
            labelLine={false}
            label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
            fill="#8884d8"
            dataKey="value"
            animationBegin={0}
            animationDuration={800}
            onMouseEnter={(entry, index, e) => handleCategoryHover(entry.category, e)}
            onMouseLeave={handleCategoryLeave}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={`url(#categoryGradient${index % COLORS.length})`}
                stroke="#fff"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="bottom" 
            height={36}
            iconType="circle"
            wrapperStyle={{ fontSize: '12px' }}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Category Domains Modal */}
      {hoveredCategory && (
        <div
          onMouseEnter={handleModalEnter}
          onMouseLeave={handleModalLeave}
          style={{
            position: 'fixed',
            left: `${modalPosition.x + 20}px`,
            top: `${modalPosition.y}px`,
            backgroundColor: 'white',
            padding: '1rem',
            borderRadius: '8px',
            border: '1px solid #e9ecef',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: 1000,
            minWidth: '280px',
            maxWidth: '400px',
            pointerEvents: 'auto'
          }}
        >
          <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: '#2c3e50', borderBottom: '2px solid #667eea', paddingBottom: '0.5rem' }}>
            {hoveredCategory.charAt(0).toUpperCase() + hoveredCategory.slice(1)} - Top Domains
          </h3>
          
          {loadingDomains ? (
            <p style={{ textAlign: 'center', color: '#666', padding: '1rem', margin: 0 }}>Loading...</p>
          ) : categoryDomains.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {categoryDomains.map((domain, index) => (
                <li
                  key={`${domain.domain}-${index}`}
                  style={{
                    padding: '0.5rem 0.75rem',
                    background: index % 2 === 0 ? '#f8f9fa' : '#fff',
                    marginBottom: '0.25rem',
                    borderRadius: '4px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.85rem'
                  }}
                >
                  <span style={{ fontWeight: '500', color: '#2c3e50' }}>
                    {domain.domain}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: '#999' }}>
                    {domain.count} emails
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ textAlign: 'center', color: '#666', padding: '1rem', margin: 0 }}>No domains found</p>
          )}
        </div>
      )}
    </div>
  )
}

