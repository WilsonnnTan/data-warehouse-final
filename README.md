# Data Warehouse Final Project

## Identity

- Name: Wilson Angelie Tan
- Project: `data-warehouse-final`

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

### 2. Run the project

```bash
uv run main.py
```