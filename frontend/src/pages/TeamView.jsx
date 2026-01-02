import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { apiService } from '../services/api'
import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'
import './TeamView.css'

/**
 * TeamView page - Detailed view of a team
 * Uses neutral language only
 */
function TeamView() {
  const { teamId } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [teamSummary, setTeamSummary] = useState(null)

  useEffect(() => {
    if (teamId) {
      loadTeamData()
    }
  }, [teamId])

  const loadTeamData = async () => {
    try {
      setLoading(true)
      const response = await apiService.getTeamSummary(parseInt(teamId))
      setTeamSummary(response.data)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load team data')
      console.error('TeamView error:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading team data...</div>
  }

  if (error) {
    return <div className="error">Error: {error}</div>
  }

  if (!teamSummary) {
    return <div className="empty-state">Team not found</div>
  }

  return (
    <div className="team-view">
      <div className="team-view-header">
        <Link to="/" className="back-link">← Back to Dashboard</Link>
        <h2>{teamSummary.team_name}</h2>
        <p className="team-info">
          {teamSummary.total_members} members • Average Score: {teamSummary.average_composite_score.toFixed(1)}
        </p>
      </div>

      <div className="team-summary-cards">
        <MetricCard
          title="Healthy"
          value={teamSummary.healthy_count}
          status="healthy"
        />
        <MetricCard
          title="Watch"
          value={teamSummary.watch_count}
          status="watch"
        />
        <MetricCard
          title="Needs Review"
          value={teamSummary.needs_review_count}
          status="needs_review"
        />
      </div>

      <div className="team-members-section">
        <h3>Team Members</h3>
        <div className="members-grid">
          {teamSummary.members.map(member => (
            <Link
              key={member.user_id}
              to={`/users/${member.user_id}`}
              className="member-card"
            >
              <div className="member-card-header">
                <h4>{member.user_name}</h4>
                <StatusBadge status={member.engagement_status} />
              </div>
              <div className="member-card-body">
                <div className="member-metrics">
                  <div className="member-metric">
                    <span className="metric-label">Role:</span>
                    <span className="metric-value-small">{member.user_role}</span>
                  </div>
                  <div className="member-metric">
                    <span className="metric-label">Score:</span>
                    <span className="metric-value-small">
                      {member.current_week.composite_score?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                  <div className="member-metric">
                    <span className="metric-label">Trend:</span>
                    <span className={`metric-value-small trend-${member.trend}`}>
                      {member.trend}
                    </span>
                  </div>
                </div>
                <div className="member-activity">
                  <div className="activity-item">
                    <span>Tickets: {member.current_week.tickets_completed}</span>
                  </div>
                  <div className="activity-item">
                    <span>PRs: {member.current_week.prs_authored}</span>
                  </div>
                  <div className="activity-item">
                    <span>Reviews: {member.current_week.prs_reviewed}</span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TeamView

