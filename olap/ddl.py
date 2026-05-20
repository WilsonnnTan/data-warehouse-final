"""
olap/ddl.py
===========
DDL constants for all OLAP aggregation tables and data marts.

Naming convention:
  agg_{subject}_{grain}_v{version}  — pre-aggregated summary tables
  mart_{subject}_v{version}         — wide, denormalized data marts

All tables are built by olap/build_olap.py (DROP + CREATE + INSERT approach
so they stay fully refreshable without incremental complexity).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. SALES — Aggregation tables
# ---------------------------------------------------------------------------

DDL_AGG_SALES_DAILY = """
CREATE TABLE agg_sales_daily_v1 AS
SELECT
    f.time_id,
    f.product_id,
    f.customer_id,
    f.region_id,
    f.segment_id,
    f.employee_id,
    f.warehouse_id,

    -- Core measures
    SUM(f.quantity_ordered)                                     AS qty_sold,
    SUM(f.net_amount)                                           AS revenue,
    SUM(f.quantity_ordered * f.unit_price)                      AS gross_amount,
    AVG(f.gross_margin_pct)                                     AS avg_margin_pct,
    COUNT(f.sales_fact_id)                                      AS line_count,

    -- Derived
    SUM(f.net_amount) / NULLIF(COUNT(f.sales_fact_id), 0)       AS avg_line_value,

    CURRENT_TIMESTAMP                                           AS created_at

FROM fact_sales f
GROUP BY
    f.time_id, f.product_id, f.customer_id,
    f.region_id, f.segment_id, f.employee_id, f.warehouse_id;
"""

IDX_AGG_SALES_DAILY = [
    "CREATE INDEX idx_asd_time     ON agg_sales_daily_v1(time_id);",
    "CREATE INDEX idx_asd_product  ON agg_sales_daily_v1(product_id);",
    "CREATE INDEX idx_asd_customer ON agg_sales_daily_v1(customer_id);",
    "CREATE INDEX idx_asd_region   ON agg_sales_daily_v1(region_id);",
    "CREATE INDEX idx_asd_segment  ON agg_sales_daily_v1(segment_id);",
    "CREATE INDEX idx_asd_employee ON agg_sales_daily_v1(employee_id);",
]

DDL_AGG_SALES_MONTHLY = """
CREATE TABLE agg_sales_monthly_v1 AS
SELECT
    TO_CHAR(t.full_date, 'YYYYMM')      AS year_month,
    d.region_id,
    d.segment_id,
    d.employee_id,

    SUM(d.revenue)                       AS total_revenue,
    SUM(d.qty_sold)                      AS total_qty,
    AVG(d.avg_margin_pct)                AS avg_margin_pct,
    SUM(d.line_count)                    AS total_order_lines,
    COUNT(DISTINCT d.customer_id)        AS unique_customers,
    SUM(d.revenue) / NULLIF(SUM(d.line_count), 0) AS avg_order_line_value,

    CURRENT_TIMESTAMP                    AS created_at

FROM agg_sales_daily_v1 d
JOIN dim_time t ON d.time_id = t.time_id
GROUP BY
    TO_CHAR(t.full_date, 'YYYYMM'),
    d.region_id, d.segment_id, d.employee_id;
