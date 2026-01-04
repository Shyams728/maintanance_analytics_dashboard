
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from styles import (
    inject_custom_css, COLORS, format_currency, style_plotly_chart,
    section_header
)

import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Technician Performance",
    page_icon="👷",
    layout="wide"
)

inject_custom_css()

st.title("👷 Technician Performance")
st.markdown("**Workforce productivity, skill analysis, and workload distribution**")

DATA_DIR = "d:/data_science/power_bi/data"


@st.cache_data
def load_data():
    df_wo = pd.read_csv(os.path.join(DATA_DIR, "Fact_Maintenance_WorkOrders_Enriched.csv"))
    df_wo['Date'] = pd.to_datetime(df_wo['Date'])
    df_tech = pd.read_csv(os.path.join(DATA_DIR, "Dim_Technician.csv"))
    df = pd.merge(df_wo, df_tech, on="TechnicianID")
    return df, df_tech


df, df_tech = load_data()

# =============================================================================
# SIDEBAR FILTERS
# =============================================================================

st.sidebar.header("🔍 Filters")

# Technician filter
technicians = ["All"] + list(df_tech['Name'].unique())
selected_tech = st.sidebar.selectbox("Technician", technicians)

if selected_tech != "All":
    df_filtered = df[df['Name'] == selected_tech]
else:
    df_filtered = df

# Skill level filter
skill_levels = ["All"] + list(df_tech['SkillLevel'].unique())
selected_skill = st.sidebar.selectbox("Skill Level", skill_levels)

if selected_skill != "All":
    df_filtered = df_filtered[df_filtered['SkillLevel'] == selected_skill]

# =============================================================================
# KPI CARDS
# =============================================================================

st.markdown("---")
section_header("Workforce KPIs", "📊")

col1, col2, col3, col4, col5 = st.columns(5)

total_technicians = df_filtered['TechnicianID'].nunique()
total_wo = len(df_filtered)
total_labor_hours = df_filtered['LaborHours'].sum()
avg_repair_time = df_filtered['LaborHours'].mean()
total_labor_cost = df_filtered['LaborCost'].sum()

with col1:
    st.metric("Active Technicians", total_technicians)

with col2:
    st.metric("Work Orders Completed", total_wo)

with col3:
    st.metric("Total Labor Hours", f"{total_labor_hours:,.0f} hrs")

with col4:
    st.metric("Avg Repair Time", f"{avg_repair_time:.1f} hrs")

with col5:
    st.metric("Labor Cost", format_currency(total_labor_cost))

# =============================================================================
# CHARTS ROW 1
# =============================================================================

