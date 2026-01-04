
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kpi_calculations import calculate_payment_variance, calculate_budget_adherence
from styles import (
    inject_custom_css, COLORS, format_currency, style_plotly_chart,
    section_header
)

import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Cost & Vendor Analysis",
    page_icon="💰",
    layout="wide"
)

inject_custom_css()

st.title("💰 Cost & Vendor Analysis")
st.markdown("**Vendor performance, payment variance, and budget adherence tracking**")

DATA_DIR = "d:/data_science/power_bi/data"


@st.cache_data
def load_data():
    df_costs = pd.read_csv(os.path.join(DATA_DIR, "Fact_Costs.csv"))
    df_budget = pd.read_csv(os.path.join(DATA_DIR, "Fact_Budget_vs_Actual.csv"))
    df_budget['Date'] = pd.to_datetime(df_budget['Date'])
    df_vendor = pd.read_csv(os.path.join(DATA_DIR, "Dim_Vendor.csv"))
    return df_costs, df_budget, df_vendor


df_costs, df_budget, df_vendor = load_data()

# =============================================================================
# KPI CALCULATIONS
# =============================================================================

payment_variance = calculate_payment_variance(df_costs)
budget_adherence = calculate_budget_adherence(df_budget)

# Merge vendor names
payment_variance = payment_variance.merge(
    df_vendor[['VendorID', 'VendorName', 'Rating', 'Category']], 
    on='VendorID'
)

# =============================================================================
# SIDEBAR FILTERS
# =============================================================================

st.sidebar.header("🔍 Filters")

# Cost Center filter
cost_centers = ["All"] + list(df_budget['CostCenter'].unique())
selected_cc = st.sidebar.selectbox("Cost Center", cost_centers)

if selected_cc != "All":
    df_budget_filtered = df_budget[df_budget['CostCenter'] == selected_cc]
else:
    df_budget_filtered = df_budget

# Vendor filter
vendors = ["All"] + list(df_vendor['VendorName'].unique())
selected_vendor = st.sidebar.selectbox("Vendor", vendors)

# =============================================================================
# KPI CARDS
# =============================================================================

st.markdown("---")
section_header("Cost Management KPIs", "📊")

total_contract = df_costs['ContractValue'].sum()
total_actual = df_costs['ActualPayment'].sum()
total_variance = total_actual - total_contract
variance_pct = (total_variance / total_contract) * 100 if total_contract > 0 else 0

total_budget = df_budget_filtered['BudgetAmount'].sum()
total_actual_budget = df_budget_filtered['ActualAmount'].sum()
budget_variance = total_actual_budget - total_budget
budget_var_pct = (budget_variance / total_budget) * 100 if total_budget > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Contract Value", format_currency(total_contract))

with col2:
    st.metric("Total Actual Paid", format_currency(total_actual))

with col3:
    delta_color = "inverse" if total_variance > 0 else "normal"
    st.metric(
        "Payment Variance", 
        format_currency(abs(total_variance)),
        delta=f"{variance_pct:+.1f}%",
        delta_color=delta_color
    )

with col4:
    st.metric("Total Budget", format_currency(total_budget))

with col5:
    budget_delta_color = "inverse" if budget_variance > 0 else "normal"
    st.metric(
        "Budget Variance",
        format_currency(abs(budget_variance)),
        delta=f"{budget_var_pct:+.1f}%",
        delta_color=budget_delta_color
    )

# =============================================================================
# VENDOR ANALYSIS
# =============================================================================