"""

IDX_AGG_SALES_MONTHLY = [
    "CREATE INDEX idx_asm_yearmonth ON agg_sales_monthly_v1(year_month);",
    "CREATE INDEX idx_asm_region    ON agg_sales_monthly_v1(region_id);",
    "CREATE INDEX idx_asm_segment   ON agg_sales_monthly_v1(segment_id);",
]

# ---------------------------------------------------------------------------
# 2. PRODUCTION — Aggregation tables
# ---------------------------------------------------------------------------

DDL_AGG_PRODUCTION_DAILY = """
CREATE TABLE agg_production_daily_v1 AS
SELECT
    f.time_id,
    f.product_id,
    f.plant_id,
    f.segment_id,

    COUNT(f.production_fact_id)                                  AS production_runs,
    SUM(f.planned_qty)                                           AS total_planned,
    SUM(f.actual_qty)                                            AS total_actual,
    SUM(f.actual_qty) - SUM(f.planned_qty)                       AS qty_variance,
    SUM(f.actual_qty) / NULLIF(SUM(f.planned_qty), 0)            AS achievement_ratio,
    AVG(f.yield_pct)                                             AS avg_yield_pct,
    SUM(f.total_production_cost)                                 AS total_cost,
    SUM(f.total_production_cost) / NULLIF(SUM(f.actual_qty), 0)  AS cost_per_unit,

    CURRENT_TIMESTAMP                                            AS created_at

FROM fact_production f
GROUP BY f.time_id, f.product_id, f.plant_id, f.segment_id;
"""

IDX_AGG_PRODUCTION_DAILY = [
    "CREATE INDEX idx_apd_time    ON agg_production_daily_v1(time_id);",
    "CREATE INDEX idx_apd_plant   ON agg_production_daily_v1(plant_id);",
    "CREATE INDEX idx_apd_product ON agg_production_daily_v1(product_id);",
]

DDL_AGG_PRODUCTION_PLANT = """
CREATE TABLE agg_production_plant_v1 AS
SELECT
    TO_CHAR(t.full_date, 'YYYYMM')       AS year_month,
    d.plant_id,

    SUM(d.production_runs)               AS monthly_runs,
    SUM(d.total_planned)                 AS monthly_planned,
    SUM(d.total_actual)                  AS monthly_actual,
    SUM(d.qty_variance)                  AS monthly_qty_variance,
    AVG(d.avg_yield_pct)                 AS plant_avg_yield,
    SUM(d.total_cost)                    AS monthly_total_cost,
    SUM(d.total_cost) / NULLIF(SUM(d.total_actual), 0) AS monthly_cost_per_unit,

    CASE
        WHEN AVG(d.avg_yield_pct) >= 0.95 THEN 'Excellent'
        WHEN AVG(d.avg_yield_pct) >= 0.88 THEN 'Good'
        WHEN AVG(d.avg_yield_pct) >= 0.80 THEN 'Fair'
        ELSE 'Below Target'
    END                                  AS yield_status,

    CURRENT_TIMESTAMP                    AS created_at

FROM agg_production_daily_v1 d
JOIN dim_time t ON d.time_id = t.time_id
GROUP BY TO_CHAR(t.full_date, 'YYYYMM'), d.plant_id;
"""

IDX_AGG_PRODUCTION_PLANT = [
    "CREATE INDEX idx_app_yearmonth ON agg_production_plant_v1(year_month);",
    "CREATE INDEX idx_app_plant     ON agg_production_plant_v1(plant_id);",
]

# ---------------------------------------------------------------------------
# 3. INVENTORY — Aggregation tables
# ---------------------------------------------------------------------------

DDL_AGG_INVENTORY_SNAPSHOT = """
CREATE TABLE agg_inventory_snapshot_v1 AS
SELECT
    fi.product_id,
    fi.warehouse_id,
    fi.segment_id,

    MAX(fi.time_id)                                     AS latest_time_id,
    AVG(fi.closing_qty)                                 AS avg_closing_qty,
    MAX(fi.closing_qty)                                 AS peak_closing_qty,
    MIN(fi.closing_qty)                                 AS min_closing_qty,
    AVG(fi.opening_qty)                                 AS avg_opening_qty,
    AVG(fi.inventory_value)                             AS avg_inventory_value,
    SUM(fi.inventory_value)                             AS total_inventory_value,
    COUNT(*) FILTER (WHERE fi.closing_qty <= 0)         AS stockout_periods,
    COUNT(fi.inventory_fact_id)                         AS total_snapshots,

    CURRENT_TIMESTAMP                                   AS created_at

