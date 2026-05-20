"""
olap/build_olap.py
==================
Orchestrator script that builds (or rebuilds) all OLAP aggregation
tables and data marts from the existing warehouse fact + dimension tables.

Usage (from project root):
    uv run python -m olap.build_olap
    # or
    python olap/build_olap.py

Environment:
    DATABASE_URL must be set in .env (e.g. postgresql://user:pw@host/dbname)
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from dotenv import load_dotenv

from olap.ddl import OLAP_TABLES

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL: str = os.environ.get("DATABASE_URL", "")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_engine() -> sa.Engine:
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set.\n"
            "Add it to your .env file:\n"
            "  DATABASE_URL=postgresql://user:password@localhost:5432/warehouse"
        )
    return sa.create_engine(DATABASE_URL, echo=False)


def _table_exists(conn: sa.Connection, table_name: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables"
            "  WHERE table_schema = 'public' AND table_name = :name"
            ")"
        ),
        {"name": table_name},
    )
    return bool(result.scalar())


def _drop_table(conn: sa.Connection, table_name: str) -> None:
    conn.execute(sa.text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))


def _row_count(conn: sa.Connection, table_name: str) -> int:
    result = conn.execute(sa.text(f'SELECT COUNT(*) FROM "{table_name}"'))
    return result.scalar() or 0


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_all(engine: sa.Engine | None = None) -> dict[str, int]:
    """
    Drop and recreate all OLAP tables in dependency order.
    Returns a mapping of table_name → row_count for reporting.
    """
    if engine is None:
        engine = _get_engine()

    summary: dict[str, int] = {}

    with engine.begin() as conn:
        print(f"\n{'='*60}")
        print(f"  OLAP Build — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        for table_name, create_ddl, index_ddls in OLAP_TABLES:
            t0 = time.perf_counter()

            # Drop existing
            _drop_table(conn, table_name)

            # Create + populate via CTAS
            conn.execute(sa.text(create_ddl))

            # Create indexes
            for idx_ddl in index_ddls:
                conn.execute(sa.text(idx_ddl))

            rows = _row_count(conn, table_name)
            elapsed = time.perf_counter() - t0
            summary[table_name] = rows

            status = "✓" if rows > 0 else "⚠ 0 rows"
            print(f"  {status}  {table_name:<40}  {rows:>7,} rows  ({elapsed:.2f}s)")

    print(f"{'='*60}")
    print(f"  Build complete — {len(OLAP_TABLES)} tables built.\n")
    return summary


# ---------------------------------------------------------------------------
# Data Quality Validation
# ---------------------------------------------------------------------------

DQ_CHECKS: list[tuple[str, str]] = [
    (
        "DQ-1: Sales Revenue match (fact vs agg)",
        """
        SELECT ABS(
            (SELECT COALESCE(SUM(net_amount), 0)        FROM fact_sales) -
            (SELECT COALESCE(SUM(revenue), 0)           FROM agg_sales_daily_v1)
        ) < 0.01 AS passed
        """,
    ),
    (
        "DQ-2: Production cost match (fact vs agg)",
        """
        SELECT ABS(
            (SELECT COALESCE(SUM(total_production_cost), 0) FROM fact_production) -
            (SELECT COALESCE(SUM(total_cost), 0)            FROM agg_production_daily_v1)
        ) < 0.01 AS passed
        """,
    ),
    (
        "DQ-3: No null revenue in agg_sales_daily_v1",
        """
        SELECT COUNT(*) FILTER (WHERE revenue IS NULL) = 0 AS passed
        FROM agg_sales_daily_v1
        """,
    ),
    (
        "DQ-4: Inventory snapshot has rows",
        """
        SELECT (SELECT COUNT(*) FROM agg_inventory_snapshot_v1) > 0 AS passed
        """,
    ),
    (
        "DQ-5: OTD % plausibility (0–100)",
        """
        SELECT (MIN(on_time_pct) >= 0 AND MAX(on_time_pct) <= 100) AS passed
        FROM agg_shipment_daily_v1
        """,
    ),
    (
        "DQ-6: mart_sales_v1 row count equals fact_sales",
        """
        SELECT (
            (SELECT COUNT(*) FROM mart_sales_v1) =
            (SELECT COUNT(*) FROM fact_sales)
        ) AS passed
        """,
    ),
    (
        "DQ-7: mart_integrated_kpi_v1 has rows",
        """
        SELECT (SELECT COUNT(*) FROM mart_integrated_kpi_v1) > 0 AS passed
        """,
    ),
    (
        "DQ-8: Production yield in valid range (0–1)",
        """
        SELECT (
            MIN(avg_yield_pct) >= 0 AND MAX(avg_yield_pct) <= 1
        ) AS passed
        FROM agg_production_daily_v1
        """,
    ),
]


def validate_all(engine: sa.Engine | None = None) -> bool:
    """
    Run all data quality checks.  Returns True if all pass, False otherwise.
    """
    if engine is None:
        engine = _get_engine()

    all_passed = True

    print(f"\n{'='*60}")
    print(f"  Data Quality Validation — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    with engine.connect() as conn:
        for check_name, query in DQ_CHECKS:
            try:
                result = conn.execute(sa.text(query))
                passed = bool(result.scalar())
                icon = "✓ PASS" if passed else "✗ FAIL"
                if not passed:
                    all_passed = False
                print(f"  {icon}  {check_name}")
            except Exception as exc:  # noqa: BLE001
                print(f"  ✗ ERR  {check_name}")
                print(f"         → {exc}")
                all_passed = False

    print(f"{'='*60}")
    overall = "ALL CHECKS PASSED ✓" if all_passed else "SOME CHECKS FAILED ✗"
    print(f"  Result: {overall}\n")
    return all_passed


# ---------------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------------

def print_build_report(summary: dict[str, int]) -> None:
    """Print a formatted summary of the OLAP build."""
    agg_tables   = {k: v for k, v in summary.items() if k.startswith("agg_")}
    mart_tables  = {k: v for k, v in summary.items() if k.startswith("mart_")}

    print(f"\n{'='*60}")
    print("  OLAP Build Report")
    print(f"{'='*60}")
    print(f"\n  Aggregation Tables ({len(agg_tables)}):")
    for name, rows in agg_tables.items():
        print(f"    {name:<42}  {rows:>7,} rows")
    print(f"\n  Data Marts ({len(mart_tables)}):")
    for name, rows in mart_tables.items():
        print(f"    {name:<42}  {rows:>7,} rows")
    total_rows = sum(summary.values())
    print(f"\n  Total rows across all OLAP tables: {total_rows:,}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        engine = _get_engine()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    summary = build_all(engine)
    print_build_report(summary)
    ok = validate_all(engine)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
