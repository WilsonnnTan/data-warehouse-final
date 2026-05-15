from __future__ import annotations

import csv
import json
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import random
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parent
CSV_DIR = ROOT_DIR / "csv"
JSON_DIR = ROOT_DIR / "json"
SQLITE_DIR = ROOT_DIR / "sqlite"
SQLITE_PATH = SQLITE_DIR / "source_systems.db"

SEED = 20260515
HOME_COUNTRY = "Indonesia"
TABLE_FORMATS = {
    "crm_regions": "json",
    "crm_customers": "json",
    "so_orders": "json",
    "so_order_items": "json",
    "lgs_shipments": "json",
    "segment_reference": "json",
    "customer_region_snapshot": "json",
    "wms_warehouses": "csv",
    "wms_inventory_transactions": "csv",
    "hr_employees": "csv",
    "sales_employee_segment_lookup": "csv",
    "erp_products": "sqlite",
    "erp_plants": "sqlite",
    "mrp_production_orders": "sqlite",
    "mrp_production_results": "sqlite",
    "product_cost_lookup": "sqlite",
    "production_segment_lookup": "sqlite",
    "inventory_segment_lookup": "sqlite",
}


def quantize(value: Decimal, places: str = "0.01") -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def date_to_time_id(value: date) -> int:
    return int(value.strftime("%Y%m%d"))


@dataclass(frozen=True)
class Region:
    region_id: int
    region_code: str
    region_name: str
    country: str


@dataclass(frozen=True)
class Customer:
    customer_id: int
    customer_code: str
    customer_name: str
    customer_type: str
    industry: str
    region_id: int


@dataclass(frozen=True)
class Product:
    product_id: int
    product_code: str
    product_name: str
    category: str
    uom: str
    principal: str
    target_industry: str
    standard_cost: Decimal


@dataclass(frozen=True)
class Plant:
    plant_id: int
    plant_code: str
    plant_name: str
    plant_type: str
    region_id: int


@dataclass(frozen=True)
class Warehouse:
    warehouse_id: int
    warehouse_code: str
    warehouse_name: str
    warehouse_type: str
    region_id: int


@dataclass(frozen=True)
class Employee:
    employee_id: int
    employee_code: str
    full_name: str
    department: str
    segment: str
    region_id: int


@dataclass(frozen=True)
class Segment:
    segment_id: int
    segment_code: str
    segment_name: str


def serialize_value(value: object) -> object:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def rows_from_records(records: Iterable[object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in records:
        if hasattr(record, "__dataclass_fields__"):
            raw = asdict(record)
        elif isinstance(record, dict):
            raw = dict(record)
        else:
            raise TypeError(f"Unsupported record type: {type(record)!r}")
        rows.append({key: serialize_value(value) for key, value in raw.items()})
    return rows


def ensure_directories() -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)


def clear_previous_outputs() -> None:
    for directory in (CSV_DIR, JSON_DIR):
        for path in directory.glob("*"):
            if path.is_file():
                path.unlink()
    if SQLITE_PATH.exists():
        SQLITE_PATH.unlink()


def write_csv(table_name: str, rows: list[dict[str, object]]) -> None:
    path = CSV_DIR / f"{table_name}.csv"
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(table_name: str, rows: list[dict[str, object]]) -> None:
    path = JSON_DIR / f"{table_name}.json"
    with path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)


def sqlite_type(value: object) -> str:
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    return "TEXT"


def write_sqlite(table_map: dict[str, list[dict[str, object]]]) -> None:
    with sqlite3.connect(SQLITE_PATH) as connection:
        cursor = connection.cursor()

        for table_name, rows in table_map.items():
            if not rows:
                continue

            columns = list(rows[0].keys())
            column_defs = ", ".join(
                f'"{column}" {sqlite_type(rows[0][column])}' for column in columns
            )
            placeholders = ", ".join("?" for _ in columns)
            quoted_columns = ", ".join(f'"{column}"' for column in columns)

            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            cursor.execute(f'CREATE TABLE "{table_name}" ({column_defs})')
            cursor.executemany(
                f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})',
                [tuple(row[column] for column in columns) for row in rows],
            )

        connection.commit()


