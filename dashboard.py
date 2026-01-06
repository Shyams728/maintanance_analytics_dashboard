import streamlit as st
import pandas as pd
import os
import sys
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from styles import inject_custom_css, COLORS, format_currency
try:
    from analytics_engine import predict_rul_batch
except ImportError:
    # Fallback if analytics_engine is not yet ready or path issue
    def predict_rul_batch(df): return [999] * len(df)

st.set_page_config(
    page_title="Maintenance Analytics Dashboard",
    page_icon="🏭",
    layout="wide"
)

inject_custom_css()

# =============================================================================
# DATA LOADING
# =============================================================================
DATA_DIR = "../data"

@st.cache_data
def load_data():
    try:
        # Load necessary files
        return {
            'wo': pd.read_csv(os.path.join(DATA_DIR, "Fact_Maintenance_WorkOrders_Enriched.csv")),
            'sensor': pd.read_csv(os.path.join(DATA_DIR, "Fact_Sensor_Readings.csv")),
            'equip': pd.read_csv(os.path.join(DATA_DIR, "Dim_Equipment.csv")),
            'budget': pd.read_csv(os.path.join(DATA_DIR, "Fact_Budget_vs_Actual.csv")),
        }
    except FileNotFoundError:
        st.error("Data files not found. Please run generate_data.py first.")
        return None

data = load_data()

# =============================================================================
# SIDEBAR - PERSONA SELECTION
# =============================================================================
st.sidebar.title("👤 User Persona")
persona = st.sidebar.radio(
    "Select View Mode:",
    ("Operator (Shop Floor)", "Maintenance Manager", "Plant Executive"),
    index=1
)

st.sidebar.markdown("---")
if persona == "Operator (Shop Floor)":
    st.sidebar.info("Focus: Real-time Asset Health, Alerts, Sensor Readings.")
elif persona == "Maintenance Manager":
    st.sidebar.info("Focus: Work Orders, Schedule Compliance, technician allocation.")
else:
    st.sidebar.info("Focus: ROI, OEE, Budget Adherence, High-level Reliability.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Navigation")
st.sidebar.page_link("dashboard.py", label="🏠 Home", icon="🏠")
st.sidebar.page_link("pages/1_Executive_Command_Center.py", label="📊 Executive Details", icon="📊")
st.sidebar.page_link("pages/2_Maintenance_Operations.py", label="🛠️ Maintenance Ops", icon="🛠️")

# =============================================================================
# VIEW LOGIC
# =============================================================================

