# Engineer Productivity Analyzer

A production-ready system for analyzing engineering productivity using Jira tickets, Git PRs & commits, and documentation activity. The goal is to detect low engagement patterns and provide actionable insights to team leads — **not to punish engineers**.

## Features

- **Multi-source data ingestion**: Jira, GitHub, documentation, and calendar events
- **Role-based normalization**: Metrics are normalized by role (backend, frontend, devops, manager)
- **Engagement detection**: Identifies patterns that may need manager attention using neutral language (healthy, watch, needs_review)
- **RBAC**: Role-based access control (Engineer → self only, Manager → team, Admin → all)
- **Weekly aggregation**: Automatic background jobs for metrics calculation
- **Modern UI**: React-based dashboard with charts and detailed views

## Architecture

- **Backend**: FastAPI (Python) with PostgreSQL
- **Frontend**: React with Vite
- **Database**: PostgreSQL (RDS compatible, NO TimescaleDB)
- **Authentication**: JWT-based

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Jira API access (optional)
- GitHub API token (optional)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**:
   ```bash
   # Create PostgreSQL database
   createdb productivity_db

   # Run migrations
   alembic upgrade head
   ```

6. **Run the backend**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. **Run background worker** (in separate terminal):
   ```bash
   python -m app.workers.aggregation_job
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables** (optional):
   ```bash
   # Create .env file if needed
   VITE_API_URL=http://localhost:8000/api
   ```

4. **Run the frontend**:
   ```bash
   npm run dev
   ```

5. **Access the application**:
   Open http://localhost:3000 in your browser

## Database Schema

### Tables

- **users**: Engineers, managers, and admins
- **teams**: Team groupings
- **activity_events**: Individual activities from various sources
- **weekly_user_metrics**: Aggregated weekly metrics per user

### Key Indexes

- `(user_id, occurred_at)` on `activity_events`
- `(user_id, week_start)` on `weekly_user_metrics`
- `week_start` on `weekly_user_metrics`

## API Endpoints

### Authentication
- `POST /api/token` - Get JWT token (implement as needed)

### Users
- `GET /api/users/me` - Get current user
- `GET /api/users/{user_id}` - Get user by ID
- `GET /api/users/` - List users (filtered by permissions)

### Metrics
- `GET /api/metrics/users/{user_id}` - Get user metrics summary
- `GET /api/metrics/users/{user_id}/weekly` - Get weekly metrics over date range

### Reports
- `GET /api/reports/teams/{team_id}/summary` - Get team summary
- `GET /api/reports/weekly` - Get weekly report for all teams
- `POST /api/reports/overrides` - Create engagement status override

## Engagement Detection Rules

The system detects low engagement using these rules:

1. **Below threshold for N weeks**: Composite score below 30% of baseline for 2+ weeks (watch) or 3+ weeks (needs_review)
2. **Sudden drop**: >40% drop vs baseline in a single week
3. **Low collaboration**: Authored PRs but no reviews over multiple weeks
4. **Sustained inactivity**: All metrics near zero for 2+ weeks

### Exceptions

The system automatically accounts for:
- PTO (paid time off)
- Onboarding period
- Role changes (2-week grace period)
- On-call duty

## Ethics & Safety

This system is designed with ethics in mind:

- ✅ **No ranking leaderboards**: Users are not ranked against each other
- ✅ **No public comparison**: Data is only visible to authorized users
- ✅ **No "worst performer" UI**: Neutral language only (healthy, watch, needs_review)
- ✅ **Context always shown**: PTO, onboarding, and other flags are displayed
- ✅ **Manager-focused**: Insights are for team leads, not for punishment

## Configuration

### Metrics Weights

Role-based weights for composite score calculation can be configured in `app/core/config.py`:

```python
COMPOSITE_SCORE_WEIGHTS = {
    "backend": {
        "tickets": 0.25,
        "story_points": 0.20,
        "prs_authored": 0.15,
        "prs_reviewed": 0.15,
        "commits": 0.10,
        "docs": 0.10,
        "meetings": 0.05
    },
    # ... other roles
}
```

### Engagement Thresholds

- `LOW_ENGAGEMENT_THRESHOLD`: 0.3 (30% below baseline)
- `SUDDEN_DROP_THRESHOLD`: 0.4 (40% drop)
- `WATCH_WEEKS`: 2
- `NEEDS_REVIEW_WEEKS`: 3

## Development

### Running Tests

```bash
# Backend tests (add when implemented)
pytest

# Frontend tests (add when implemented)
npm test
```

### Code Style

- Backend: Follow PEP 8
- Frontend: ESLint with React rules

## Production Deployment

### Backend

1. Use a production WSGI server (e.g., Gunicorn with Uvicorn workers)
2. Set up proper environment variables
3. Use a managed PostgreSQL database (AWS RDS)
4. Set up background worker as a systemd service or container

### Frontend

1. Build for production:
   ```bash
   npm run build
   ```
2. Serve static files with nginx or similar
3. Configure API URL for production

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues or questions, please [create an issue](link-to-issues).