st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    section_header("Average Repair Time by Technician", "⏱️")
    
    avg_repair = df_filtered.groupby(['Name', 'SkillLevel'])['LaborHours'].mean().reset_index()
    avg_repair = avg_repair.sort_values('LaborHours')
    
    team_avg = df_filtered['LaborHours'].mean()
    
    fig = px.bar(
        avg_repair,
        x='Name',
        y='LaborHours',
        color='SkillLevel',
        color_discrete_map={
            'Master': COLORS['success'],
            'Senior': COLORS['primary'],
            'Mid-Level': COLORS['warning'],
            'Junior': COLORS['info']
        }
    )
    
    fig.add_hline(
        y=team_avg, 
        line_dash="dash", 
        line_color=COLORS['danger'],
        annotation_text=f"Team Avg: {team_avg:.1f} hrs"
    )
    
    fig.update_layout(
        xaxis_title="Technician",
        yaxis_title="Avg Labor Hours",
        legend_title="Skill Level"
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    section_header("Work Order Distribution", "📊")
    
    wo_count = df_filtered['Name'].value_counts().reset_index()
    wo_count.columns = ['Name', 'Work Orders']
    
    fig = px.pie(
        wo_count,
        values='Work Orders',
        names='Name',
        hole=0.4,
        color_discrete_sequence=COLORS['chart_palette']
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# CHARTS ROW 2
# =============================================================================

col_left2, col_right2 = st.columns(2)

with col_left2:
    section_header("Technician Efficiency Matrix", "🎯")
    
    # Calculate efficiency metrics per technician
    tech_stats = df_filtered.groupby('Name').agg({
        'WorkOrderID': 'count',
        'LaborHours': 'sum',
        'TotalCost': 'sum',
        'DowntimeHours': 'mean'
    }).reset_index()
    tech_stats.columns = ['Name', 'WO_Count', 'Labor_Hours', 'Total_Cost', 'Avg_Downtime']
    
    # Merge with skill level
    tech_stats = tech_stats.merge(df_tech[['Name', 'SkillLevel', 'HourlyRate']], on='Name')
    
    # Calculate efficiency (WOs per labor hour)
    tech_stats['Efficiency'] = tech_stats['WO_Count'] / tech_stats['Labor_Hours']
    tech_stats['Avg_Hours_Per_WO'] = tech_stats['Labor_Hours'] / tech_stats['WO_Count']
    
    fig = px.scatter(
        tech_stats,
        x='WO_Count',
        y='Avg_Hours_Per_WO',
        size='Total_Cost',
        color='SkillLevel',
        hover_data=['Name', 'HourlyRate'],
        labels={
            'WO_Count': 'Work Orders Completed',
            'Avg_Hours_Per_WO': 'Avg Hours per WO'
        },
        color_discrete_map={
            'Master': COLORS['success'],
            'Senior': COLORS['primary'],
            'Mid-Level': COLORS['warning'],
            'Junior': COLORS['info']
        }
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right2:
    section_header("Monthly Productivity Trend", "📈")
    
    df_filtered['Month'] = df_filtered['Date'].dt.to_period('M').astype(str)
    
    monthly_stats = df_filtered.groupby('Month').agg({
        'WorkOrderID': 'count',
        'LaborHours': 'sum'
    }).reset_index()
    monthly_stats.columns = ['Month', 'Work_Orders', 'Labor_Hours']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Work Orders',
        x=monthly_stats['Month'],
        y=monthly_stats['Work_Orders'],
        marker_color=COLORS['primary']
    ))
    
    fig.add_trace(go.Scatter(
        name='Labor Hours',
        x=monthly_stats['Month'],
        y=monthly_stats['Labor_Hours'],
        yaxis='y2',
        mode='lines+markers',
        line=dict(color=COLORS['warning'], width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        yaxis=dict(title='Work Orders'),
        yaxis2=dict(title='Labor Hours', overlaying='y', side='right'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# SKILL ANALYSIS
# =============================================================================

st.markdown("---")
section_header("Skill Level Analysis", "🎓")

col1, col2 = st.columns(2)

with col1:
    skill_summary = df_filtered.groupby('SkillLevel').agg({
        'WorkOrderID': 'count',
        'LaborHours': 'sum',
        'TotalCost': 'sum',
        'LaborCost': 'sum'
    }).reset_index()
    skill_summary.columns = ['Skill Level', 'Work Orders', 'Labor Hours', 'Total Cost', 'Labor Cost']
    
    # Merge with hourly rates
    hourly_rates = df_tech.groupby('SkillLevel')['HourlyRate'].mean().reset_index()
    skill_summary = skill_summary.merge(hourly_rates, left_on='Skill Level', right_on='SkillLevel')
    skill_summary['Avg Rate'] = skill_summary['HourlyRate'].apply(lambda x: f"₹{x:.0f}/hr")
    
    # Format currency columns
    skill_summary['Total Cost'] = skill_summary['Total Cost'].apply(format_currency)
    skill_summary['Labor Cost'] = skill_summary['Labor Cost'].apply(format_currency)
    
    st.dataframe(
        skill_summary[['Skill Level', 'Work Orders', 'Labor Hours', 'Total Cost', 'Labor Cost', 'Avg Rate']],
        use_container_width=True,
        hide_index=True
    )

with col2:
    # Cost per WO by skill level
    cost_per_wo = df_filtered.groupby('SkillLevel').agg({
        'TotalCost': 'sum',
        'WorkOrderID': 'count'
    }).reset_index()
    cost_per_wo['Cost_Per_WO'] = cost_per_wo['TotalCost'] / cost_per_wo['WorkOrderID']
    
    fig = px.bar(
        cost_per_wo,
        x='SkillLevel',
        y='Cost_Per_WO',
        color='SkillLevel',
        color_discrete_map={
            'Master': COLORS['success'],
            'Senior': COLORS['primary'],
            'Mid-Level': COLORS['warning'],
            'Junior': COLORS['info']
        }
    )
    
    fig.update_layout(
        xaxis_title="Skill Level",
        yaxis_title="Avg Cost per Work Order (₹)",
        showlegend=False
    )
    
    fig = style_plotly_chart(fig, height=300)
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# TECHNICIAN DETAILS TABLE
# =============================================================================

st.markdown("---")
section_header("Technician Performance Details", "📋")

tech_details = df_filtered.groupby(['Name', 'SkillLevel']).agg({
    'WorkOrderID': 'count',
    'LaborHours': ['sum', 'mean'],
    'TotalCost': 'sum',
    'DowntimeHours': 'mean'
}).reset_index()

tech_details.columns = ['Name', 'Skill Level', 'Completed WOs', 'Total Hours', 'Avg Hours/WO', 'Total Cost', 'Avg Downtime']
tech_details['Total Cost'] = tech_details['Total Cost'].apply(format_currency)
tech_details['Avg Hours/WO'] = tech_details['Avg Hours/WO'].round(1)
tech_details['Avg Downtime'] = tech_details['Avg Downtime'].round(1)

st.dataframe(
    tech_details,
    use_container_width=True,
    hide_index=True
)
