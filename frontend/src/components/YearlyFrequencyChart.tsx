import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
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

  // Prepare monthly distribution data for all years
  const monthlyData: Array<{ month: string; [key: string]: string | number }> = []
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  
  for (let month = 1; month <= 12; month++) {
    const monthData: { month: string; [key: string]: string | number } = {
      month: monthNames[month - 1]
    }
    insights.years.forEach(year => {
      monthData[year.toString()] = insights.yearly_stats[year]?.monthly_distribution[month] || 0
    })
    monthlyData.push(monthData)
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Year-over-Year Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={yearOverYearData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="total" stroke="#667eea" name="Total Emails" strokeWidth={2} />
            <Line type="monotone" dataKey="dailyAvg" stroke="#764ba2" name="Daily Average" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
        
        <div style={{ marginTop: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: '0.5rem', textAlign: 'left' }}>Year</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Total Emails</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Daily Avg</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Change</th>
              </tr>
            </thead>
            <tbody>
              {insights.year_over_year.map(yoy => (
                <tr key={yoy.year} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '0.5rem', fontWeight: '500' }}>{yoy.year}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right' }}>{yoy.total_emails.toLocaleString()}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right' }}>{yoy.daily_average.toFixed(2)}</td>
                  <td style={{ 
                    padding: '0.5rem', 
                    textAlign: 'right',
                    color: yoy.change_from_previous && yoy.change_from_previous > 0 ? '#28a745' : yoy.change_from_previous && yoy.change_from_previous < 0 ? '#dc3545' : '#666'
                  }}>
                    {yoy.change_from_previous !== null ? (
                      <>
                        {yoy.change_from_previous > 0 ? '+' : ''}{yoy.change_from_previous.toLocaleString()}
                        {yoy.change_percent !== null && (
                          <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem' }}>
                            ({yoy.change_percent > 0 ? '+' : ''}{yoy.change_percent}%)
                          </span>
                        )}
                      </>
                    ) : (
                      '-'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {insights.years.length > 0 && (
        <div>
          <h3 style={{ marginBottom: '1rem' }}>Monthly Distribution by Year</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              {insights.years.map((year, index) => {
                const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe']
                return (
                  <Bar 
                    key={year} 
                    dataKey={year.toString()} 
                    fill={colors[index % colors.length]}
                    name={`${year}`}
                  />
                )
              })}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

