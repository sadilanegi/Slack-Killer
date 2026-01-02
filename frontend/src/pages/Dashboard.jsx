import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { apiService } from '../services/api'
import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'
import './Dashboard.css'

/**
 * Dashboard page - Overview of all teams and users
 * Uses neutral language only
 */
function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [weeklyReport, setWeeklyReport] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const response = await apiService.getWeeklyReport()
      setWeeklyReport(response.data)
      setError(null)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load dashboard data'
      setError(errorMessage)
      console.error('Dashboard error:', err)
      
      // If it's a network error, provide helpful message
      if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        setError('Cannot connect to backend. Please ensure the backend server is running on http://localhost:8000')
      }
    } finally {
      setLoading(false)
    }
  }

  const exportToCSV = () => {
    if (!weeklyReport) return

    // Simple CSV export
    const csv = [
      ['Week Start', 'Team', 'User', 'Status', 'Composite Score', 'Tickets', 'PRs Authored', 'PRs Reviewed'],
      ...weeklyReport.teams.flatMap(team =>
        team.members.map(member => [
          weeklyReport.week_start,
          team.team_name,
          member.user_name,
          member.engagement_status,
          member.current_week.composite_score || 0,
          member.current_week.tickets_completed,
          member.current_week.prs_authored,
          member.current_week.prs_reviewed,
        ])
      )
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `productivity-report-${weeklyReport.week_start}.csv`
    a.click()
  }

  if (loading) {
    return <div className="loading">Loading dashboard...</div>
  }

  if (error) {
    return (
      <div className="error">
        <h3>Error Loading Dashboard</h3>
        <p>{error}</p>
        <div style={{ marginTop: '1rem' }}>
          <p><strong>Troubleshooting:</strong></p>
          <ul style={{ marginLeft: '1.5rem', marginTop: '0.5rem' }}>
            <li>Ensure the backend server is running: <code>uvicorn app.main:app --reload</code></li>
            <li>Check that the backend is accessible at <code>http://localhost:8000</code></li>
            <li>Verify CORS settings in backend configuration</li>
            <li>Check browser console for detailed error messages</li>
          </ul>
        </div>
      </div>
    )
  }

  if (!weeklyReport) {
    return <div className="empty-state">No data available</div>
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h2>Team Productivity Overview</h2>
          <p className="week-info">
            Week of {new Date(weeklyReport.week_start).toLocaleDateString()}
          </p>
        </div>
        <div className="dashboard-actions">
          <button onClick={exportToCSV} className="btn-export">
            Export CSV
          </button>
        </div>
      </div>

      <div className="dashboard-summary">
        <MetricCard
          title="Total Users"
          value={weeklyReport.total_users}
          status="healthy"
        />
        <MetricCard
          title="Healthy"
          value={weeklyReport.healthy_users}
          status="healthy"
        />
        <MetricCard
          title="Watch"
          value={weeklyReport.watch_users}
          status="watch"
        />
        <MetricCard
          title="Needs Review"
          value={weeklyReport.needs_review_users}
          status="needs_review"
        />
      </div>

      <div className="teams-section">
        <h3>Teams</h3>
        {weeklyReport.teams.map(team => (
          <div key={team.team_id} className="team-card">
            <div className="team-header">
              <Link to={`/teams/${team.team_id}`}>
                <h4>{team.team_name}</h4>
              </Link>
              <div className="team-stats">
                <span>{team.total_members} members</span>
                <span>Avg Score: {team.average_composite_score.toFixed(1)}</span>
              </div>
            </div>
            <div className="team-status-breakdown">
              <StatusBadge status="healthy" />
              <span>{team.healthy_count}</span>
              <StatusBadge status="watch" />
              <span>{team.watch_count}</span>
              <StatusBadge status="needs_review" />
              <span>{team.needs_review_count}</span>
            </div>
            <div className="team-members-preview">
              {team.members.slice(0, 5).map(member => (
                <Link
                  key={member.user_id}
                  to={`/users/${member.user_id}`}
                  className="member-preview"
                >
                  <span className="member-name">{member.user_name}</span>
                  <StatusBadge status={member.engagement_status} />
                </Link>
              ))}
              {team.members.length > 5 && (
                <span className="more-members">
                  +{team.members.length - 5} more
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-footer">
        <p className="disclaimer">
          <strong>Note:</strong> This signal indicates reduced activity and may require a manager check-in.
          Always consider context such as PTO, onboarding, role changes, or on-call duty.
        </p>
      </div>
    </div>
  )
}

export default Dashboard

