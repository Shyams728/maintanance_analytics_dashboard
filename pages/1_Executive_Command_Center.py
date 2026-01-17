
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kpi_calculations import (
    get_executive_summary, calculate_oee,
    calculate_planned_maintenance_percentage
)
from advanced_analytics import get_failure_root_cause, predict_failure_probability, forecast_maintenance_costs
from styles import (
    inject_custom_css, kpi_card, get_kpi_hints,
    section_header, style_plotly_chart
)

# Filter warnings
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Executive Command Center",
    page_icon="📊",
    layout="wide"
)

inject_custom_css()

st.title("📊 Executive Command Center")
st.markdown("**Next-level insights for plant management decisions**")

# --- Data Loading ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

@st.cache_data
def load_data():
    df_wo = pd.read_csv(os.path.join(DATA_DIR, "Fact_Maintenance_WorkOrders_Enriched.csv"))
    df_wo['Date'] = pd.to_datetime(df_wo['Date'])
    df_equip = pd.read_csv(os.path.join(DATA_DIR, "Dim_Equipment.csv"))
    df_prod = pd.read_csv(os.path.join(DATA_DIR, "Dim_Product_Enriched.csv"))
    df_budget = pd.read_csv(os.path.join(DATA_DIR, "Fact_Budget_vs_Actual.csv"))
    df_budget['Date'] = pd.to_datetime(df_budget['Date'])
    df_oee_data = pd.read_csv(os.path.join(DATA_DIR, "Fact_Production_Data_Enriched.csv"))
    df_oee_data['Date'] = pd.to_datetime(df_oee_data['Date'])
    try:
        df_sensor = pd.read_csv(os.path.join(DATA_DIR, "Fact_Sensor_Readings.csv"))
    except FileNotFoundError:
        df_sensor = pd.DataFrame() # Return empty dataframe if not found
    return df_wo, df_equip, df_prod, df_budget, df_sensor, df_oee_data

try:
    df_wo, df_equip, df_prod, df_budget, df_sensor, df_oee_data = load_data()
except FileNotFoundError as e:
    st.error(f"Data not found: {e}. Please run `python generate_data.py` and `python preprocess_data.py` first.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")
min_date, max_date = df_wo['Date'].min().date(), df_wo['Date'].max().date()
date_range = st.sidebar.date_input("Date Range", (min_date, max_date), min_date, max_date)

equipment_options = ['All'] + list(df_equip['EquipmentName'].unique())
selected_equipment = st.sidebar.selectbox("Equipment", equipment_options)

# --- Filter Data ---
if len(date_range) == 2:
    start_date, end_date = date_range
    df_wo_filtered = df_wo[(df_wo['Date'].dt.date >= start_date) & (df_wo['Date'].dt.date <= end_date)]
    df_oee_filtered = df_oee_data[(df_oee_data['Date'].dt.date >= start_date) & (df_oee_data['Date'].dt.date <= end_date)]
else:
    df_wo_filtered = df_wo.copy()
    df_oee_filtered = df_oee_data.copy()

if selected_equipment != 'All':
    equip_id = df_equip[df_equip['EquipmentName'] == selected_equipment]['EquipmentID'].values[0]
    df_wo_filtered = df_wo_filtered[df_wo_filtered['EquipmentID'] == equip_id]
    df_oee_filtered = df_oee_filtered[df_oee_filtered['EquipmentID'] == equip_id]

# --- KPI Calculations ---
kpi_hints = get_kpi_hints()
summary = get_executive_summary(df_wo_filtered, None, df_prod, equipment_ids=list(df_equip['EquipmentID'].unique()))

oee_metrics = calculate_oee(df_oee_filtered)
planned_maintenance_pct = calculate_planned_maintenance_percentage(df_wo_filtered)
failure_causes = get_failure_root_cause(df_wo_filtered)

# --- Dashboard Layout ---
st.markdown("---")
section_header("Overall Performance", "🚀")

