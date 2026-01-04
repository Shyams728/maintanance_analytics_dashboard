
import streamlit as st
import pandas as pd
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from styles import inject_custom_css, COLORS, format_currency

st.set_page_config(
    page_title="Maintenance Analytics Dashboard",
    page_icon="🏭",
    layout="wide"
)

inject_custom_css()

# =============================================================================
# HEADER
# =============================================================================

st.title("🏭 Maintenance Analytics Dashboard")
st.markdown("### Cost, Inventory & Maintenance Management System")

st.markdown("---")

# =============================================================================
# QUICK STATS
# =============================================================================

DATA_DIR = "d:/data_science/power_bi/data"

@st.cache_data
def load_quick_stats():
    try:
        df_wo = pd.read_csv(os.path.join(DATA_DIR, "Fact_Maintenance_WorkOrders_Enriched.csv"))
        df_prod = pd.read_csv(os.path.join(DATA_DIR, "Dim_Product_Enriched.csv"))
        df_equip = pd.read_csv(os.path.join(DATA_DIR, "Dim_Equipment.csv"))
        df_budget = pd.read_csv(os.path.join(DATA_DIR, "Fact_Budget_vs_Actual.csv"))
        
        return {
            'work_orders': len(df_wo),
            'total_cost': df_wo['TotalCost'].sum(),
            'products': len(df_prod),
            'equipment': len(df_equip),
            'critical_stock': len(df_prod[df_prod['Stock Status'] == 'Critical']),
            'breakdown_count': len(df_wo[df_wo['MaintenanceType'] == 'Breakdown']),
            'budget_total': df_budget['BudgetAmount'].sum()
        }
    except:
        return None

stats = load_quick_stats()

if stats:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Work Orders", stats['work_orders'])
        
    with col2:
        st.metric("💰 Maintenance Cost", format_currency(stats['total_cost']))
        
    with col3:
        st.metric("⚙️ Equipment Units", stats['equipment'])
        
    with col4:
        st.metric("📦 Products", stats['products'])

st.markdown("---")

# =============================================================================
# NAVIGATION
# =============================================================================

st.markdown("""
### 📍 Navigation Guide

Use the sidebar to navigate to the different analytics modules:

| Page | Description | Key Features |
|------|-------------|--------------|
| 📊 **Executive Command Center** | High-level KPIs for plant managers | MTTR/MTBF, Availability %, Budget Variance |
| 🛠️ **Maintenance Operations** | Reliability analytics & work order management | Pareto Analysis, MTTR/MTBF Quadrant, Failure Trends |
| 📦 **Inventory & Supply Chain** | Stock monitoring & procurement intelligence | Turnover Ratio, Coverage Days, Reorder Alerts |
| 👷 **Technician Performance** | Workforce productivity analysis | Repair Time, Work Order Volume |
| 💰 **Cost & Vendor Analysis** | Financial tracking & vendor management | Payment Variance, Budget Adherence |

---

### 🎯 Key Performance Indicators

This dashboard tracks the following **industry-standard KPIs**:

**Maintenance Reliability**
- **MTTR** (Mean Time To Repair) - Average repair duration
- **MTBF** (Mean Time Between Failures) - Equipment reliability indicator
- **Equipment Availability %** - Uptime percentage

**Inventory Management**
- **Inventory Turnover Ratio** - Stock efficiency metric
- **Stock Coverage Days** - Days of supply remaining
- **Reorder Point Alerts** - Critical stock notifications

**Cost Control**
- **Payment Variance** - Contract vs actual payments
- **Budget Adherence %** - Actual vs planned spending
- **Maintenance Cost Distribution** - Preventive vs breakdown costs

---

### 👤 Profile Alignment

This analytics system is designed for professionals in:

✔ **Mining & Limestone Operations**  
✔ **Mechanical Maintenance Engineering**  
✔ **Heavy Equipment (HEMM) Management**  
✔ **Reliability & Preventive Maintenance**  
✔ **Plant Operations & SAP Integration**

---

*Built with Streamlit & Plotly | Data Analytics for Cement/Mining Operations*
""")

# =============================================================================
# SIDEBAR
# =============================================================================

st.sidebar.success("👈 Select a page from the navigation above.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Dashboard Info")
st.sidebar.markdown("""
**Data Coverage**: 2024-2025  
**Last Updated**: Live Data  
**Domain**: Cement/Mining/HEMM
""")

if stats:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚠️ Quick Alerts")
    
    if stats['critical_stock'] > 0:
        st.sidebar.warning(f"🔴 {stats['critical_stock']} items at critical stock")
    else:
        st.sidebar.success("✅ All inventory healthy")
    
    breakdown_pct = (stats['breakdown_count'] / stats['work_orders']) * 100 if stats['work_orders'] > 0 else 0
    if breakdown_pct > 40:
        st.sidebar.warning(f"🔴 High breakdown rate: {breakdown_pct:.1f}%")
    else:
        st.sidebar.success(f"✅ Breakdown rate: {breakdown_pct:.1f}%")
