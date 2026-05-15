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

After `uv` is installed, run these commands from the project folder:

### 1. Sync dependencies

```bash
uv sync
```

## Run Database Migrations

To create or update the database schema with Alembic:

### 1. Copy the environment file

```bash
cp .env.example .env
```

If you are using Windows PowerShell, you can use:

```powershell
Copy-Item .env.example .env
```

### 2. Fill in your database URL

Open `.env` and set your `DATABASE_URL`.

Example:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/data_warehouse
```

### 3. Run the migration

```bash
alembic -c alembic/alembic.ini upgrade head
```
