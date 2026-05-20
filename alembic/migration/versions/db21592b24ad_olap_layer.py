"""olap_layer

Revision ID: db21592b24ad
Revises: 8a2cee70598a
Create Date: 2026-05-21 02:43:56.613764

Creates the complete OLAP aggregation layer and data mart tables on top of
the existing warehouse schema (dim_* + fact_* tables).

Tables created (in dependency order):
  Aggregation:
    agg_sales_daily_v1, agg_sales_monthly_v1
    agg_production_daily_v1, agg_production_plant_v1
    agg_inventory_snapshot_v1, agg_inventory_weekly_v1
    agg_shipment_daily_v1
  Data Marts:
    mart_sales_v1, mart_production_v1, mart_inventory_v1,
    mart_logistics_v1, mart_integrated_kpi_v1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db21592b24ad'
down_revision: Union[str, None] = '8a2cee70598a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Ordered list of (table_name, create_sql, [index_sqls])
# Import from ddl module at runtime to keep migration self-contained
# ---------------------------------------------------------------------------

def _get_olap_tables():
    """Import OLAP_TABLES lazily to avoid import issues during alembic ops."""
    import sys, os
    # Ensure project root is on path
    project_root = str(op.get_bind().engine.url)  # noqa: just for path resolution trick
    # Use direct import since alembic runs from project root
    from olap.ddl import OLAP_TABLES
    return OLAP_TABLES


def upgrade() -> None:
    from olap.ddl import OLAP_TABLES

    for table_name, create_ddl, index_ddls in OLAP_TABLES:
        # Drop if exists (idempotent)
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
        # Create + populate via CTAS
        op.execute(sa.text(create_ddl))
        # Create indexes
        for idx_ddl in index_ddls:
            op.execute(sa.text(idx_ddl))


def downgrade() -> None:
    # Drop in reverse order (marts first, then aggregations)
    olap_table_names = [
        "mart_integrated_kpi_v1",
        "mart_logistics_v1",
        "mart_inventory_v1",
        "mart_production_v1",
        "mart_sales_v1",
        "agg_shipment_daily_v1",
        "agg_inventory_weekly_v1",
        "agg_inventory_snapshot_v1",
        "agg_production_plant_v1",
        "agg_production_daily_v1",
        "agg_sales_monthly_v1",
        "agg_sales_daily_v1",
    ]
    for table_name in olap_table_names:
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