def write_table_by_format(table_name: str, rows: list[dict[str, object]]) -> None:
    output_format = TABLE_FORMATS[table_name]
    if output_format == "csv":
        write_csv(table_name, rows)
    elif output_format == "json":
        write_json(table_name, rows)
    elif output_format == "sqlite":
        return
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def build_reference_data() -> dict[str, list[object]]:
    regions = [
        Region(1, "JKT", "Jakarta Metro", "Indonesia"),
        Region(2, "SBY", "Surabaya East", "Indonesia"),
        Region(3, "BDG", "Bandung Highlands", "Indonesia"),
        Region(4, "SGP", "Singapore Hub", "Singapore"),
        Region(5, "KUL", "Kuala Lumpur Hub", "Malaysia"),
        Region(6, "BKK", "Bangkok Corridor", "Thailand"),
    ]

    segments = [
        Segment(1, "CON", "Consumer"),
        Segment(2, "RET", "Retail"),
        Segment(3, "HRC", "Healthcare"),
        Segment(4, "MFG", "Manufacturing"),
    ]

    customers = [
        Customer(1, "CUST-001", "Nusantara Mart", "Distributor", "Retail", 1),
        Customer(2, "CUST-002", "Sehat Farma", "Enterprise", "Healthcare", 1),
        Customer(3, "CUST-003", "Java Wholesale", "Distributor", "Consumer Goods", 2),
        Customer(4, "CUST-004", "Bandung Medika", "Enterprise", "Healthcare", 3),
        Customer(5, "CUST-005", "Lion City Trade", "Export", "Retail", 4),
        Customer(6, "CUST-006", "Malaya Essentials", "Export", "Consumer Goods", 5),
        Customer(7, "CUST-007", "Siam Care Supply", "Enterprise", "Healthcare", 6),
        Customer(8, "CUST-008", "Archipelago Foods", "Enterprise", "Food & Beverage", 2),
        Customer(9, "CUST-009", "Pacific Hardware", "Distributor", "Manufacturing", 4),
        Customer(10, "CUST-010", "Indo Retail Group", "Key Account", "Retail", 1),
        Customer(11, "CUST-011", "Garuda Home Goods", "Distributor", "Consumer Goods", 3),
        Customer(12, "CUST-012", "Mekar Industri", "Enterprise", "Manufacturing", 2),
    ]

    products = [
        Product(1, "PRD-001", "Vitamin C Syrup", "Pharma", "BOTTLE", "BioNusa", "Healthcare", Decimal("18.50")),
        Product(2, "PRD-002", "Pain Relief Tablet", "Pharma", "BOX", "BioNusa", "Healthcare", Decimal("12.40")),
        Product(3, "PRD-003", "Mineral Water 600ml", "Beverage", "CASE", "FreshWave", "Food & Beverage", Decimal("22.10")),
        Product(4, "PRD-004", "Sparkling Drink", "Beverage", "CASE", "FreshWave", "Retail", Decimal("26.80")),
        Product(5, "PRD-005", "Household Cleaner", "Home Care", "BOX", "Cleanera", "Retail", Decimal("15.30")),
        Product(6, "PRD-006", "Dishwashing Liquid", "Home Care", "BOTTLE", "Cleanera", "Retail", Decimal("10.70")),
        Product(7, "PRD-007", "Industrial Solvent", "Chemical", "DRUM", "ChemPro", "Manufacturing", Decimal("75.00")),
        Product(8, "PRD-008", "Lubricant Oil", "Chemical", "DRUM", "ChemPro", "Manufacturing", Decimal("68.40")),
        Product(9, "PRD-009", "Snack Crackers", "Food", "CASE", "Golden Bite", "Consumer", Decimal("14.90")),
        Product(10, "PRD-010", "Instant Noodles", "Food", "CASE", "Golden Bite", "Consumer", Decimal("11.80")),
    ]

    plants = [
        Plant(1, "PLT-JKT", "Jakarta Main Plant", "Manufacturing", 1),
        Plant(2, "PLT-SBY", "Surabaya Processing Plant", "Manufacturing", 2),
        Plant(3, "PLT-BDG", "Bandung Packaging Plant", "Packaging", 3),
        Plant(4, "PLT-SGP", "Singapore Export Plant", "Manufacturing", 4),
    ]

    warehouses = [
        Warehouse(1, "WH-JKT", "Jakarta Central Warehouse", "Distribution", 1),
        Warehouse(2, "WH-SBY", "Surabaya Fulfillment Center", "Distribution", 2),
        Warehouse(3, "WH-BDG", "Bandung Finished Goods Hub", "Storage", 3),
        Warehouse(4, "WH-SGP", "Singapore Export Warehouse", "Export", 4),
        Warehouse(5, "WH-BKK", "Bangkok Transit Warehouse", "Transit", 6),
    ]

    employees = [
        Employee(1, "EMP-001", "Ari Pratama", "Sales", "Retail", 1),
        Employee(2, "EMP-002", "Dina Kusuma", "Sales", "Healthcare", 1),
        Employee(3, "EMP-003", "Rizky Mahesa", "Sales", "Consumer", 2),
        Employee(4, "EMP-004", "Nadia Putri", "Operations", "Manufacturing", 2),
        Employee(5, "EMP-005", "Kevin Tan", "Export", "Retail", 4),
        Employee(6, "EMP-006", "Siti Rahma", "Operations", "Healthcare", 3),
        Employee(7, "EMP-007", "Anan Chaiwat", "Logistics", "Healthcare", 6),
        Employee(8, "EMP-008", "Maya Lestari", "Sales", "Manufacturing", 3),
    ]

    return {
        "crm_regions": regions,
        "crm_customers": customers,
        "erp_products": products,
        "erp_plants": plants,
        "wms_warehouses": warehouses,
        "hr_employees": employees,
        "segment_reference": segments,
    }