FROM fact_inventory fi
GROUP BY fi.product_id, fi.warehouse_id, fi.segment_id;
"""

IDX_AGG_INVENTORY_SNAPSHOT = [
    "CREATE INDEX idx_ais_product   ON agg_inventory_snapshot_v1(product_id);",
    "CREATE INDEX idx_ais_warehouse ON agg_inventory_snapshot_v1(warehouse_id);",
]

DDL_AGG_INVENTORY_WEEKLY = """
CREATE TABLE agg_inventory_weekly_v1 AS
SELECT
    TO_CHAR(t.full_date, 'IYYYIW')           AS year_week,
    f.product_id,
    f.warehouse_id,
    f.segment_id,

    COUNT(f.inventory_fact_id)               AS snapshots_in_week,
    AVG(f.closing_qty)                       AS avg_qty,
    MAX(f.closing_qty)                       AS max_qty,
    MIN(f.closing_qty)                       AS min_qty,
    MAX(f.closing_qty) - MIN(f.closing_qty)  AS qty_range,
    AVG(f.inventory_value)                   AS avg_value,
    COUNT(*) FILTER (WHERE f.closing_qty <= 0)                          AS stockout_days,
    SUM(GREATEST(f.closing_qty - f.opening_qty, 0))                     AS total_net_inflow,
    SUM(GREATEST(f.opening_qty - f.closing_qty, 0))                     AS total_net_outflow,

    CURRENT_TIMESTAMP                        AS created_at

FROM fact_inventory f
JOIN dim_time t ON f.time_id = t.time_id
GROUP BY
    TO_CHAR(t.full_date, 'IYYYIW'),
    f.product_id, f.warehouse_id, f.segment_id;
"""

IDX_AGG_INVENTORY_WEEKLY = [
    "CREATE INDEX idx_aiw_week      ON agg_inventory_weekly_v1(year_week);",
    "CREATE INDEX idx_aiw_product   ON agg_inventory_weekly_v1(product_id);",
    "CREATE INDEX idx_aiw_warehouse ON agg_inventory_weekly_v1(warehouse_id);",
]

# ---------------------------------------------------------------------------
# 4. SHIPMENT — Aggregation tables
# ---------------------------------------------------------------------------

DDL_AGG_SHIPMENT_DAILY = """
CREATE TABLE agg_shipment_daily_v1 AS
SELECT
    f.time_id,
    f.region_id,
    f.warehouse_id,
    f.shipping_method,

    COUNT(f.shipment_fact_id)                                           AS total_shipments,
    COUNT(*) FILTER (WHERE f.on_time_flag)                              AS on_time_count,
    COUNT(*) FILTER (WHERE NOT f.on_time_flag)                          AS late_count,
    ROUND(AVG(CASE WHEN f.on_time_flag THEN 1.0 ELSE 0.0 END) * 100, 2) AS on_time_pct,
    SUM(f.freight_cost)                                                 AS total_freight_cost,
    AVG(f.freight_cost)                                                 AS avg_freight_cost,

    CURRENT_TIMESTAMP                                                   AS created_at

