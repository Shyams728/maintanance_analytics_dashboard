
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kpi_calculations import calculate_mttr, calculate_mtbf, calculate_schedule_compliance
from advanced_analytics import predict_failure_probability
from styles import (
    inject_custom_css, COLORS, format_currency, style_plotly_chart,
    section_header
)

import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Maintenance Operations",
    page_icon="🛠️",
    layout="wide"
)

inject_custom_css()

st.title("🛠️ Maintenance Operations")
st.markdown("**Reliability analytics, failure analysis, and work order management**")

# Handle relative paths for portability
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


@st.cache_data
def load_data():
    df_wo = pd.read_csv(os.path.join(DATA_DIR, "Fact_Maintenance_WorkOrders_Enriched.csv"))
    df_wo['Date'] = pd.to_datetime(df_wo['Date'])
    df_equip = pd.read_csv(os.path.join(DATA_DIR, "Dim_Equipment.csv"))
    df_tech = pd.read_csv(os.path.join(DATA_DIR, "Dim_Technician.csv"))
    
    # Merge for analysis
    df = pd.merge(df_wo, df_equip, on="EquipmentID")
    df = pd.merge(df, df_tech, on="TechnicianID")
    
    try:
        df_sensor = pd.read_csv(os.path.join(DATA_DIR, "Fact_Sensor_Readings.csv"))
    except:
        df_sensor = pd.DataFrame()
        
    return df, df_equip, df_sensor


df, df_equip, df_sensor = load_data()

# =============================================================================
# SIDEBAR FILTERS
# =============================================================================

st.sidebar.header("🔍 Filters")

# Equipment filter
selected_equip = st.sidebar.selectbox(
    "Select Equipment", 
    ["All"] + list(df['EquipmentName'].unique())
)
if selected_equip != "All":
    df = df[df['EquipmentName'] == selected_equip]

# Maintenance type filter
selected_type = st.sidebar.selectbox(
    "Maintenance Type",
    ["All", "Preventive", "Breakdown"]
)
if selected_type != "All":
    df = df[df['MaintenanceType'] == selected_type]

# Date range
min_date = df['Date'].min()
max_date = df['Date'].max()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date.date(), max_date.date())
)
if len(date_range) == 2:
    df = df[(df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])]

# =============================================================================
# KPI SUMMARY
# =============================================================================

st.markdown("---")
section_header("Maintenance KPIs", "📊")

col1, col2, col3, col4, col5, col6 = st.columns(6)

breakdown_df = df[df['MaintenanceType'] == 'Breakdown']
preventive_df = df[df['MaintenanceType'] == 'Preventive']

with col1:
    total_wo = len(df)
    st.metric("Total Work Orders", total_wo)

with col2:
    breakdown_count = len(breakdown_df)
    st.metric("Breakdowns", breakdown_count, 
              delta=f"{(breakdown_count/total_wo*100):.1f}% of total" if total_wo > 0 else "0%",
              delta_color="inverse")

with col3:
    avg_mttr = breakdown_df['DowntimeHours'].mean() if not breakdown_df.empty else 0
    st.metric("Avg MTTR", f"{avg_mttr:.1f} hrs")

with col4:
    total_downtime = df['DowntimeHours'].sum()
    st.metric("Total Downtime", f"{total_downtime:,.0f} hrs")

with col5:
    total_cost = df['TotalCost'].sum()
    st.metric("Total Cost", format_currency(total_cost))

with col6:
    compliance = calculate_schedule_compliance(df)
    st.metric(
        "Schedule Compliance", 
        f"{compliance['Compliance_Pct']:.1f}%",
        delta=f"{compliance['Late_Count']} Late WOs",
        delta_color="inverse"
    )

