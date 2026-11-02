"""photo framing on cook logs

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-02
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cook_logs", sa.Column("photo_crop", sa.JSON().with_variant(postgresql.JSONB(), "postgresql")))


def downgrade() -> None:
    op.drop_column("cook_logs", "photo_crop")