FROM fact_shipment f
GROUP BY f.time_id, f.region_id, f.warehouse_id, f.shipping_method;
"""

IDX_AGG_SHIPMENT_DAILY = [
    "CREATE INDEX idx_ashipd_time      ON agg_shipment_daily_v1(time_id);",
    "CREATE INDEX idx_ashipd_region    ON agg_shipment_daily_v1(region_id);",
    "CREATE INDEX idx_ashipd_warehouse ON agg_shipment_daily_v1(warehouse_id);",
]

# ---------------------------------------------------------------------------
# 5. DATA MARTS — Wide / Denormalized
# ---------------------------------------------------------------------------

DDL_MART_SALES = """
CREATE TABLE mart_sales_v1 AS
SELECT
    -- Time
    t.time_id,
    t.full_date,
    t.day_of_week,
    t.month_name,
    t.quarter,
    t.year,
    TO_CHAR(t.full_date, 'YYYYMM')                          AS year_month,

    -- Product
    p.product_code,
    p.product_name,
    p.product_category,
    p.unit_of_measure,
    p.principal_name,
    p.target_industry,

    -- Customer
    c.customer_code,
    c.customer_name,
    c.customer_type,
    c.industry_segment,

    -- Region
    r.region_code,
    r.region_name,
    r.country,
    r.is_domestic,

    -- Segment
    sg.segment_code,
    sg.segment_name,

    -- Employee
    e.employee_code,
    e.full_name                                              AS salesperson_name,
    e.department,

    -- Warehouse
    w.warehouse_code,
    w.warehouse_name,
    w.warehouse_type,

    -- Measures
    f.quantity_ordered,
    f.unit_price,
    f.net_amount,
    f.gross_margin_pct,
    f.quantity_ordered * f.unit_price                        AS gross_amount,
    f.net_amount - (f.quantity_ordered * f.unit_price)       AS discount_amount,
    f.net_amount * f.gross_margin_pct                        AS est_gross_profit,

    CURRENT_TIMESTAMP                                        AS mart_created_at

FROM fact_sales      f
JOIN dim_time        t  ON f.time_id      = t.time_id
JOIN dim_product     p  ON f.product_id   = p.product_id
JOIN dim_customer    c  ON f.customer_id  = c.customer_id
JOIN dim_region      r  ON f.region_id    = r.region_id
JOIN dim_segment     sg ON f.segment_id   = sg.segment_id
JOIN dim_employee    e  ON f.employee_id  = e.employee_id
JOIN dim_warehouse   w  ON f.warehouse_id = w.warehouse_id;
"""

IDX_MART_SALES = [
    "CREATE INDEX idx_msv1_yearmonth ON mart_sales_v1(year_month);",
    "CREATE INDEX idx_msv1_region    ON mart_sales_v1(region_code);",
    "CREATE INDEX idx_msv1_product   ON mart_sales_v1(product_code);",
    "CREATE INDEX idx_msv1_customer  ON mart_sales_v1(customer_code);",
    "CREATE INDEX idx_msv1_domestic  ON mart_sales_v1(is_domestic);",
]

DDL_MART_PRODUCTION = """
CREATE TABLE mart_production_v1 AS
SELECT
    -- Time
    t.time_id,
    t.full_date,
    t.month_name,
    t.quarter,
    t.year,
    TO_CHAR(t.full_date, 'YYYYMM')                              AS year_month,

    -- Plant
    pl.plant_code,
    pl.plant_name,
    pl.plant_type,

    -- Plant region
    pr.region_name                                              AS plant_region,
    pr.country                                                  AS plant_country,
    pr.is_domestic                                              AS plant_is_domestic,

    -- Product
    p.product_code,
    p.product_name,
    p.product_category,
    p.principal_name,
    p.unit_of_measure,

    -- Segment
    sg.segment_code,
    sg.segment_name,

    -- Measures
    f.planned_qty,
    f.actual_qty,
    f.actual_qty - f.planned_qty                                AS qty_variance,
    ROUND(f.actual_qty / NULLIF(f.planned_qty, 0), 4)           AS achievement_ratio,
    f.yield_pct,
    ROUND((1 - f.yield_pct) * 100, 2)                          AS implied_scrap_pct,
    f.total_production_cost,
    f.total_production_cost / NULLIF(f.actual_qty, 0)           AS cost_per_unit,

    -- Status
    CASE
        WHEN f.yield_pct >= 0.95 THEN 'Excellent'
        WHEN f.yield_pct >= 0.88 THEN 'Good'
        WHEN f.yield_pct >= 0.80 THEN 'Fair'
        ELSE 'Below Target'
    END                                                         AS yield_status,

    CURRENT_TIMESTAMP                                           AS mart_created_at

