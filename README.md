# Data Warehouse Final Project

## Group Profile
 
**Project:** `data-warehouse-final`
 
| No | Name | Student ID |
|---|---|---|
| 1 | Wilson Angelie Tan | 140810230024 |
| 2 | Muhammad Fadhli Ramadhan Aulia | 140810230056 |
| 3 | Bim Yusuf Karang | 140810230084 |
## Project Description

This project is a data warehouse pipeline project built for a Data Warehouse course. The main goal is to prepare a foundation for collecting, transforming, and organizing data into a structured warehouse that can support reporting, analytics, and better decision-making.

In a complete data warehouse workflow, the pipeline usually covers:

- Extracting data from source systems
- Transforming and cleaning the data
- Loading the processed data into a warehouse structure
- Preparing the data for analysis and business insight

This repository uses Python and `uv` for dependency management and project execution.

## Install `uv`

If you are **not using PowerShell**, you can install `uv` with one of these commands:

### Windows Command Prompt

```bat
winget install --id=astral-sh.uv -e
```

### macOS or Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Using `pip`

If you already have Python and `pip`, you can also install it with:

```bash
pip install uv
```

## Run the Project

Follow the steps below to run the complete data warehouse pipeline from Source Data → ETL → Data Warehouse → OLAP Layer → Presentation Dashboard.

### 1. Sync Dependencies
Use `uv` to sync all project dependencies, including chart visualization libraries such as `matplotlib` and `seaborn`:

```bash
uv sync
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`, then adjust it to match your PostgreSQL database connection:

```bash
# Bash
cp .env.example .env

# PowerShell
Copy-Item .env.example .env
```

Open the `.env` file and fill in `DATABASE_URL` with your database connection string:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/data_warehouse
```

### 3. Run Database Migrations
Use Alembic to create the base database schema (dimension and fact tables) along with the OLAP tables (summary tables and data marts):

```bash
uv run alembic -c alembic/alembic.ini upgrade head
```

### 4. Run the ETL Pipeline
Open and run all cells in the `main.ipynb` notebook to process data from source systems (ERP, CRM, WMS, HR, etc.) and load it into the data warehouse fact and dimension tables.

### 5. Build OLAP Layer (Summary Tables & Data Marts)
After the data warehouse has been populated by the ETL process, run the OLAP builder module to create aggregate tables (`agg_*`) and wide denormalized data marts (`mart_*`):

```bash
uv run olap/build_olap.py
```
This process will:
- Drop and recreate the OLAP tables in a controlled manner.
- Run 8 **Data Quality (DQ) Checks** automatically to ensure data consistency, including validation of total revenue, cost, OTD percentage, and more.
- Display a summary report of the rows successfully processed.

### 6. Access the Presentation Layer (Analytic Dashboard)
To analyze the data, create pivot table reports, view KPI scorecards, and explore chart visualizations, open the dashboard Jupyter notebook:

```bash
uv run jupyter notebook presentation/olap_dashboard.ipynb
```
Inside this notebook, you can explore:
- **Sales Analytics:** Sales pivot tables, monthly revenue trends, regional performance, segmentation, and salesperson rankings.
- **Production Analytics:** Production yield scorecards by plant, planned vs. actual comparison charts, and cost-per-unit trends.
- **Inventory Analytics:** Stock level heatmaps (Product × Warehouse), turnover rates, and inbound-outbound inventory flow analysis.
- **Shipment & Logistics Analytics:** On-time delivery ratio (OTD%), freight cost by shipping method, and SLA compliance.
- **Integrated KPI Dashboard:** Monthly executive scorecards across subject areas.

