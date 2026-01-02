import React from 'react'
import '../styles/StatusBadge.css'

/**
 * StatusBadge component for displaying engagement status
 * Uses neutral language: healthy, watch, needs_review
 */
function StatusBadge({ status, showLabel = true }) {
  const getStatusInfo = () => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return {
          class: 'status-healthy',
          label: 'Healthy',
          description: 'Activity levels are within expected range'
        }
      case 'watch':
        return {
          class: 'status-watch',
          label: 'Watch',
          description: 'This signal indicates reduced activity and may require a manager check-in.'
        }
      case 'needs_review':
        return {
          class: 'status-needs-review',
          label: 'Needs Review',
          description: 'Sustained low activity detected. Manager review recommended.'
        }
      default:
        return {
          class: 'status-unknown',
          label: 'Unknown',
          description: 'Status not available'
        }
    }
  }

  const statusInfo = getStatusInfo()

  return (
    <div className={`status-badge ${statusInfo.class}`}>
      <span className="status-indicator"></span>
      {showLabel && <span className="status-label">{statusInfo.label}</span>}
      {statusInfo.description && (
        <span className="status-description" title={statusInfo.description}>
          ℹ️
        </span>
      )}
    </div>
  )
}

export default StatusBadge