FROM fact_production f
JOIN dim_time     t  ON f.time_id    = t.time_id
JOIN dim_plant    pl ON f.plant_id   = pl.plant_id
JOIN dim_region   pr ON pl.region_id = pr.region_id
JOIN dim_product  p  ON f.product_id = p.product_id
JOIN dim_segment  sg ON f.segment_id = sg.segment_id;
"""

IDX_MART_PRODUCTION = [
    "CREATE INDEX idx_mpv1_yearmonth ON mart_production_v1(year_month);",
    "CREATE INDEX idx_mpv1_plant     ON mart_production_v1(plant_code);",
    "CREATE INDEX idx_mpv1_product   ON mart_production_v1(product_code);",
]

DDL_MART_INVENTORY = """
CREATE TABLE mart_inventory_v1 AS
SELECT
    -- Time
    t.time_id,
    t.full_date,
    t.month_name,
    t.quarter,
    t.year,
    TO_CHAR(t.full_date, 'YYYYMM')                              AS year_month,
    TO_CHAR(t.full_date, 'IYYYIW')                              AS year_week,

    -- Product
    p.product_code,
    p.product_name,
    p.product_category,
    p.principal_name,
    p.unit_of_measure,

    -- Warehouse
    w.warehouse_code,
    w.warehouse_name,
    w.warehouse_type,

    -- Warehouse region
    wr.region_name                                              AS warehouse_region,
    wr.country                                                  AS warehouse_country,
    wr.is_domestic                                              AS is_domestic_warehouse,

    -- Segment
    sg.segment_code,
    sg.segment_name,

    -- Measures
    f.opening_qty,
    f.closing_qty,
    f.closing_qty - f.opening_qty                               AS net_movement,
    f.inventory_value,

    -- Derived flags
    CASE WHEN f.closing_qty <= 0  THEN 1 ELSE 0 END             AS is_stockout,
    CASE WHEN f.closing_qty > f.opening_qty * 2 THEN 1 ELSE 0 END AS is_overstock,

    CURRENT_TIMESTAMP                                           AS mart_created_at

FROM fact_inventory  f
JOIN dim_time        t  ON f.time_id      = t.time_id
JOIN dim_product     p  ON f.product_id   = p.product_id
JOIN dim_warehouse   w  ON f.warehouse_id = w.warehouse_id
JOIN dim_region      wr ON w.region_id    = wr.region_id
JOIN dim_segment     sg ON f.segment_id   = sg.segment_id;
"""

IDX_MART_INVENTORY = [
    "CREATE INDEX idx_miv1_yearmonth  ON mart_inventory_v1(year_month);",
    "CREATE INDEX idx_miv1_product    ON mart_inventory_v1(product_code);",
    "CREATE INDEX idx_miv1_warehouse  ON mart_inventory_v1(warehouse_code);",
    "CREATE INDEX idx_miv1_domestic   ON mart_inventory_v1(is_domestic_warehouse);",
]

DDL_MART_LOGISTICS = """
CREATE TABLE mart_logistics_v1 AS
SELECT
    -- Time
    t.time_id,
    t.full_date,
    t.month_name,
    t.quarter,
    t.year,
    TO_CHAR(t.full_date, 'YYYYMM')                              AS year_month,

    -- Customer
    c.customer_code,
    c.customer_name,
    c.customer_type,
    c.industry_segment,

    -- Destination region
    r.region_code,
    r.region_name,
    r.country,
    r.is_domestic,

    -- Origin warehouse
    w.warehouse_code,
    w.warehouse_name,
    w.warehouse_type,

    -- Shipment facts
    f.shipping_method,
    f.freight_cost,
    f.on_time_flag,
    CASE WHEN f.on_time_flag THEN 'On-Time' ELSE 'Late' END      AS delivery_status,

    -- SLA classification
    CASE
        WHEN r.is_domestic AND f.on_time_flag           THEN 'Domestic On-Time'
        WHEN r.is_domestic AND NOT f.on_time_flag        THEN 'Domestic Late'
        WHEN NOT r.is_domestic AND f.on_time_flag        THEN 'Export On-Time'
        ELSE 'Export Late'
    END                                                          AS sla_category,

    CURRENT_TIMESTAMP                                            AS mart_created_at

