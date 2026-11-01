"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-01
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

JSONType = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "photos",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_by", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "recipes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_alt", sa.String(200)),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("note", sa.Text()),
        sa.Column("ingredients", JSONType, nullable=False),
        sa.Column("steps", JSONType, nullable=False),
        sa.Column("plate_id", sa.String(32)),
        sa.Column("created_by", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "cook_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("recipe_id", sa.Uuid(), sa.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cooked_on", sa.Date(), nullable=False),
        sa.Column("rating", sa.Integer()),
        sa.Column("note", sa.Text()),
        sa.Column("tweaks", sa.Text()),
        sa.Column("photo_id", sa.Uuid(), sa.ForeignKey("photos.id", ondelete="SET NULL")),
        sa.Column("created_by", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cook_logs_recipe_id", "cook_logs", ["recipe_id"])
    op.create_table(
        "grocery_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("key", sa.String(200), nullable=False),
        sa.Column("base_unit", sa.String(32)),
        sa.Column("amount", sa.Float()),
        sa.Column("sources", JSONType, nullable=False),
        sa.Column("checked", sa.Boolean(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_grocery_items_key", "grocery_items", ["key"])


def downgrade() -> None:
    op.drop_table("grocery_items")
    op.drop_table("cook_logs")
    op.drop_table("recipes")
    op.drop_table("photos")
