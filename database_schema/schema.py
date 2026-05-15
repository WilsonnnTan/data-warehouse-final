from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative class for the warehouse schema."""


class DimTime(Base):
    __tablename__ = "dim_time"

    time_id: Mapped[int] = mapped_column(primary_key=True)
    full_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=False)
    month_name: Mapped[str] = mapped_column(String(20), nullable=False)
    quarter: Mapped[int] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False, index=True)


class DimRegion(Base):
    __tablename__ = "dim_region"

    region_id: Mapped[int] = mapped_column(primary_key=True)
    region_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    region_name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    is_domestic: Mapped[bool] = mapped_column(Boolean, nullable=False)


class DimSegment(Base):
    __tablename__ = "dim_segment"

    segment_id: Mapped[int] = mapped_column(primary_key=True)
    segment_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    segment_name: Mapped[str] = mapped_column(String(100), nullable=False)


class DimProduct(Base):
    __tablename__ = "dim_product"

    product_id: Mapped[int] = mapped_column(primary_key=True)
    product_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    product_category: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    principal_name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_industry: Mapped[str | None] = mapped_column(String(100))


class DimCustomer(Base):
    __tablename__ = "dim_customer"

    customer_id: Mapped[int] = mapped_column(primary_key=True)
    customer_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    customer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    industry_segment: Mapped[str] = mapped_column(String(100), nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("dim_region.region_id"), nullable=False, index=True)


class DimEmployee(Base):
    __tablename__ = "dim_employee"

    employee_id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    segment_id: Mapped[int] = mapped_column(ForeignKey("dim_segment.segment_id"), nullable=False, index=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("dim_region.region_id"), nullable=False, index=True)


class DimWarehouse(Base):
    __tablename__ = "dim_warehouse"

    warehouse_id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    warehouse_name: Mapped[str] = mapped_column(String(150), nullable=False)
    warehouse_type: Mapped[str] = mapped_column(String(50), nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("dim_region.region_id"), nullable=False, index=True)


class DimPlant(Base):
    __tablename__ = "dim_plant"

    plant_id: Mapped[int] = mapped_column(primary_key=True)
    plant_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    plant_name: Mapped[str] = mapped_column(String(150), nullable=False)
    plant_type: Mapped[str] = mapped_column(String(50), nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("dim_region.region_id"), nullable=False, index=True)


class FactSales(Base):
    __tablename__ = "fact_sales"

    sales_fact_id: Mapped[int] = mapped_column(primary_key=True)
    time_id: Mapped[int] = mapped_column(ForeignKey("dim_time.time_id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("dim_product.product_id"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("dim_customer.customer_id"), nullable=False, index=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("dim_region.region_id"), nullable=False, index=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("dim_segment.segment_id"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("dim_employee.employee_id"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("dim_warehouse.warehouse_id"), nullable=False, index=True)
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    gross_margin_pct: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)


class FactProduction(Base):
    __tablename__ = "fact_production"

    production_fact_id: Mapped[int] = mapped_column(primary_key=True)
    time_id: Mapped[int] = mapped_column(ForeignKey("dim_time.time_id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("dim_product.product_id"), nullable=False, index=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("dim_plant.plant_id"), nullable=False, index=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("dim_segment.segment_id"), nullable=False, index=True)
    planned_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    actual_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    yield_pct: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    total_production_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class FactInventory(Base):
    __tablename__ = "fact_inventory"

    inventory_fact_id: Mapped[int] = mapped_column(primary_key=True)
    time_id: Mapped[int] = mapped_column(ForeignKey("dim_time.time_id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("dim_product.product_id"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("dim_warehouse.warehouse_id"), nullable=False, index=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("dim_segment.segment_id"), nullable=False, index=True)
    opening_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    closing_qty: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    inventory_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class FactShipment(Base):
    __tablename__ = "fact_shipment"

    shipment_fact_id: Mapped[int] = mapped_column(primary_key=True)
    time_id: Mapped[int] = mapped_column(ForeignKey("dim_time.time_id"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("dim_customer.customer_id"), nullable=False, index=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("dim_region.region_id"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("dim_warehouse.warehouse_id"), nullable=False, index=True)
    shipping_method: Mapped[str] = mapped_column(String(50), nullable=False)
    freight_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    on_time_flag: Mapped[bool] = mapped_column(Boolean, nullable=False)