FROM fact_shipment   f
JOIN dim_time        t  ON f.time_id      = t.time_id
JOIN dim_customer    c  ON f.customer_id  = c.customer_id
JOIN dim_region      r  ON f.region_id    = r.region_id
JOIN dim_warehouse   w  ON f.warehouse_id = w.warehouse_id;
"""

IDX_MART_LOGISTICS = [
    "CREATE INDEX idx_mlv1_yearmonth ON mart_logistics_v1(year_month);",
    "CREATE INDEX idx_mlv1_region    ON mart_logistics_v1(region_code);",
    "CREATE INDEX idx_mlv1_method    ON mart_logistics_v1(shipping_method);",
    "CREATE INDEX idx_mlv1_otf       ON mart_logistics_v1(on_time_flag);",
]

DDL_MART_INTEGRATED_KPI = """
CREATE TABLE mart_integrated_kpi_v1 AS
WITH
sales_kpi AS (
    SELECT
        TO_CHAR(t.full_date, 'YYYYMM')  AS year_month,
        SUM(f.net_amount)               AS total_revenue,
        SUM(f.quantity_ordered)         AS total_units_sold,
        AVG(f.gross_margin_pct)         AS avg_sales_margin,
        COUNT(DISTINCT f.customer_id)   AS unique_customers,
        COUNT(f.sales_fact_id)          AS total_order_lines
    FROM fact_sales f
    JOIN dim_time t ON f.time_id = t.time_id
    GROUP BY TO_CHAR(t.full_date, 'YYYYMM')
),
production_kpi AS (
    SELECT
        TO_CHAR(t.full_date, 'YYYYMM')   AS year_month,
        SUM(f.actual_qty)                 AS total_produced,
        SUM(f.planned_qty)                AS total_planned,
        AVG(f.yield_pct)                  AS avg_yield,
        SUM(f.total_production_cost)      AS total_prod_cost,
        COUNT(f.production_fact_id)       AS production_runs
    FROM fact_production f
    JOIN dim_time t ON f.time_id = t.time_id
    GROUP BY TO_CHAR(t.full_date, 'YYYYMM')
),
inventory_kpi AS (
    SELECT
        TO_CHAR(t.full_date, 'YYYYMM')           AS year_month,
        AVG(f.closing_qty)                        AS avg_stock_level,
        SUM(f.inventory_value)                    AS total_inventory_value,
        COUNT(*) FILTER (WHERE f.closing_qty <= 0) AS stockout_events,
        COUNT(f.inventory_fact_id)                AS inventory_snapshots
    FROM fact_inventory f
    JOIN dim_time t ON f.time_id = t.time_id
    GROUP BY TO_CHAR(t.full_date, 'YYYYMM')
),
shipment_kpi AS (
    SELECT
        TO_CHAR(t.full_date, 'YYYYMM')                                     AS year_month,
        COUNT(f.shipment_fact_id)                                           AS total_shipments,
        ROUND(AVG(CASE WHEN f.on_time_flag THEN 1.0 ELSE 0.0 END)*100, 2)  AS otd_pct,
        SUM(f.freight_cost)                                                 AS total_freight_cost,
        AVG(f.freight_cost)                                                 AS avg_freight_per_shipment
    FROM fact_shipment f
    JOIN dim_time t ON f.time_id = t.time_id
    GROUP BY TO_CHAR(t.full_date, 'YYYYMM')
)
SELECT
    COALESCE(s.year_month, p.year_month, i.year_month, sh.year_month) AS year_month,

    -- Sales KPIs
    s.total_revenue,
    s.total_units_sold,
    ROUND(s.avg_sales_margin * 100, 2)                      AS avg_sales_margin_pct,
    s.unique_customers,
    s.total_order_lines,

    -- Production KPIs
    p.total_produced,
    p.total_planned,
    ROUND(p.avg_yield * 100, 2)                             AS avg_yield_pct,
    ROUND((1 - p.avg_yield) * 100, 2)                       AS avg_scrap_pct,
    p.total_prod_cost,
    ROUND(p.total_prod_cost / NULLIF(p.total_produced, 0), 4) AS prod_cost_per_unit,
    p.production_runs,

    -- Inventory KPIs
    ROUND(i.avg_stock_level, 2)                             AS avg_stock_level,
    i.total_inventory_value,
    i.stockout_events,
    i.inventory_snapshots,

    -- Shipment KPIs
    sh.total_shipments,
    sh.otd_pct,
    sh.total_freight_cost,
    sh.avg_freight_per_shipment,

    -- Integrated / Cross-domain derived
    ROUND(s.total_revenue / NULLIF(sh.total_freight_cost, 0), 2)         AS revenue_per_freight,
    ROUND(s.total_units_sold / NULLIF(p.total_produced, 0), 4)            AS sell_thru_ratio,
    ROUND(s.total_revenue / NULLIF(i.total_inventory_value, 0), 4)        AS revenue_to_inventory_ratio,

    CURRENT_TIMESTAMP                                       AS created_at

