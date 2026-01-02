"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('onboarding_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_name'), 'users', ['name'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_team_id'), 'users', ['team_id'], unique=False)

    # Create activity_events table
    op.create_table(
        'activity_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_events_id'), 'activity_events', ['id'], unique=False)
    op.create_index(op.f('ix_activity_events_occurred_at'), 'activity_events', ['occurred_at'], unique=False)
    op.create_index(op.f('ix_activity_events_source'), 'activity_events', ['source'], unique=False)
    op.create_index(op.f('ix_activity_events_user_id'), 'activity_events', ['user_id'], unique=False)
    op.create_index('idx_user_occurred_at', 'activity_events', ['user_id', 'occurred_at'], unique=False)

    # Create weekly_user_metrics table
    op.create_table(
        'weekly_user_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('tickets_completed', sa.Integer(), nullable=False),
        sa.Column('story_points', sa.Float(), nullable=False),
        sa.Column('prs_authored', sa.Integer(), nullable=False),
        sa.Column('prs_reviewed', sa.Integer(), nullable=False),
        sa.Column('commits', sa.Integer(), nullable=False),
        sa.Column('docs_authored', sa.Integer(), nullable=False),
        sa.Column('meeting_hours', sa.Float(), nullable=False),
        sa.Column('composite_score', sa.Float(), nullable=True),
        sa.Column('baseline_score', sa.Float(), nullable=True),
        sa.Column('engagement_status', sa.String(), nullable=True),
        sa.Column('flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'week_start', name='idx_user_week_start')
    )
    op.create_index(op.f('ix_weekly_user_metrics_engagement_status'), 'weekly_user_metrics', ['engagement_status'], unique=False)
    op.create_index(op.f('ix_weekly_user_metrics_id'), 'weekly_user_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_weekly_user_metrics_user_id'), 'weekly_user_metrics', ['user_id'], unique=False)
    op.create_index(op.f('ix_weekly_user_metrics_week_start'), 'weekly_user_metrics', ['week_start'], unique=False)
    op.create_index('idx_user_week_start', 'weekly_user_metrics', ['user_id', 'week_start'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_user_week_start', table_name='weekly_user_metrics')
    op.drop_index(op.f('ix_weekly_user_metrics_week_start'), table_name='weekly_user_metrics')
    op.drop_index(op.f('ix_weekly_user_metrics_user_id'), table_name='weekly_user_metrics')
    op.drop_index(op.f('ix_weekly_user_metrics_id'), table_name='weekly_user_metrics')
    op.drop_index(op.f('ix_weekly_user_metrics_engagement_status'), table_name='weekly_user_metrics')
    op.drop_table('weekly_user_metrics')
    op.drop_index('idx_user_occurred_at', table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_user_id'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_source'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_occurred_at'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_id'), table_name='activity_events')
    op.drop_table('activity_events')
    op.drop_index(op.f('ix_users_team_id'), table_name='users')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_name'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_teams_id'), table_name='teams')
    op.drop_table('teams')

