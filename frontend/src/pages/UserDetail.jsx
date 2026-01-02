import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { apiService } from '../services/api'
import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'
import TrendChart from '../components/TrendChart'
import './UserDetail.css'

/**
 * UserDetail page - Detailed view of individual user metrics
 * Uses neutral language only
 */
function UserDetail() {
  const { userId } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userMetrics, setUserMetrics] = useState(null)

  useEffect(() => {
    if (userId) {
      loadUserData()
    }
  }, [userId])

  const loadUserData = async () => {
    try {
      setLoading(true)
      const response = await apiService.getUserMetrics(parseInt(userId), 12)
      setUserMetrics(response.data)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load user data')
      console.error('UserDetail error:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading user data...</div>
  }

  if (error) {
    return <div className="error">Error: {error}</div>
  }

  if (!userMetrics) {
    return <div className="empty-state">User not found</div>
  }

  const currentWeek = userMetrics.current_week
  const allWeeks = [currentWeek, ...userMetrics.previous_weeks]

  return (
    <div className="user-detail">
      <div className="user-detail-header">
        <Link to="/" className="back-link">← Back to Dashboard</Link>
        <div className="user-info">
          <h2>{userMetrics.user_name}</h2>
          <p className="user-role">{userMetrics.user_role}</p>
          <StatusBadge status={userMetrics.engagement_status} />
        </div>
      </div>

      {userMetrics.engagement_status !== 'healthy' && (
        <div className="engagement-notice">
          <p>
            <strong>Engagement Notice:</strong> This signal indicates reduced activity and may require a manager check-in.
            {currentWeek.flags && (
              <span className="context-info">
                {' '}Context: {JSON.stringify(currentWeek.flags, null, 2)}
              </span>
            )}
          </p>
        </div>
      )}

      <div className="user-metrics-grid">
        <MetricCard
          title="Composite Score"
          value={currentWeek.composite_score?.toFixed(1) || 'N/A'}
          trend={userMetrics.trend}
          status={userMetrics.engagement_status}
        />
        <MetricCard
          title="Baseline Score"
          value={currentWeek.baseline_score?.toFixed(1) || 'N/A'}
        />
        <MetricCard
          title="Tickets Completed"
          value={currentWeek.tickets_completed}
        />
        <MetricCard
          title="Story Points"
          value={currentWeek.story_points?.toFixed(1) || '0'}
        />
        <MetricCard
          title="PRs Authored"
          value={currentWeek.prs_authored}
        />
        <MetricCard
          title="PRs Reviewed"
          value={currentWeek.prs_reviewed}
        />
        <MetricCard
          title="Commits"
          value={currentWeek.commits}
        />
        <MetricCard
          title="Docs Authored"
          value={currentWeek.docs_authored}
        />
        <MetricCard
          title="Meeting Hours"
          value={currentWeek.meeting_hours?.toFixed(1) || '0'}
          unit="hrs"
        />
      </div>

      <div className="user-trends-section">
        <h3>Trends Over Time</h3>
        <TrendChart
          data={allWeeks}
          metrics={['composite_score', 'baseline_score']}
        />
      </div>

      <div className="user-activity-breakdown">
        <h3>Activity Breakdown</h3>
        <TrendChart
          data={allWeeks}
          metrics={['tickets_completed', 'prs_authored', 'prs_reviewed', 'commits']}
        />
      </div>

      <div className="user-context-section">
        <h3>Context & Flags</h3>
        {currentWeek.flags ? (
          <div className="context-display">
            <pre>{JSON.stringify(currentWeek.flags, null, 2)}</pre>
            <p className="context-note">
              Flags may include: PTO, onboarding, role changes, on-call duty, or manual overrides.
            </p>
          </div>
        ) : (
          <p className="no-context">No special context flags for this week.</p>
        )}
      </div>
    </div>
  )
}

export default UserDetail

