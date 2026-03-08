import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { YearlyFrequencyInsights } from '../api/client'

interface YearlyFrequencyChartProps {
  insights: YearlyFrequencyInsights
}

export default function YearlyFrequencyChart({ insights }: YearlyFrequencyChartProps) {
  // Prepare data for year-over-year comparison
  const yearOverYearData = insights.year_over_year.map(yoy => ({
    year: yoy.year.toString(),
    total: yoy.total_emails,
    dailyAvg: yoy.daily_average,
    change: yoy.change_from_previous,
    changePercent: yoy.change_percent
  }))

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: 'white',
          padding: '12px',
          border: '1px solid #ccc',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 600, color: '#2c3e50' }}>Year {label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ margin: '4px 0', fontSize: '0.9rem', color: entry.color }}>
              {entry.name}: <strong>{entry.value.toLocaleString()}</strong>
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div>
      <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #e9ecef' }}>
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#666' }}>
          📈 Year-over-year email volume trends
        </p>
      </div>
      <div style={{ marginBottom: '2rem' }}>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={yearOverYearData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <defs>
              <linearGradient id="totalGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#667eea" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#667eea" stopOpacity={0.1}/>
              </linearGradient>
              <linearGradient id="avgGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#764ba2" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#764ba2" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis 
              dataKey="year" 
              tick={{ fontSize: 12, fill: '#666' }}
            />
            <YAxis 
              tick={{ fontSize: 12, fill: '#666' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Area 
              type="monotone" 
              dataKey="total" 
              stroke="#667eea" 
              strokeWidth={2}
              fill="url(#totalGradient)"
              name="Total Emails"
              dot={false}
              activeDot={{ r: 5, fill: '#667eea' }}
            />
            <Area 
              type="monotone" 
              dataKey="dailyAvg" 
              stroke="#764ba2" 
              strokeWidth={2}
              fill="url(#avgGradient)"
              name="Daily Average"
              dot={false}
              activeDot={{ r: 5, fill: '#764ba2' }}
            />
          </AreaChart>
        </ResponsiveContainer>
        
        <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e9ecef' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e0e0e0', backgroundColor: '#f8f9fa' }}>
                <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 600, color: '#2c3e50' }}>Year</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600, color: '#2c3e50' }}>Total Emails</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600, color: '#2c3e50' }}>Daily Avg</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600, color: '#2c3e50' }}>Change</th>
              </tr>
            </thead>
            <tbody>
              {insights.year_over_year.map((yoy, index) => (
                <tr 
                  key={yoy.year} 
                  style={{ 
                    borderBottom: '1px solid #f0f0f0',
                    backgroundColor: index % 2 === 0 ? '#fff' : '#fafafa'
                  }}
                >
                  <td style={{ padding: '0.75rem', fontWeight: '600', color: '#667eea' }}>{yoy.year}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'right', color: '#2c3e50' }}>{yoy.total_emails.toLocaleString()}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'right', color: '#2c3e50' }}>{yoy.daily_average.toFixed(2)}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: '600' }}>
                    {yoy.change_from_previous !== null ? (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        backgroundColor: yoy.change_from_previous > 0 ? '#d4edda' : yoy.change_from_previous < 0 ? '#f8d7da' : '#e9ecef',
                        color: yoy.change_from_previous > 0 ? '#155724' : yoy.change_from_previous < 0 ? '#721c24' : '#666'
                      }}>
                        {yoy.change_from_previous > 0 ? '↑' : yoy.change_from_previous < 0 ? '↓' : '→'}
                        {yoy.change_from_previous > 0 ? '+' : ''}{yoy.change_from_previous.toLocaleString()}
                        {yoy.change_percent !== null && (
                          <span style={{ fontSize: '0.85rem' }}>
                            ({yoy.change_percent > 0 ? '+' : ''}{yoy.change_percent}%)
                          </span>
                        )}
                      </span>
                    ) : (
                      <span style={{ color: '#999' }}>-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}