col1, col2 = st.columns(2)
with col1:
    oee_trend = df_wo_filtered.resample('M', on='Date').apply(lambda x: calculate_oee(x, len(df_equip), 30, 120, x['TotalPartsProduced'].sum(), x['GoodPartsProduced'].sum())['OEE_Pct']).fillna(0)
    sparkline = go.Figure(go.Scatter(
        x=oee_trend.index, y=oee_trend.values,
        mode='lines', fill='tozeroy', line_color='#00bfff',
    ))
    sparkline.update_layout(height=100, margin=dict(l=0, r=0, t=0, b=0),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(sparkline, use_container_width=True)
    kpi_card("OEE (Overall Equipment Effectiveness)", f"{oee_metrics['OEE_Pct']:.2f}%", kpi_hints['OEE_Pct'],
             f"A: {oee_metrics['Availability_Component']}% | P: {oee_metrics['Performance_Component']}% | Q: {oee_metrics['Quality_Component']}%")

with col2:
    st.markdown("### Top Failure Root Causes")
    if not failure_causes.empty:
        fig = px.bar(failure_causes.head(), x=failure_causes.head().values, y=failure_causes.head().index,
                     orientation='h', labels={'x': 'Number of Failures', 'y': 'Failure Code'},
                     color_discrete_sequence=['#e74c3c'])
        fig = style_plotly_chart(fig, 300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("No breakdown maintenance recorded in this period.")

st.markdown("---")
section_header("Reliability Metrics", "🛠️")
cols = st.columns(3)
with cols[0]:
    kpi_card("Availability", f"{summary['Availability_Pct']:.2f}%", kpi_hints['Availability_Pct'])
with cols[1]:
    kpi_card("MTTR (Mean Time To Repair)", f"{summary['MTTR_Hours']:.2f} hrs", kpi_hints['MTTR_Hours'])
with cols[2]:
    kpi_card("MTBF (Mean Time Between Failures)", f"{summary['MTBF_Hours']:.2f} hrs", kpi_hints['MTBF_Hours'])

st.markdown("---")
section_header("Maintenance Strategy", "🧭")
cols = st.columns(3)
with cols[0]:
    kpi_card("Planned Maintenance", f"{planned_maintenance_pct:.2f}%", kpi_hints['Planned_Maintenance_Pct'],
             f"Preventive vs. Reactive work ratio.")
with cols[1]:
    st.markdown("### Maintenance Cost Distribution")
    cost_data = pd.DataFrame({
        'Type': ['Preventive', 'Breakdown'],
        'Cost': [summary['Preventive_Cost'], summary['Breakdown_Cost']],
    })
    fig = px.pie(cost_data, values='Cost', names='Type', hole=0.5,
                 color_discrete_map={'Preventive': '#2ecc71', 'Breakdown': '#e74c3c'})
    st.plotly_chart(fig, use_container_width=True)
with cols[2]:
    st.markdown("### Downtime Analysis")
    downtime_data = pd.DataFrame({
        'Type': ['Planned', 'Unplanned'],
        'Hours': [summary['Planned_Downtime'], summary['Unplanned_Downtime']],
    })
    fig = px.pie(downtime_data, values='Hours', names='Type', hole=0.5,
                 color_discrete_map={'Planned': '#3498db', 'Unplanned': '#f39c12'})
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Expand for More Details"):
    st.markdown("---")
    section_header("Budget vs Actual Trend", "📈")
    budget_monthly = df_budget.groupby(df_budget['Date'].dt.to_period('M')).agg({
        'BudgetAmount': 'sum',
        'ActualAmount': 'sum'
    }).reset_index()
    budget_monthly['Date'] = budget_monthly['Date'].astype(str)
    forecast = forecast_maintenance_costs(df_budget)
    forecast['Date'] = forecast['Date'].astype(str)
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Budget', x=budget_monthly['Date'], y=budget_monthly['BudgetAmount'], marker_color=px.colors.qualitative.Plotly[0]))
    fig.add_trace(go.Scatter(name='Actual', x=budget_monthly['Date'], y=budget_monthly['ActualAmount'], mode='lines+markers', line=dict(color=px.colors.qualitative.Plotly[1])))
    fig.add_trace(go.Scatter(name='Forecast', x=forecast['Date'], y=forecast['ForecastAmount'], mode='lines+markers', line=dict(color=px.colors.qualitative.Plotly[2], dash='dash')))
    fig = style_plotly_chart(fig, 400)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    section_header("Critical Stock Alerts", "📦")
    critical_products = df_prod[df_prod['Stock Status'] == 'Critical']
    if not critical_products.empty:
        st.warning(f"**{len(critical_products)} product(s) at critical stock level!**")
        st.dataframe(critical_products[['ProductID', 'ProductName', 'CurrentStock', 'ReorderPoint', 'UnitCost']], use_container_width=True, hide_index=True)
    else:
        st.success("✅ All inventory items are at healthy stock levels.")

    if not df_sensor.empty:
        st.markdown("---")
        section_header("Plant Health Insights", "🏥")
        health_data = predict_failure_probability(df_sensor)
        health_data = health_data.merge(df_equip[['EquipmentID', 'EquipmentName']], on='EquipmentID', how='left')
        fig_heat = px.scatter(
            health_data,
            x='Avg_Temp',
            y='Max_Vibration',
            size='Failure_Probability',
            color='Failure_Probability',
            hover_name='EquipmentName',
            text='EquipmentName',
            color_continuous_scale=['green', 'yellow', 'red'],
            range_color=[0, 100],
            labels={'Avg_Temp': 'Avg Temperature (°C)', 'Max_Vibration': 'Max Vibration (mm/s)', 'Failure_Probability': 'Failure Risk %'}
        )
        st.plotly_chart(fig_heat, use_container_width=True)
