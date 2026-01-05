# Maintenance Analytics Dashboard 🏭

A comprehensive **Cost, Inventory, and Maintenance Management System** built with Python and Streamlit. This dashboard provides real-time insights for the Cement, Mining, and Heavy Machinery industries, focusing on equipment reliability, supply chain efficiency, and cost control.

## 🚀 Key Features

*   **Executive Command Center**: High-level KPIs including MTTR, MTBF, Availability %, and Budget Variance.
*   **Maintenance Operations**: Detailed reliability analytics, failure trend analysis, and work order management.
*   **Inventory & Supply Chain**: Stock monitoring with ABC analysis, turnover ratios, and automated reorder alerts.
*   **Technician Performance**: Workforce productivity analysis showing repair efficiency and work volume.
*   **Cost & Vendor Analysis**: Financial tracking, vendor reliability predictions, and budget adherence monitoring.
*   **Advanced Analytics**: Rule-based predictive maintenance alerts and maintenance cost forecasting.

## 🛠️ Prerequisites

*   Python 3.8+
*   The following Python packages:
    *   `streamlit`
    *   `pandas`
    *   `numpy`
    *   `plotly`

## 📦 Installation

1.  Clone this repository or navigate to the project directory.
2.  Install the required dependencies:

    ```bash
    pip install streamlit pandas numpy plotly
    ```

## ⚙️ Data Generation

This project includes a built-in data generator to create realistic dummy data for demonstration purposes (simulating the years 2024-2025).

**Step 1: Generate Raw Data**
Run the data generation script to create the base CSV files in the `data/` directory.

```bash
python generate_data.py
```

**Step 2: Preprocess & Enrich Data**
Run the preprocessing script to calculate derived metrics and create enriched datasets (e.g., `Fact_Maintenance_WorkOrders_Enriched.csv`).

```bash
python preprocess_data.py
```

> **Note**: You must run both scripts in this order before launching the dashboard for the first time.

## 📊 Running the Dashboard

Once the data is generated, you can launch the Streamlit application:

```bash
streamlit run dashboard.py
```

The dashboard will open automatically in your default web browser (usually at `http://localhost:8501`).

## 📂 Project Structure

```text
d:\data_science\power_bi\
├── dashboard.py             # Main application entry point & Executive Dashboard
├── generate_data.py         # Script to generate realistic dummy data
├── preprocess_data.py       # Script to enrich data and calculate status columns
├── kpi_calculations.py      # Core logic for KPI formulas (MTTR, MTBF, etc.)
├── advanced_analytics.py    # Predictive models and forecasting logic
├── styles.py                # CSS styling and theme configuration
├── data/                    # Directory for generated CSV data files
└── pages/                   # Additional dashboard pages
    ├── 2_Maintenance_Operations.py
    ├── 3_Inventory_Supply_Chain.py
    ├── 4_Technician_Performance.py
    └── 5_Cost_Vendor_Analysis.py
```

## 🤝 Usage Guide

*   **Navigation**: Use the sidebar to switch between different analytics modules.
*   **Filters**: Most pages include sidebar filters (e.g., Year, Month, Equipment Type) to drill down into the data.
*   **Interactivity**: Charts are interactive (powered by Plotly) - hover to see details, zoom in/out, or click legend items to toggle series.

## 🏭 Domain Context

This system is tailored for:
*   **Mining & Limestone Operations**
*   **Heavy Earth Moving Machinery (HEMM)**
*   **Preventive & Reliability Maintenance**
*   **Spare Parts Inventory Management**
