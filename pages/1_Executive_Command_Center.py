
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kpi_calculations import (
    calculate_mttr, calculate_mtbf, calculate_equipment_availability,
    calculate_maintenance_mix, get_executive_summary
)
from advanced_analytics import predict_failure_probability, forecast_maintenance_costs
from styles import (
    inject_custom_css, COLORS, format_currency, style_plotly_chart,
    get_gauge_color, section_header
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
st.markdown("**Real-time operational insights for plant management decisions**")

# Handle relative paths for portability
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


@st.cache_data
def load_data():
    df_wo = pd.read_csv(os.path.join(DATA_DIR, "Fact_Maintenance_WorkOrders_Enriched.csv"))
    df_wo['Date'] = pd.to_datetime(df_wo['Date'])
    
    df_prod = pd.read_csv(os.path.join(DATA_DIR, "Dim_Product_Enriched.csv"))
    df_budget = pd.read_csv(os.path.join(DATA_DIR, "Fact_Budget_vs_Actual.csv"))
    df_budget['Date'] = pd.to_datetime(df_budget['Date'])
    
    df_equip = pd.read_csv(os.path.join(DATA_DIR, "Dim_Equipment.csv"))
    
    try:
        df_sensor = pd.read_csv(os.path.join(DATA_DIR, "Fact_Sensor_Readings.csv"))
    except:
        df_sensor = pd.DataFrame()
    
    return df_wo, df_prod, df_budget, df_equip, df_sensor


try:
    df_wo, df_prod, df_budget, df_equip, df_sensor = load_data()
except FileNotFoundError as e:
    st.error(f"Data not found: {e}. Please run `python preprocess_data.py` first.")
    st.stop()

# =============================================================================
# SIDEBAR FILTERS
# =============================================================================

st.sidebar.header("🔍 Filters")

# Date range filter
min_date = df_wo['Date'].min().date()
max_date = df_wo['Date'].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_wo_filtered = df_wo[(df_wo['Date'].dt.date >= start_date) & 
                           (df_wo['Date'].dt.date <= end_date)]
else:
    df_wo_filtered = df_wo

# Equipment filter
equipment_options = ['All'] + list(df_equip['EquipmentName'].unique())
selected_equipment = st.sidebar.selectbox("Equipment", equipment_options)

if selected_equipment != 'All':
    equip_id = df_equip[df_equip['EquipmentName'] == selected_equipment]['EquipmentID'].values[0]
    df_wo_filtered = df_wo_filtered[df_wo_filtered['EquipmentID'] == equip_id]

# =============================================================================
# CALCULATE KPIs
# =============================================================================

summary = get_executive_summary(df_wo_filtered, None, df_prod)
availability = calculate_equipment_availability(df_wo_filtered, len(df_equip))
maintenance_mix = calculate_maintenance_mix(df_wo_filtered)

# =============================================================================
# KPI CARDS ROW
# =============================================================================

st.markdown("---")
section_header("Key Performance Indicators", "🎯")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Total Maintenance Cost",
        value=format_currency(summary['Total_Maintenance_Cost']),
        delta=None
    )

with col2:
    st.metric(
        label="Equipment Availability",
        value=f"{availability['Availability_Pct']:.1f}%",
        delta="Target: 95%",
        delta_color="off"
    )

with col3:
    st.metric(
        label="MTTR (Avg)",
        value=f"{summary['MTTR_Hours']:.1f} hrs",
        delta="Lower is better",
        delta_color="off"
    )

with col4:
    st.metric(
        label="MTBF (Avg)",
        value=f"{summary['MTBF_Hours']:.0f} hrs",
        delta="Higher is better",
        delta_color="off"
    )

with col5:
    st.metric(
        label="Preventive Ratio",
        value=f"{summary['Preventive_Pct']:.1f}%",
        delta=f"{summary['Breakdown_Count']} breakdowns",
        delta_color="inverse"
    )