st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    section_header("Vendor Payment Variance", "📊")
    
    # Filter by selected vendor if not All
    display_variance = payment_variance if selected_vendor == "All" else \
        payment_variance[payment_variance['VendorName'] == selected_vendor]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Contract Value',
        x=display_variance['VendorName'],
        y=display_variance['Total_Contract'],
        marker_color=COLORS['primary_light']
    ))
    
    fig.add_trace(go.Bar(
        name='Actual Payment',
        x=display_variance['VendorName'],
        y=display_variance['Total_Actual'],
        marker_color=COLORS['primary_dark']
    ))
    
    fig.update_layout(
        barmode='group',
        xaxis_title="Vendor",
        yaxis_title="Amount (₹)",
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    section_header("Vendor Scorecard", "⭐")
    
    # Create vendor scorecard
    scorecard = payment_variance[['VendorName', 'Rating', 'Category', 
                                   'Total_Contract', 'Variance_Pct', 'Status']].copy()
    
    scorecard['Contract'] = scorecard['Total_Contract'].apply(format_currency)
    scorecard['Variance'] = scorecard['Variance_Pct'].apply(lambda x: f"{x:+.1f}%")
    
    # Color code status
    def get_status_emoji(status):
        if status == 'Over Budget':
            return '🔴 ' + status
        elif status == 'Under Budget':
            return '🟢 ' + status
        else:
            return '🟡 ' + status
    
    scorecard['Status'] = scorecard['Status'].apply(get_status_emoji)
    
    st.dataframe(
        scorecard[['VendorName', 'Rating', 'Category', 'Contract', 'Variance', 'Status']],
        use_container_width=True,
        hide_index=True
    )

# =============================================================================
# BUDGET ANALYSIS
# =============================================================================

st.markdown("---")
col_left2, col_right2 = st.columns(2)

with col_left2:
    section_header("Budget vs Actual by Cost Center", "🏢")
    
    cc_summary = df_budget_filtered.groupby('CostCenter').agg({
        'BudgetAmount': 'sum',
        'ActualAmount': 'sum'
    }).reset_index()
    cc_summary['Variance'] = cc_summary['ActualAmount'] - cc_summary['BudgetAmount']
    cc_summary['Variance_Pct'] = (cc_summary['Variance'] / cc_summary['BudgetAmount']) * 100
    
    fig = px.bar(
        cc_summary,
        x='CostCenter',
        y=['BudgetAmount', 'ActualAmount'],
        barmode='group',
        color_discrete_map={'BudgetAmount': COLORS['primary_light'], 
                           'ActualAmount': COLORS['primary_dark']}
    )
    
    fig.update_layout(
        xaxis_title="Cost Center",
        yaxis_title="Amount (₹)",
        legend_title=""
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right2:
    section_header("Expense Breakdown (Treemap)", "🌳")
    
    fig = px.treemap(
        df_budget_filtered,
        path=['CostCenter', 'GLAccount'],
        values='ActualAmount',
        color='ActualAmount',
        color_continuous_scale='RdYlGn_r'
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# MONTHLY TREND
# =============================================================================

st.markdown("---")
section_header("Monthly Budget Trend", "📈")

monthly_trend = df_budget_filtered.groupby(df_budget_filtered['Date'].dt.to_period('M')).agg({
    'BudgetAmount': 'sum',
    'ActualAmount': 'sum'
}).reset_index()
monthly_trend['Date'] = monthly_trend['Date'].astype(str)
monthly_trend['Variance'] = monthly_trend['ActualAmount'] - monthly_trend['BudgetAmount']

fig = go.Figure()

fig.add_trace(go.Bar(
    name='Budget',
    x=monthly_trend['Date'],
    y=monthly_trend['BudgetAmount'],
    marker_color=COLORS['primary_light'],
    opacity=0.7
))

fig.add_trace(go.Scatter(
    name='Actual',
    x=monthly_trend['Date'],
    y=monthly_trend['ActualAmount'],
    mode='lines+markers',
    line=dict(color=COLORS['primary_dark'], width=3),
    marker=dict(size=8)
))

# Add variance indicators
colors = [COLORS['danger'] if v > 0 else COLORS['success'] for v in monthly_trend['Variance']]
fig.add_trace(go.Bar(
    name='Variance',
    x=monthly_trend['Date'],
    y=monthly_trend['Variance'],
    marker_color=colors,
    opacity=0.5,
    yaxis='y2'
))

fig.update_layout(
    yaxis=dict(title='Amount (₹)'),
    yaxis2=dict(title='Variance', overlaying='y', side='right'),
    hovermode='x unified',
    legend=dict(orientation='h', yanchor='bottom', y=1.02)
)

fig = style_plotly_chart(fig, height=400)
st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# VARIANCE DETAILS TABLE
# =============================================================================

st.markdown("---")
section_header("Budget Adherence Details", "📋")

adherence_display = budget_adherence.copy()
adherence_display['Budget'] = adherence_display['Total_Budget'].apply(format_currency)
adherence_display['Actual'] = adherence_display['Total_Actual'].apply(format_currency)
adherence_display['Variance'] = adherence_display['Variance'].apply(lambda x: format_currency(abs(x)))
adherence_display['Var %'] = adherence_display['Variance_Pct'].apply(lambda x: f"{x:+.1f}%")

# Filter if cost center selected
if selected_cc != "All":
    adherence_display = adherence_display[adherence_display['CostCenter'] == selected_cc]

st.dataframe(
    adherence_display[['CostCenter', 'GLAccount', 'Budget', 'Actual', 'Variance', 'Var %']],
    use_container_width=True,
    hide_index=True
)
