"""add query indexes

Revision ID: d8e7f6a5b4c3
Revises: b39140e0fe8e
Create Date: 2026-08-26
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "d8e7f6a5b4c3"
down_revision = "b39140e0fe8e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("request_id", sa.String(length=64), nullable=True))
    op.create_index("ix_jobs_request_id", "jobs", ["request_id"], unique=True)
    op.create_index("ix_jobs_requested_at", "jobs", ["requested_at"])
    op.create_index(
        "ix_host_metrics_host_collected_at",
        "host_metrics",
        ["host_id", "collected_at"],
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_host_metrics_host_collected_at", table_name="host_metrics")
    op.drop_index("ix_jobs_requested_at", table_name="jobs")
    op.drop_index("ix_jobs_request_id", table_name="jobs")
    op.drop_column("jobs", "request_id")