if data:
    df_wo = data['wo']
    df_sensor = data['sensor']
    df_equip = data['equip']
    
    # -------------------------------------------------------------------------
    # OPERATOR VIEW
    # -------------------------------------------------------------------------
    if persona == "Operator (Shop Floor)":
        st.title("👷 Operator Dashboard")
        st.markdown("### Real-Time Asset Health Monitoring")
        
        # Simulate "Live" data by taking the last known reading for each equipment
        # In a real app, this would query an API or DB
        latest_readings = df_sensor.sort_values('Timestamp').groupby('EquipmentID').tail(1).copy()
        
        # PREDICT RUL
        # We need to make sure we map these correctly
        rul_preds = predict_rul_batch(latest_readings) 
        latest_readings['Predicted_RUL'] = rul_preds
        
        # Display Grid
        cols = st.columns(3)
        
        for idx, (i, row) in enumerate(latest_readings.iterrows()):
            equip_name = df_equip[df_equip['EquipmentID'] == row['EquipmentID']]['EquipmentName'].values[0]
            
            with cols[idx % 3]:
                # Determine Status Color
                rul = row['Predicted_RUL']
                if rul < 7:
                    status_color = "red"
                    icon = "🚨"
                    msg = "CRITICAL FAILURE IMMINENT"
                elif rul < 30:
                    status_color = "orange"
                    icon = "⚠️"
                    msg = "Maintenance Required Soon"
                else:
                    status_color = "green"
                    icon = "✅"
                    msg = "Healthy Operation"
                
                st.markdown(f"""
                <div style="border: 1px solid #444; padding: 15px; border-radius: 10px; border-left: 10px solid {status_color}; background-color: #262730;">
                    <h4 style="margin:0;">{icon} {equip_name}</h4>
                    <p style="font-size: 0.9em; opacity: 0.8; margin-bottom: 10px;">ID: {row['EquipmentID']}</p>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>🌡️ Temp: <b>{row['Temperature_C']}°C</b></span>
                        <span>〰️ Vibration: <b>{row['Vibration_mm_s']}</b></span>
                    </div>
                    <hr style="margin: 5px 0;">
                    <div style="text-align: center;">
                        <span style="font-size: 0.8em;">ESTIMATED REMAINING LIFE</span><br>
                        <strong style="font-size: 1.5em; color: {status_color};">{rul:.1f} Days</strong>
                    </div>
                     <div style="text-align: center; margin-top:5px; font-size: 0.8em; font-weight: bold; color: {status_color};">
                        {msg}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("") # Spacer

    # -------------------------------------------------------------------------
    # MANAGER VIEW
    # -------------------------------------------------------------------------
    elif persona == "Maintenance Manager":
        st.title("🛠️ Maintenance Management")
        
        # Quick Stats Row
        c1, c2, c3, c4 = st.columns(4)
        total_open = len(df_wo[df_wo['DowntimeHours'].isna()]) # Proxy for open if Downtime not logged? Or just simulate
        # Actually our enriched data is historical, so let's simulate "Open" as "Recent Breakdown"
        recent_breakdowns = len(df_wo[df_wo['MaintenanceType'] == 'Breakdown'])
        
        c1.metric("Total Work Orders", len(df_wo))
        c2.metric("Breakdown Events", recent_breakdowns, delta_color="inverse")
        c3.metric("Avg Repair Cost", format_currency(df_wo['TotalCost'].mean()))
        c4.metric("Avg Downtime (Hrs)", f"{df_wo['DowntimeHours'].mean():.1f}")
        
        st.markdown("### 📋 Active Work Order Queue (Simulated)")
        # Show 'recent' work orders
        st.dataframe(
            df_wo.tail(10)[['WorkOrderID', 'EquipmentID', 'MaintenanceType', 'Date', 'FailureCode', 'TotalCost']],
            use_container_width=True,
            hide_index=True
        )
        
        col_1, col_2 = st.columns(2)
        with col_1:
             st.markdown("### 📉 Failure Causes (Pareto)")
             # Simple Pareto
             pareto = df_wo[df_wo['MaintenanceType'] == 'Breakdown']['FailureCode'].value_counts()
             st.bar_chart(pareto)
             
        with col_2:
            st.markdown("### 📅 Upcoming Scheduled Maintenance")
            # In a real app this would query future dates. 
            # We'll just list some high-use equipment
            st.info("Next Maintenance Cycle: **Monday, 14th Feb 2025**")
            st.text("- Conveyor Belt CV001 (Preventive)\n- Crusher Unit CR001 (Inspection)\n- Excavator EX001 (Oil Change)")

    # -------------------------------------------------------------------------
    # EXECUTIVE VIEW
    # -------------------------------------------------------------------------
    else: # Executive
        st.title("📊 Executive Command Center")
        
        # Financial Highlights
        total_spend = df_wo['TotalCost'].sum()
        budget = data['budget']['BudgetAmount'].sum()
        variance = budget - total_spend
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("YTD Maintenance Spend", format_currency(total_spend), delta=format_currency(variance))
        kpi2.metric("Total Budget", format_currency(budget))
        kpi3.metric("Budget Utilization", f"{(total_spend/budget)*100:.1f}%", delta_color="inverse") # Inverse because higher is worse
        
        st.markdown("### 🏭 Plant Health Overview")
        
        # Simple OEE Proxy (Availability)
        total_hours = 365 * 24
        total_downtime = df_wo['DowntimeHours'].sum()
        availability = ((total_hours - total_downtime) / total_hours) * 100
        
        st.progress(availability / 100, text=f"Overall Plant Availability: **{availability:.2f}%**")
        
        st.markdown("### 💰 Cost Drivers")
        cost_by_equip = df_wo.groupby('EquipmentID')['TotalCost'].sum().sort_values(ascending=False).head(5)
        st.bar_chart(cost_by_equip)

else:
    st.info("Loading data...")