# =============================================================================
# PROACTIVE MAINTENANCE (NEW)
# =============================================================================
if not df_sensor.empty:
    st.markdown("---")
    section_header("Proactive Maintenance Alerts", "🛡️")
    
    col_pred_1, col_pred_2 = st.columns([2, 1])
    
    with col_pred_1:
        st.subheader("Predictive Failure Analysis")
        
        health_df = predict_failure_probability(df_sensor)
        health_df = health_df.merge(df_equip[['EquipmentID', 'EquipmentName']], on='EquipmentID', how='left')
        
        risky_eq = health_df[health_df['Failure_Probability'] > 20].sort_values('Failure_Probability', ascending=False)
        
        if not risky_eq.empty:
            st.dataframe(
                risky_eq[['EquipmentName', 'Failure_Probability', 'Avg_Temp', 'Max_Vibration', 'Insight']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Failure_Probability": st.column_config.ProgressColumn(
                        "Risk Probability",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "Avg_Temp": st.column_config.NumberColumn("Avg Temp (°C)"),
                    "Max_Vibration": st.column_config.NumberColumn("Vibration (mm/s)")
                }
            )
        else:
            st.success("✅ No high-risk equipment detected by predictive models.")
            
    with col_pred_2:
        st.subheader("Risk Distribution")
        if not health_df.empty:
            fig_pie = px.pie(
                health_df,
                names='Status',
                color='Status',
                color_discrete_map={'Healthy': COLORS['success'], 'Warning': COLORS['warning'], 'Critical': COLORS['danger']},
                hole=0.5
            )
            fig_pie.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

# =============================================================================
# PARETO ANALYSIS
# =============================================================================