FROM      sales_kpi      s
FULL JOIN production_kpi p  ON s.year_month = p.year_month
FULL JOIN inventory_kpi  i  ON COALESCE(s.year_month, p.year_month) = i.year_month
FULL JOIN shipment_kpi   sh ON COALESCE(s.year_month, p.year_month, i.year_month) = sh.year_month
ORDER BY year_month;
"""

IDX_MART_INTEGRATED_KPI = [
    "CREATE INDEX idx_mikpi_ym ON mart_integrated_kpi_v1(year_month);",
]

# ---------------------------------------------------------------------------
# 6. Master table registry
#    Each entry: (table_name, create_ddl, index_ddl_list)
#    Order matters: agg tables first, then marts that depend on agg tables.
# ---------------------------------------------------------------------------

OLAP_TABLES: list[tuple[str, str, list[str]]] = [
    # ── Aggregation layer ──────────────────────────────────────────────────
    ("agg_sales_daily_v1",          DDL_AGG_SALES_DAILY,          IDX_AGG_SALES_DAILY),
    ("agg_sales_monthly_v1",        DDL_AGG_SALES_MONTHLY,        IDX_AGG_SALES_MONTHLY),
    ("agg_production_daily_v1",     DDL_AGG_PRODUCTION_DAILY,     IDX_AGG_PRODUCTION_DAILY),
    ("agg_production_plant_v1",     DDL_AGG_PRODUCTION_PLANT,     IDX_AGG_PRODUCTION_PLANT),
    ("agg_inventory_snapshot_v1",   DDL_AGG_INVENTORY_SNAPSHOT,   IDX_AGG_INVENTORY_SNAPSHOT),
    ("agg_inventory_weekly_v1",     DDL_AGG_INVENTORY_WEEKLY,     IDX_AGG_INVENTORY_WEEKLY),
    ("agg_shipment_daily_v1",       DDL_AGG_SHIPMENT_DAILY,       IDX_AGG_SHIPMENT_DAILY),
    # ── Data mart layer ────────────────────────────────────────────────────
    ("mart_sales_v1",               DDL_MART_SALES,               IDX_MART_SALES),
    ("mart_production_v1",          DDL_MART_PRODUCTION,          IDX_MART_PRODUCTION),
    ("mart_inventory_v1",           DDL_MART_INVENTORY,           IDX_MART_INVENTORY),
    ("mart_logistics_v1",           DDL_MART_LOGISTICS,           IDX_MART_LOGISTICS),
    ("mart_integrated_kpi_v1",      DDL_MART_INTEGRATED_KPI,      IDX_MART_INTEGRATED_KPI),
]
