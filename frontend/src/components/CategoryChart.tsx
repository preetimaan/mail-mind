import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { CategoryInsights } from '../api/client'

interface CategoryChartProps {
  insights: CategoryInsights
}

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b', '#fa709a']

export default function CategoryChart({ insights }: CategoryChartProps) {
  const data = insights.categories.map((cat) => ({
    name: cat.category.charAt(0).toUpperCase() + cat.category.slice(1),
    value: cat.count,
    percentage: cat.percentage,
    category: cat.category,
  }))

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
          📊 Distribution of emails by category
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
    </div>
  )
}