# =============================================================================
# PLANT HEALTH HEATMAP (NEW)
# =============================================================================
if not df_sensor.empty:
    st.markdown("---")
    section_header("Plant Health Insights", "🏥")
    
    # Calculate failure probability
    health_data = predict_failure_probability(df_sensor)
    
    # Merge with equipment names
    health_data = health_data.merge(df_equip[['EquipmentID', 'EquipmentName']], on='EquipmentID', how='left')
    
    col_map, col_details = st.columns([1, 1])
    
    with col_map:
        st.subheader("Equipment Condition Heatmap")
        
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
        
        fig_heat.update_traces(textposition='top center')
        fig_heat.update_layout(
            height=400,
            xaxis=dict(showgrid=True, zeroline=False),
            yaxis=dict(showgrid=True, zeroline=False)
        )
        
        st.plotly_chart(fig_heat, use_container_width=True)
        
    with col_details:
        st.subheader("⚠️ Predictive Alerts")
        alerts = health_data[health_data['Status'] != 'Healthy'].sort_values('Failure_Probability', ascending=False)
        
        if not alerts.empty:
            for _, row in alerts.iterrows():
                if row['Status'] == 'Critical':
                    st.error(f"**{row['EquipmentName']}**: {row['Insight']} (Risk: {row['Failure_Probability']}%)")
                else:
                    st.warning(f"**{row['EquipmentName']}**: {row['Insight']} (Risk: {row['Failure_Probability']}%)")
        else:
            st.success("All monitored equipment operating within normal parameters.")

# =============================================================================
# SECOND ROW - MINI METRICS
# =============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Work Orders (Total)",
        value=summary['Total_Work_Orders']
    )

with col2:
    st.metric(
        label="Preventive Cost",
        value=format_currency(summary['Preventive_Cost'])
    )

with col3:
    st.metric(
        label="Breakdown Cost",
        value=format_currency(summary['Breakdown_Cost'])
    )

with col4:
    critical_items = summary['Critical_Stock_Items']
    st.metric(
        label="Critical Stock Items",
        value=critical_items,
        delta="Needs attention" if critical_items > 0 else "All healthy",
        delta_color="inverse" if critical_items > 0 else "normal"
    )

# =============================================================================
# CHARTS ROW 1
# =============================================================================