def build_sales_data(
    rng: random.Random,
    customers: list[Customer],
    employees: list[Employee],
    products: list[Product],
    warehouses: list[Warehouse],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    order_start = date(2025, 1, 1)
    payment_terms_options = ["COD", "NET15", "NET30", "NET45"]
    order_status_options = ["CONFIRMED", "SHIPPED", "COMPLETED"]

    orders: list[dict[str, object]] = []
    order_items: list[dict[str, object]] = []
    item_id = 1

    for order_id in range(1, 61):
        customer = rng.choice(customers)
        salesperson = rng.choice(employees)
        warehouse = rng.choice(warehouses)
        order_date = order_start + timedelta(days=rng.randint(0, 119))
        item_count = rng.randint(1, 4)

        orders.append(
            {
                "order_id": order_id,
                "order_no": f"SO-{order_date.year}-{order_id:04d}",
                "order_date": order_date,
                "customer_id": customer.customer_id,
                "salesperson_id": salesperson.employee_id,
                "warehouse_id": warehouse.warehouse_id,
                "order_status": rng.choice(order_status_options),
                "payment_terms": rng.choice(payment_terms_options),
            }
        )

        for _ in range(item_count):
            product = rng.choice(products)
            qty_ordered = Decimal(rng.randint(5, 120))
            markup = Decimal(str(rng.uniform(1.15, 1.65)))
            unit_price = quantize(product.standard_cost * markup)
            order_items.append(
                {
                    "item_id": item_id,
                    "order_id": order_id,
                    "product_id": product.product_id,
                    "qty_ordered": quantize(qty_ordered),
                    "unit_price": unit_price,
                    "discount_pct": quantize(Decimal(str(rng.choice([0, 0.02, 0.05, 0.1]))), "0.0001"),
                }
            )
            item_id += 1

    return orders, order_items


def build_production_data(
    rng: random.Random,
    products: list[Product],
    plants: list[Plant],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    start_date = date(2025, 1, 1)
    production_orders: list[dict[str, object]] = []
    production_results: list[dict[str, object]] = []

    for prod_order_id in range(1, 41):
        product = rng.choice(products)
        plant = rng.choice(plants)
        plan_start = start_date + timedelta(days=rng.randint(0, 119))
        duration_days = rng.randint(1, 5)
        planned_qty = Decimal(rng.randint(100, 1200))
        actual_qty = quantize(planned_qty * Decimal(str(rng.uniform(0.88, 1.05))))
        scrap_qty = quantize(actual_qty * Decimal(str(rng.uniform(0.01, 0.08))))
        production_cost = quantize(
            actual_qty * product.standard_cost * Decimal(str(rng.uniform(0.92, 1.15)))
        )

        production_orders.append(
            {
                "prod_order_id": prod_order_id,
                "prod_order_no": f"MO-2025-{prod_order_id:04d}",
                "product_id": product.product_id,
                "plant_id": plant.plant_id,
                "plan_start_date": plan_start,
                "plan_end_date": plan_start + timedelta(days=duration_days),
                "planned_qty": quantize(planned_qty),
            }
        )

        production_results.append(
            {
                "result_id": prod_order_id,
                "prod_order_id": prod_order_id,
                "actual_date": plan_start + timedelta(days=duration_days),
                "actual_qty": actual_qty,
                "scrap_qty": scrap_qty,
                "production_cost": production_cost,
            }
        )

    return production_orders, production_results


def build_inventory_transactions(
    rng: random.Random,
    products: list[Product],
    warehouses: list[Warehouse],
) -> list[dict[str, object]]:
    start_date = date(2025, 1, 1)
    transactions: list[dict[str, object]] = []
    txn_id = 1

    for warehouse in warehouses:
        for product in products:
            base_cost = product.standard_cost
            for day_offset in range(0, 120, 6):
                txn_date = start_date + timedelta(days=day_offset)
                inbound_qty = Decimal(rng.randint(20, 180))
                outbound_qty = Decimal(rng.randint(10, 140))

                transactions.append(
                    {
                        "txn_id": txn_id,
                        "product_id": product.product_id,
                        "warehouse_id": warehouse.warehouse_id,
                        "txn_date": txn_date,
                        "txn_type": "IN",
                        "qty_in": quantize(inbound_qty),
                        "qty_out": Decimal("0.00"),
                        "unit_cost": quantize(base_cost * Decimal(str(rng.uniform(0.98, 1.06)))),
                    }
                )
                txn_id += 1

                transactions.append(
                    {
                        "txn_id": txn_id,
                        "product_id": product.product_id,
                        "warehouse_id": warehouse.warehouse_id,
                        "txn_date": txn_date + timedelta(days=2),
                        "txn_type": "OUT",
                        "qty_in": Decimal("0.00"),
                        "qty_out": quantize(outbound_qty),
                        "unit_cost": quantize(base_cost * Decimal(str(rng.uniform(0.98, 1.06)))),
                    }
                )
                txn_id += 1

    return transactions


def build_shipments(
    rng: random.Random,
    orders: list[dict[str, object]],
    customers_by_id: dict[int, Customer],
) -> list[dict[str, object]]:
    shipping_methods = ["Truck", "Sea Freight", "Air Freight", "Courier"]
    shipments: list[dict[str, object]] = []

    for shipment_id, order in enumerate(orders[:45], start=1):
        ship_date = order["order_date"] + timedelta(days=rng.randint(1, 6))
        eta_date = ship_date + timedelta(days=rng.randint(1, 10))
        actual_arrival = eta_date + timedelta(days=rng.choice([-1, 0, 0, 1, 2]))
        customer = customers_by_id[order["customer_id"]]

        shipments.append(
            {
                "shipment_id": shipment_id,
                "tracking_no": f"TRK-{ship_date.year}-{shipment_id:05d}",
                "order_id": order["order_id"],
                "warehouse_id": order["warehouse_id"],
                "region_id": customer.region_id,
                "ship_date": ship_date,
                "eta_date": eta_date,
                "actual_arrival": actual_arrival,
                "shipping_method": rng.choice(shipping_methods),
                "freight_cost": quantize(Decimal(str(rng.uniform(150, 2500)))),
            }
        )

    return shipments


def build_metadata(
    regions: list[Region],
    customers: list[Customer],
    products: list[Product],
    plants: list[Plant],
    warehouses: list[Warehouse],
    employees: list[Employee],
    segments: list[Segment],
) -> dict[str, dict[int, object]]:
    return {
        "regions_by_id": {row.region_id: row for row in regions},
        "customers_by_id": {row.customer_id: row for row in customers},
        "products_by_id": {row.product_id: row for row in products},
        "plants_by_id": {row.plant_id: row for row in plants},
        "warehouses_by_id": {row.warehouse_id: row for row in warehouses},
        "employees_by_id": {row.employee_id: row for row in employees},
        "segments_by_name": {row.segment_name: row for row in segments},
    }


def build_fact_seed_files(
    products_by_id: dict[int, Product],
    customers_by_id: dict[int, Customer],
    employees_by_id: dict[int, Employee],
    segments_by_name: dict[str, Segment],
    production_orders: list[dict[str, object]],
    production_results: list[dict[str, object]],
    inventory_transactions: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    product_cost_lookup = []
    for product in products_by_id.values():
        product_cost_lookup.append(
            {
                "product_id": product.product_id,
                "product_code": product.product_code,
                "standard_cost": product.standard_cost,
                "target_industry": product.target_industry,
            }
        )

    production_segment_lookup = []
    for order in production_orders:
        product = products_by_id[order["product_id"]]
        segment = segments_by_name.get(product.target_industry, segments_by_name["Manufacturing"])
        production_segment_lookup.append(
            {
                "prod_order_id": order["prod_order_id"],
                "segment_code": segment.segment_code,
                "segment_name": segment.segment_name,
            }
        )

    inventory_segment_lookup = []
    segment_keys = list(segments_by_name.keys())
    for txn in inventory_transactions:
        product = products_by_id[txn["product_id"]]
        segment_name = product.target_industry if product.target_industry in segments_by_name else segment_keys[0]
        inventory_segment_lookup.append(
            {
                "txn_id": txn["txn_id"],
                "segment_code": segments_by_name[segment_name].segment_code,
                "segment_name": segments_by_name[segment_name].segment_name,
            }
        )

    sales_assignment = []
    for employee in employees_by_id.values():
        segment = segments_by_name[employee.segment]
        sales_assignment.append(
            {
                "employee_id": employee.employee_id,
                "employee_code": employee.employee_code,
                "segment_code": segment.segment_code,
                "segment_name": segment.segment_name,
            }
        )

    customer_region_snapshot = []
    for customer in customers_by_id.values():
        customer_region_snapshot.append(
            {
                "customer_id": customer.customer_id,
                "customer_code": customer.customer_code,
                "region_id": customer.region_id,
            }
        )

    return {
        "product_cost_lookup": rows_from_records(product_cost_lookup),
        "production_segment_lookup": rows_from_records(production_segment_lookup),
        "inventory_segment_lookup": rows_from_records(inventory_segment_lookup),
        "sales_employee_segment_lookup": rows_from_records(sales_assignment),
        "customer_region_snapshot": rows_from_records(customer_region_snapshot),
    }


def main() -> None:
    rng = random.Random(SEED)
    ensure_directories()
    clear_previous_outputs()

    reference_data = build_reference_data()
    regions = reference_data["crm_regions"]
    customers = reference_data["crm_customers"]
    products = reference_data["erp_products"]
    plants = reference_data["erp_plants"]
    warehouses = reference_data["wms_warehouses"]
    employees = reference_data["hr_employees"]
    segments = reference_data["segment_reference"]

    metadata = build_metadata(
        regions=regions,
        customers=customers,
        products=products,
        plants=plants,
        warehouses=warehouses,
        employees=employees,
        segments=segments,
    )

    so_orders, so_order_items = build_sales_data(
        rng=rng,
        customers=customers,
        employees=employees,
        products=products,
        warehouses=warehouses,
    )
    mrp_orders, mrp_results = build_production_data(rng=rng, products=products, plants=plants)
    inventory_transactions = build_inventory_transactions(rng=rng, products=products, warehouses=warehouses)
    shipments = build_shipments(rng=rng, orders=so_orders, customers_by_id=metadata["customers_by_id"])

    table_map: dict[str, list[dict[str, object]]] = {
        "crm_regions": rows_from_records(regions),
        "crm_customers": rows_from_records(customers),
        "erp_products": rows_from_records(products),
        "erp_plants": rows_from_records(plants),
        "hr_employees": rows_from_records(employees),
        "wms_warehouses": rows_from_records(warehouses),
        "so_orders": rows_from_records(so_orders),
        "so_order_items": rows_from_records(so_order_items),
        "mrp_production_orders": rows_from_records(mrp_orders),
        "mrp_production_results": rows_from_records(mrp_results),
        "wms_inventory_transactions": rows_from_records(inventory_transactions),
        "lgs_shipments": rows_from_records(shipments),
        "segment_reference": rows_from_records(segments),
    }
    table_map.update(
        build_fact_seed_files(
            products_by_id=metadata["products_by_id"],
            customers_by_id=metadata["customers_by_id"],
            employees_by_id=metadata["employees_by_id"],
            segments_by_name=metadata["segments_by_name"],
            production_orders=mrp_orders,
            production_results=mrp_results,
            inventory_transactions=inventory_transactions,
        )
    )

    sqlite_tables = {
        table_name: rows
        for table_name, rows in table_map.items()
        if TABLE_FORMATS[table_name] == "sqlite"
    }

    for table_name, rows in table_map.items():
        write_table_by_format(table_name, rows)

    write_sqlite(sqlite_tables)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "home_country": HOME_COUNTRY,
        "sqlite_database": str(SQLITE_PATH.relative_to(ROOT_DIR)) if sqlite_tables else None,
        "tables": {
            table_name: {
                "rows": len(rows),
                "format": TABLE_FORMATS[table_name],
                "path": (
                    str((CSV_DIR / f"{table_name}.csv").relative_to(ROOT_DIR))
                    if TABLE_FORMATS[table_name] == "csv"
                    else str((JSON_DIR / f"{table_name}.json").relative_to(ROOT_DIR))
                    if TABLE_FORMATS[table_name] == "json"
                    else str(SQLITE_PATH.relative_to(ROOT_DIR))
                ),
            }
            for table_name, rows in table_map.items()
        },
    }
    write_json("_manifest", [manifest])

    print(f"Generated {len(table_map)} datasets in {ROOT_DIR}")
    for table_name, details in manifest["tables"].items():
        print(
            f"- {table_name}: {details['rows']} rows "
            f"({details['format']} -> {details['path']})"
        )


if __name__ == "__main__":
    main()
