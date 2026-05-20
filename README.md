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

Ikuti langkah-langkah berikut untuk menjalankan seluruh pipeline data warehouse dari Source Data → ETL → Data Warehouse → OLAP Layer → Presentation Dashboard.

### 1. Sync Dependencies
Gunakan `uv` untuk menyinkronkan seluruh dependensi proyek (termasuk visualisasi chart seperti `matplotlib` dan `seaborn`):

```bash
uv sync
```

### 2. Konfigurasi Environment Variables
Salin file `.env.example` menjadi `.env` dan sesuaikan koneksi database PostgreSQL Anda:

```bash
# Bash
cp .env.example .env

# PowerShell
Copy-Item .env.example .env
```

Buka file `.env` dan isi `DATABASE_URL` sesuai database Anda:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/data_warehouse
```

### 3. Jalankan Migrasi Database
Gunakan Alembic untuk membuat skema dasar database (dimensi & fakta) beserta tabel OLAP (summary & data mart):

```bash
uv run alembic -c alembic/alembic.ini upgrade head
```

### 4. Jalankan Pipeline ETL
Buka dan jalankan seluruh cell di notebook `main.ipynb` untuk memproses data dari source systems (ERP, CRM, WMS, HR, dll.) lalu memuatnya (*load*) ke dalam tabel fakta dan dimensi Data Warehouse.

### 5. Build OLAP Layer (Summary Tables & Data Marts)
Setelah data warehouse terisi oleh ETL, jalankan modul pembangun OLAP untuk membuat tabel agregasi (`agg_*`) dan data mart wide denormalized (`mart_*`):

```bash
uv run python -m olap.build_olap
```
Proses ini akan:
- Menghapus dan membuat ulang tabel-tabel OLAP secara teratur.
- Menjalankan 8 kriteria **Data Quality (DQ) Checks** secara otomatis untuk memastikan konsistensi data (seperti pencocokan nilai total revenue, cost, OTD percentage, dll.).
- Menampilkan laporan ringkasan jumlah baris yang berhasil diolah.

### 6. Akses Presentation Layer (Analytic Dashboard)
Untuk menganalisis data, membuat laporan pivot table, melihat KPI scorecards, serta visualisasi charts, buka Jupyter notebook dashboard:

```bash
uv run jupyter notebook presentation/olap_dashboard.ipynb
```
Di dalam notebook ini, Anda dapat mengeksplorasi:
- **Sales Analytics:** Pivot table sales, tren pendapatan bulanan, performa per wilayah, segmentasi, serta peringkat salespersons.
- **Production Analytics:** Scorecard yield produksi per plant, grafik perbandingan rencana vs realisasi, dan tren biaya per unit produksi.
- **Inventory Analytics:** Heatmap tingkat stok (Product × Warehouse), turnover rate, dan analisis arus masuk-keluar stok.
- **Shipment & Logistics Analytics:** Rasio pengiriman tepat waktu (OTD%), biaya freight per metode pengiriman, dan kepatuhan SLA.
- **Integrated KPI Dashboard:** Executive scorecard bulanan lintas subject area.