st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    section_header("Failure Mode Pareto Analysis", "📉")
    
    if not breakdown_df.empty and breakdown_df['FailureCode'].notna().any():
        # Prepare Pareto data
        failure_counts = breakdown_df['FailureCode'].value_counts().reset_index()
        failure_counts.columns = ['FailureCode', 'Count']
        failure_counts['Cumulative'] = failure_counts['Count'].cumsum()
        failure_counts['Cumulative_Pct'] = (failure_counts['Cumulative'] / failure_counts['Count'].sum()) * 100
        
        # Create Pareto chart
        fig = go.Figure()
        
        # Bars
        fig.add_trace(go.Bar(
            x=failure_counts['FailureCode'],
            y=failure_counts['Count'],
            name='Failure Count',
            marker_color=COLORS['primary']
        ))
        
        # Cumulative line
        fig.add_trace(go.Scatter(
            x=failure_counts['FailureCode'],
            y=failure_counts['Cumulative_Pct'],
            name='Cumulative %',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color=COLORS['danger'], width=2),
            marker=dict(size=8)
        ))
        
        # 80% threshold line
        fig.add_hline(
            y=80, 
            line_dash="dash", 
            line_color=COLORS['warning'],
            annotation_text="80% Threshold",
            yref='y2'
        )
        
        fig.update_layout(
            yaxis=dict(title='Count', side='left'),
            yaxis2=dict(title='Cumulative %', side='right', overlaying='y', range=[0, 105]),
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        
        fig = style_plotly_chart(fig, height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No failure data available for Pareto analysis.")

with col_right:
    section_header("MTTR vs MTBF Quadrant", "🎯")
    
    # Calculate MTTR and MTBF per equipment
    mttr_data = calculate_mttr(df)
    mtbf_data = calculate_mtbf(df)
    
    if not mttr_data.empty and not mtbf_data.empty:
        # Merge data
        quadrant_data = mttr_data.merge(mtbf_data, on='EquipmentID', how='outer').fillna(0)
        quadrant_data = quadrant_data.merge(
            df_equip[['EquipmentID', 'EquipmentName']], 
            on='EquipmentID'
        )
        
        # Define thresholds
        mttr_threshold = quadrant_data['MTTR_Hours'].median()
        mtbf_threshold = quadrant_data['MTBF_Hours'].median()
        
        # Create scatter plot
        fig = px.scatter(
            quadrant_data,
            x='MTBF_Hours',
            y='MTTR_Hours',
            size='Breakdown_Count',
            color='EquipmentName',
            hover_data=['EquipmentName', 'Breakdown_Count'],
            labels={
                'MTBF_Hours': 'MTBF (Hours) →',
                'MTTR_Hours': 'MTTR (Hours) →'
            }
        )
        
        # Add quadrant lines
        fig.add_hline(y=mttr_threshold, line_dash="dash", line_color=COLORS['gray'])
        fig.add_vline(x=mtbf_threshold, line_dash="dash", line_color=COLORS['gray'])
        
        # Add quadrant labels
        fig.add_annotation(x=mtbf_threshold*1.5, y=mttr_threshold*0.5, 
                          text="🟢 High Reliability", showarrow=False, font=dict(size=10))
        fig.add_annotation(x=mtbf_threshold*0.5, y=mttr_threshold*1.5, 
                          text="🔴 Priority Focus", showarrow=False, font=dict(size=10))
        
        fig = style_plotly_chart(fig, height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data for MTTR/MTBF analysis.")

# =============================================================================
# COST COMPARISON
# =============================================================================

st.markdown("---")
col_left2, col_right2 = st.columns(2)

with col_left2:
    section_header("Cost by Maintenance Type", "💵")
    
    cost_by_type = df.groupby('MaintenanceType').agg({
        'TotalCost': 'sum',
        'WorkOrderID': 'count'
    }).reset_index()
    cost_by_type.columns = ['Type', 'Total Cost', 'Count']
    
    fig = px.bar(
        cost_by_type,
        x='Type',
        y='Total Cost',
        color='Type',
        color_discrete_map={'Preventive': COLORS['success'], 'Breakdown': COLORS['danger']},
        text='Count'
    )
    
    fig.update_traces(texttemplate='%{text} WOs', textposition='outside')
    fig.update_layout(showlegend=False)
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right2:
    section_header("Downtime by Equipment", "⏱️")
    
    downtime_by_equip = df.groupby('EquipmentName')['DowntimeHours'].sum().reset_index()
    downtime_by_equip = downtime_by_equip.sort_values('DowntimeHours', ascending=True)
    
    fig = px.bar(
        downtime_by_equip,
        x='DowntimeHours',
        y='EquipmentName',
        orientation='h',
        color='DowntimeHours',
        color_continuous_scale='RdYlGn_r'
    )
    
    fig.update_layout(
        xaxis_title='Total Downtime (Hours)',
        yaxis_title='',
        coloraxis_showscale=False
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# DECOMPOSITION TREE (SUNBURST)
# =============================================================================

st.markdown("---")
section_header("Downtime Decomposition Analysis", "🌳")

if not df.empty and df['FailureCode'].notna().any():
    # Filter for breakdown work orders with failure codes
    decomp_df = df[df['FailureCode'].notna()].copy()
    
    fig_sun = px.sunburst(
        decomp_df, 
        path=['EquipmentName', 'FailureCode', 'Maintenance Category'], 
        values='DowntimeHours',
        color='DowntimeHours',
        color_continuous_scale='RdYlGn_r',
        title="Equipment → Failure Code → Category"
    )
    
    fig_sun = style_plotly_chart(fig_sun, height=500)
    st.plotly_chart(fig_sun, use_container_width=True)
else:
    st.info("No failure data available for decomposition analysis.")

# =============================================================================
# WORK ORDER TABLE
# =============================================================================

st.markdown("---")
section_header("Recent Work Orders", "📋")

# Show most recent work orders
recent_wo = df.sort_values('Date', ascending=False).head(10)

display_cols = ['Date', 'WorkOrderID', 'EquipmentName', 'MaintenanceType', 
                'FailureCode', 'DowntimeHours', 'LaborHours', 'TotalCost', 'Name']

st.dataframe(
    recent_wo[display_cols].rename(columns={'Name': 'Technician'}),
    use_container_width=True,
    hide_index=True
)
