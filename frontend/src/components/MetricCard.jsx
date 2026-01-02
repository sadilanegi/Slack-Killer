import React from 'react'
import '../styles/MetricCard.css'

/**
 * MetricCard component for displaying individual metrics
 * Uses neutral language only
 */
function MetricCard({ title, value, unit = '', trend = null, status = null }) {
  const getStatusClass = () => {
    if (!status) return ''
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'status-healthy'
      case 'watch':
        return 'status-watch'
      case 'needs_review':
        return 'status-needs-review'
      default:
        return ''
    }
  }

  const getTrendIcon = () => {
    if (!trend) return null
    switch (trend.toLowerCase()) {
      case 'improving':
        return '↑'
      case 'declining':
        return '↓'
      case 'stable':
        return '→'
      default:
        return null
    }
  }

  return (
    <div className={`metric-card ${getStatusClass()}`}>
      <div className="metric-header">
        <h3 className="metric-title">{title}</h3>
        {trend && (
          <span className={`metric-trend trend-${trend.toLowerCase()}`}>
            {getTrendIcon()}
          </span>
        )}
      </div>
      <div className="metric-value">
        {value}
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
      {status && status !== 'healthy' && (
        <div className="metric-status">
          Status: {status.replace('_', ' ')}
        </div>
      )}
    </div>
  )
}

export default MetricCard

