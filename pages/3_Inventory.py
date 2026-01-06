
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kpi_calculations import (
    calculate_inventory_turnover, calculate_stock_coverage_days, get_reorder_alerts
)
from styles import (
    inject_custom_css, COLORS, format_currency, style_plotly_chart,
    section_header, get_gauge_color
)

import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Inventory & Supply Chain",
    page_icon="📦",
    layout="wide"
)

inject_custom_css()

st.title("📦 Inventory & Supply Chain")
st.markdown("**Stock visibility, turnover analytics, and procurement intelligence**")

# Handle relative paths for portability
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


@st.cache_data
def load_data():
    df_prod = pd.read_csv(os.path.join(DATA_DIR, "Dim_Product_Enriched.csv"))
    df_trans = pd.read_csv(os.path.join(DATA_DIR, "Fact_Inventory_Transactions.csv"))
    df_trans['Date'] = pd.to_datetime(df_trans['Date'])
    return df_prod, df_trans


df_prod, df_trans = load_data()

# =============================================================================
# SIDEBAR FILTERS
# =============================================================================

st.sidebar.header("🔍 Filters")

# Category filter
categories = ["All"] + list(df_prod['Category'].unique())
selected_category = st.sidebar.selectbox("Category", categories)

if selected_category != "All":
    df_prod_filtered = df_prod[df_prod['Category'] == selected_category]
    product_ids = df_prod_filtered['ProductID'].tolist()
    df_trans_filtered = df_trans[df_trans['ProductID'].isin(product_ids)]
else:
    df_prod_filtered = df_prod
    df_trans_filtered = df_trans

# ABC Class filter
abc_classes = ["All"] + list(df_prod['ABC_Class'].unique())
selected_abc = st.sidebar.selectbox("ABC Classification", abc_classes)

if selected_abc != "All":
    df_prod_filtered = df_prod_filtered[df_prod_filtered['ABC_Class'] == selected_abc]

# =============================================================================
# KPI CALCULATIONS
# =============================================================================

turnover_df = calculate_inventory_turnover(df_trans_filtered, df_prod_filtered)
coverage_df = calculate_stock_coverage_days(df_trans_filtered, df_prod_filtered)
reorder_alerts = get_reorder_alerts(df_prod_filtered)

# =============================================================================
# KPI CARDS
# =============================================================================

st.markdown("---")
section_header("Inventory KPIs", "📊")

col1, col2, col3, col4, col5 = st.columns(5)

total_products = len(df_prod_filtered)
total_stock_value = (df_prod_filtered['CurrentStock'] * df_prod_filtered['UnitCost']).sum()
avg_turnover = turnover_df['Turnover_Ratio'].mean()
critical_items = len(df_prod_filtered[df_prod_filtered['Stock Status'] == 'Critical'])
healthy_items = len(df_prod_filtered[df_prod_filtered['Stock Status'] == 'Healthy'])

with col1:
    st.metric("Total Products", total_products)

with col2:
    st.metric("Inventory Value", format_currency(total_stock_value))

with col3:
    st.metric("Avg Turnover Ratio", f"{avg_turnover:.2f}x")

with col4:
    st.metric("Critical Items", critical_items, 
              delta="Needs Attention" if critical_items > 0 else "All Good",
              delta_color="inverse" if critical_items > 0 else "normal")

with col5:
    st.metric("Healthy Items", healthy_items)

# =============================================================================
# CHARTS ROW 1
# =============================================================================

