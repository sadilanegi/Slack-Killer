import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { format } from 'date-fns'
import '../styles/TrendChart.css'

/**
 * TrendChart component for displaying metrics over time
 */
function TrendChart({ data, metrics = ['composite_score'] }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        <p>No data available for this period</p>
      </div>
    )
  }

  // Format data for chart
  const chartData = data.map(item => ({
    week: format(new Date(item.week_start), 'MMM dd'),
    week_start: item.week_start,
    ...metrics.reduce((acc, metric) => {
      acc[metric] = item[metric] || 0
      return acc
    }, {})
  }))

  const colors = {
    composite_score: '#8884d8',
    baseline_score: '#82ca9d',
    tickets_completed: '#ffc658',
    prs_authored: '#ff7300',
  }

  return (
    <div className="trend-chart">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="week" />
          <YAxis />
          <Tooltip />
          <Legend />
          {metrics.map(metric => (
            <Line
              key={metric}
              type="monotone"
              dataKey={metric}
              stroke={colors[metric] || '#8884d8'}
              name={metric.replace('_', ' ')}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default TrendChart

