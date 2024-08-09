"""Create tables

Revision ID: 51eefefc3d8c
Revises: 
Create Date: 2024-08-08 20:13:52.946655

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "51eefefc3d8c"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_cap_table",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("currency", sa.String(length=15), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "performance_data_table",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("five_days", sa.Float(), nullable=True),
        sa.Column("one_month", sa.Float(), nullable=True),
        sa.Column("three_months", sa.Float(), nullable=True),
        sa.Column("year_to_date", sa.Float(), nullable=True),
        sa.Column("one_year", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stock_values_table",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("open", sa.Float(), nullable=True),
        sa.Column("high", sa.Float(), nullable=True),
        sa.Column("low", sa.Float(), nullable=True),
        sa.Column("close", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stock_table",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("status", sa.String(length=15), nullable=True),
        sa.Column("purchased_amount", sa.Integer(), nullable=True),
        sa.Column("purchased_status", sa.String(length=15), nullable=True),
        sa.Column("request_data", sa.Date(), nullable=True),
        sa.Column("company_code", sa.String(length=15), nullable=True),
        sa.Column("company_name", sa.String(length=30), nullable=True),
        sa.Column("stock_values_id", sa.Integer(), nullable=False),
        sa.Column("performance_data_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["performance_data_id"],
            ["performance_data_table.id"],
        ),
        sa.ForeignKeyConstraint(
            ["stock_values_id"],
            ["stock_values_table.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_code"),
    )
    op.create_index(
        op.f("ix_stock_table_performance_data_id"),
        "stock_table",
        ["performance_data_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stock_table_stock_values_id"),
        "stock_table",
        ["stock_values_id"],
        unique=False,
    )
    op.create_table(
        "competitor_table",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=30), nullable=True),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("market_cap_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["market_cap_id"],
            ["market_cap_table.id"],
        ),
        sa.ForeignKeyConstraint(
            ["stock_id"],
            ["stock_table.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_competitor_table_market_cap_id"),
        "competitor_table",
        ["market_cap_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_competitor_table_stock_id"),
        "competitor_table",
        ["stock_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_competitor_table_stock_id"), table_name="competitor_table")
    op.drop_index(
        op.f("ix_competitor_table_market_cap_id"), table_name="competitor_table"
    )
    op.drop_table("competitor_table")
    op.drop_index(op.f("ix_stock_table_stock_values_id"), table_name="stock_table")
    op.drop_index(op.f("ix_stock_table_performance_data_id"), table_name="stock_table")
    op.drop_table("stock_table")
    op.drop_table("stock_values_table")
    op.drop_table("performance_data_table")
    op.drop_table("market_cap_table")