st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    section_header("ABC Classification Matrix", "🏷️")
    
    # Create ABC vs Stock Status matrix
    matrix_data = df_prod_filtered.groupby(['ABC_Class', 'Stock Status']).size().reset_index(name='Count')
    
    # Pivot for heatmap
    pivot_data = matrix_data.pivot(index='Stock Status', columns='ABC_Class', values='Count').fillna(0)
    
    fig = px.imshow(
        pivot_data,
        labels=dict(x="ABC Class", y="Stock Status", color="Count"),
        x=pivot_data.columns,
        y=pivot_data.index,
        color_continuous_scale='RdYlGn_r',
        text_auto=True
    )
    
    fig.update_layout(
        xaxis_title="ABC Classification",
        yaxis_title="Stock Status"
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    section_header("Inventory Turnover by Product", "🔄")
    
    fig = px.bar(
        turnover_df.sort_values('Turnover_Ratio', ascending=False),
        x='ProductName',
        y='Turnover_Ratio',
        color='Turnover_Ratio',
        color_continuous_scale='Viridis'
    )
    
    # Add industry benchmark line
    fig.add_hline(y=4, line_dash="dash", line_color=COLORS['success'],
                  annotation_text="Good Turnover (4x)")
    
    fig.update_layout(
        xaxis_title="Product",
        yaxis_title="Turnover Ratio",
        coloraxis_showscale=False
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# CHARTS ROW 2
# =============================================================================

col_left2, col_right2 = st.columns(2)

with col_left2:
    section_header("Stock Coverage Days", "📅")
    
    # Prepare data for display (exclude infinite values for chart)
    coverage_chart = coverage_df[coverage_df['Coverage_Days'] != np.inf].copy()
    coverage_chart = coverage_chart.sort_values('Coverage_Days')
    
    fig = px.bar(
        coverage_chart,
        x='Coverage_Days',
        y='ProductName',
        orientation='h',
        color='Coverage_Status',
        color_discrete_map={
            'Critical': COLORS['danger'],
            'Warning': COLORS['warning'],
            'Healthy': COLORS['success'],
            'No Usage': COLORS['gray']
        }
    )
    
    # Add threshold lines
    fig.add_vline(x=7, line_dash="dash", line_color=COLORS['danger'],
                  annotation_text="Critical (7 days)")
    fig.add_vline(x=30, line_dash="dash", line_color=COLORS['warning'],
                  annotation_text="Warning (30 days)")
    
    fig.update_layout(
        xaxis_title="Days of Coverage",
        yaxis_title="",
        legend_title="Status"
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right2:
    section_header("Inventory Value Trend", "📈")
    
    # Calculate cumulative inventory value over time
    df_trans_filtered = df_trans_filtered.copy()
    df_trans_filtered['ValueChange'] = df_trans_filtered['Quantity'] * df_trans_filtered['UnitCost']
    
    daily_value = df_trans_filtered.groupby('Date')['ValueChange'].sum().cumsum().reset_index()
    
    # Add initial inventory value
    initial_value = total_stock_value - daily_value['ValueChange'].iloc[-1] if len(daily_value) > 0 else total_stock_value
    daily_value['ValueChange'] = daily_value['ValueChange'] + initial_value
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_value['Date'],
        y=daily_value['ValueChange'],
        mode='lines',
        fill='tozeroy',
        line=dict(color=COLORS['primary'], width=2),
        fillcolor='rgba(31, 119, 180, 0.2)'
    ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Inventory Value (₹)",
        hovermode='x unified'
    )
    
    fig = style_plotly_chart(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# REORDER RECOMMENDATIONS
# =============================================================================

st.markdown("---")
section_header("⚠️ Reorder Recommendations", "🛒")

if not reorder_alerts.empty:
    st.warning(f"**{len(reorder_alerts)} product(s) require immediate reordering!**")
    
    # Calculate additional fields for display
    display_df = reorder_alerts[[
        'ProductID', 'ProductName', 'Category', 'CurrentStock', 
        'ReorderPoint', 'SafetyStock', 'MOQ', 'UnitCost', 'LeadTimeDays'
    ]].copy()
    
    display_df['Shortage'] = display_df['ReorderPoint'] - display_df['CurrentStock']
    display_df['Reorder Qty'] = display_df[['Shortage', 'MOQ']].max(axis=1)
    display_df['Estimated Cost'] = display_df['Reorder Qty'] * display_df['UnitCost']
    
    # Format currency columns
    display_df['UnitCost'] = display_df['UnitCost'].apply(lambda x: format_currency(x))
    display_df['Estimated Cost'] = display_df['Estimated Cost'].apply(lambda x: format_currency(x))
    
    st.dataframe(
        display_df[[
            'ProductID', 'ProductName', 'Category', 'CurrentStock', 
            'ReorderPoint', 'Shortage', 'Reorder Qty', 'UnitCost', 'Estimated Cost', 'LeadTimeDays'
        ]],
        use_container_width=True,
        hide_index=True
    )
    
    # Total cost for reordering
    total_reorder_cost = (reorder_alerts['MOQ'] * reorder_alerts['UnitCost']).sum()
    st.info(f"💰 **Total Estimated Reorder Cost**: {format_currency(total_reorder_cost)}")
else:
    st.success("✅ All inventory items are above reorder point. No immediate action needed.")

# =============================================================================
# PRODUCT DETAILS TABLE
# =============================================================================

st.markdown("---")
section_header("Product Inventory Details", "📋")

# Add filters for the table
show_status = st.multiselect(
    "Filter by Status",
    options=['Critical', 'Stockout Risk', 'Healthy'],
    default=['Critical', 'Stockout Risk', 'Healthy']
)

filtered_products = df_prod_filtered[df_prod_filtered['Stock Status'].isin(show_status)]

# Color code by status
def highlight_status(row):
    if row['Stock Status'] == 'Critical':
        return ['background-color: rgba(231, 76, 60, 0.2)'] * len(row)
    elif row['Stock Status'] == 'Stockout Risk':
        return ['background-color: rgba(243, 156, 18, 0.2)'] * len(row)
    else:
        return [''] * len(row)

st.dataframe(
    filtered_products[[
        'ProductID', 'ProductName', 'Category', 'ABC_Class', 
        'CurrentStock', 'ReorderPoint', 'SafetyStock', 'UnitCost', 'Stock Status'
    ]],
    use_container_width=True,
    hide_index=True
)