st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    section_header("Budget vs Actual Trend", "📈")
    
    # Aggregate Budget Data by month
    budget_monthly = df_budget.groupby(df_budget['Date'].dt.to_period('M')).agg({
        'BudgetAmount': 'sum',
        'ActualAmount': 'sum'
    }).reset_index()
    budget_monthly['Date'] = budget_monthly['Date'].astype(str)
    budget_monthly['Variance'] = budget_monthly['ActualAmount'] - budget_monthly['BudgetAmount']
    budget_monthly['Variance_Pct'] = (budget_monthly['Variance'] / budget_monthly['BudgetAmount']) * 100
    
    chart_data = budget_monthly.copy()
    
    # Add Forecast
    forecast = forecast_maintenance_costs(df_budget)
    forecast['Date'] = forecast['Date'].astype(str)
    
    # Plot
    fig = go.Figure()
    
    # Budget Bar
    fig.add_trace(go.Bar(
        name='Budget', 
        x=chart_data['Date'], 
        y=chart_data['BudgetAmount'],
        marker_color=COLORS['primary_light'],
        opacity=0.5
    ))
    
    # Actual Line
    fig.add_trace(go.Scatter(
        name='Actual', 
        x=chart_data['Date'], 
        y=chart_data['ActualAmount'], 
        mode='lines+markers',
        line=dict(color=COLORS['primary_dark'], width=3),
        marker=dict(size=8)
    ))
    
    # Forecast Line
    fig.add_trace(go.Scatter(
        name='Forecast',
        x=forecast['Date'],
        y=forecast['ForecastAmount'],
        mode='lines+markers',
        line=dict(color=COLORS['warning'], width=3, dash='dash'),
        marker=dict(symbol='star', size=8)
    ))
    
    # Forecast Confidence Interval
    fig.add_trace(go.Scatter(
        name='Upper Bound',
        x=forecast['Date'],
        y=forecast['UpperBound'],
        mode='lines',
        marker=dict(color="#444"),
        line=dict(width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        name='Lower Bound',
        x=forecast['Date'],
        y=forecast['LowerBound'],
        marker=dict(color="#444"),
        line=dict(width=0),
        mode='lines',
        fillcolor='rgba(243, 156, 18, 0.2)',
        fill='tonexty',
        showlegend=False
    ))
    
    fig.update_layout(
        barmode='group',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        title="Cost Trend & Forecast"
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    section_header("Equipment Availability Gauge", "⚙️")
    
    availability_value = availability['Availability_Pct']
    gauge_color = get_gauge_color(availability_value, (85, 95))
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=availability_value,
        number={'suffix': '%', 'font': {'size': 40}},
        delta={'reference': 95, 'increasing': {'color': COLORS['success']}},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Plant Availability", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': gauge_color},
            'bgcolor': 'white',
            'borderwidth': 2,
            'bordercolor': COLORS['gray'],
            'steps': [
                {'range': [0, 70], 'color': 'rgba(231, 76, 60, 0.2)'},
                {'range': [70, 90], 'color': 'rgba(243, 156, 18, 0.2)'},
                {'range': [90, 100], 'color': 'rgba(46, 204, 113, 0.2)'}
            ],
            'threshold': {
                'line': {'color': COLORS['danger'], 'width': 4},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))
    
    fig_gauge = style_plotly_chart(fig_gauge, height=350)
    st.plotly_chart(fig_gauge, use_container_width=True)

# =============================================================================
# CHARTS ROW 2
# =============================================================================

col_left2, col_right2 = st.columns(2)

with col_left2:
    section_header("Maintenance Cost Distribution", "💰")
    
    cost_data = pd.DataFrame({
        'Type': ['Preventive', 'Breakdown'],
        'Cost': [summary['Preventive_Cost'], summary['Breakdown_Cost']],
        'Count': [maintenance_mix['Preventive_Count'], maintenance_mix['Breakdown_Count']]
    })
    
    fig_pie = px.pie(
        cost_data, 
        values='Cost', 
        names='Type',
        color='Type',
        color_discrete_map={'Preventive': COLORS['success'], 'Breakdown': COLORS['danger']},
        hole=0.4
    )
    
    fig_pie.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Cost: ₹%{value:,.0f}<br>Share: %{percent}'
    )
    
    fig_pie = style_plotly_chart(fig_pie, height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right2:
    section_header("Monthly Maintenance Trend", "📅")
    
    df_wo_filtered['Month'] = df_wo_filtered['Date'].dt.to_period('M').astype(str)
    
    monthly_trend = df_wo_filtered.groupby(['Month', 'MaintenanceType']).agg({
        'TotalCost': 'sum',
        'WorkOrderID': 'count'
    }).reset_index()
    
    fig_trend = px.bar(
        monthly_trend,
        x='Month',
        y='TotalCost',
        color='MaintenanceType',
        barmode='stack',
        color_discrete_map={'Preventive': COLORS['success'], 'Breakdown': COLORS['danger']}
    )
    
    fig_trend.update_layout(
        xaxis_title='Month',
        yaxis_title='Total Cost (₹)',
        legend_title='Type'
    )
    
    fig_trend = style_plotly_chart(fig_trend, height=350)
    st.plotly_chart(fig_trend, use_container_width=True)

# =============================================================================
# CRITICAL ALERTS
# =============================================================================

st.markdown("---")
section_header("⚠️ Critical Alerts & Action Items", "🚨")

# Stock alerts
critical_products = df_prod[df_prod['Stock Status'] == 'Critical']
if not critical_products.empty:
    st.warning(f"**{len(critical_products)} product(s) at critical stock level!**")
    st.dataframe(
        critical_products[['ProductID', 'ProductName', 'CurrentStock', 'ReorderPoint', 'UnitCost']],
        use_container_width=True,
        hide_index=True
    )
else:
    st.success("✅ All inventory items are at healthy stock levels.")

# Recent breakdowns
recent_breakdowns = df_wo_filtered[
    (df_wo_filtered['MaintenanceType'] == 'Breakdown') & 
    (df_wo_filtered['TotalCost'] > 15000)
].sort_values('Date', ascending=False).head(5)

if not recent_breakdowns.empty:
    st.warning(f"**{len(recent_breakdowns)} high-cost breakdown(s) in selected period**")
    st.dataframe(
        recent_breakdowns[['Date', 'EquipmentID', 'FailureCode', 'DowntimeHours', 'TotalCost']].round(2),
        use_container_width=True,
        hide_index=True
    )
