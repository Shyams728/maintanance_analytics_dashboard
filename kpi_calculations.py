"""
KPI Calculations Module
Centralized business logic for maintenance, inventory, and cost KPIs.
Domain: Cement / Mining / Heavy Equipment Operations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# =============================================================================
# MAINTENANCE KPIs
# =============================================================================

def calculate_mttr(df_wo: pd.DataFrame, group_by: str = 'EquipmentID') -> pd.DataFrame:
    """
    Calculate Mean Time To Repair (MTTR) per equipment.
    MTTR = Average downtime hours for breakdown work orders.
    
    Args:
        df_wo: Work orders dataframe with DowntimeHours, MaintenanceType columns
        group_by: Column to group by (default: EquipmentID)
    
    Returns:
        DataFrame with MTTR per group
    """
    breakdown_wo = df_wo[df_wo['MaintenanceType'] == 'Breakdown'].copy()
    
    if breakdown_wo.empty:
        return pd.DataFrame({group_by: [], 'MTTR_Hours': []})
    
    mttr = breakdown_wo.groupby(group_by).agg(
        MTTR_Hours=('DowntimeHours', 'mean'),
        Breakdown_Count=('WorkOrderID', 'count'),
        Total_Downtime=('DowntimeHours', 'sum')
    ).reset_index()
    
    return mttr


def calculate_mtbf(df_wo: pd.DataFrame, group_by: str = 'EquipmentID', 
                   days: float = 365) -> pd.DataFrame:
    """
    Calculate Mean Time Between Failures (MTBF) per equipment.
    MTBF = (Total Operating Hours - Total Unplanned Downtime) / Number of Failures
    
    Args:
        df_wo: Work orders dataframe
        group_by: Column to group by
        days: Number of days in the period
    
    Returns:
        DataFrame with MTBF per group
    """
    total_operating_hours = days * 24
    breakdown_wo = df_wo[df_wo['MaintenanceType'] == 'Breakdown'].copy()
    
    if breakdown_wo.empty:
        # If no breakdowns, MTBF is the full operating time (or infinite, but we'll cap it at total hours)
        # We need all equipment IDs that were in the original filtered set if possible
        return pd.DataFrame({group_by: [], 'MTBF_Hours': [], 'Failure_Count': []})
    
    stats = breakdown_wo.groupby(group_by).agg(
        Failure_Count=('WorkOrderID', 'count'),
        Total_Unplanned_Downtime=('DowntimeHours', 'sum')
    ).reset_index()
    
    # MTBF = (Operating Time - Unplanned Downtime) / Failures
    stats['MTBF_Hours'] = (total_operating_hours - stats['Total_Unplanned_Downtime']) / stats['Failure_Count']
    stats['MTBF_Hours'] = stats['MTBF_Hours'].clip(lower=0) 
    
    return stats[[group_by, 'MTBF_Hours', 'Failure_Count']]


def calculate_equipment_availability(df_wo: pd.DataFrame, 
                                     equipment_count: int = 1,
                                     days: float = 365) -> dict:
    """
    Calculate overall equipment availability percentage.
    Availability = (Total Available Hours - Total Downtime) / Total Available Hours × 100
    
    Args:
        df_wo: Work orders dataframe
        equipment_count: Number of equipment pieces in the filtered set
        days: Number of days in the period
    
    Returns:
        Dictionary with availability metrics
    """
    total_available_hours = equipment_count * days * 24
    total_downtime = df_wo['DowntimeHours'].sum()
    
    if total_available_hours == 0:
        return {
            'Availability_Pct': 100.0,
            'Total_Downtime_Hours': 0.0,
            'Total_Available_Hours': 0.0,
            'Uptime_Hours': 0.0
        }

    availability_pct = ((total_available_hours - total_downtime) / total_available_hours) * 100
    
    return {
        'Availability_Pct': round(max(0, availability_pct), 2),
        'Total_Downtime_Hours': round(total_downtime, 2),
        'Total_Available_Hours': round(total_available_hours, 2),
        'Uptime_Hours': round(max(0, total_available_hours - total_downtime), 2)
    }


def calculate_schedule_compliance(df_wo: pd.DataFrame) -> dict:
    """
    Calculate schedule compliance for preventive maintenance.
    Compliance = (On-Time WOs / Total Scheduled WOs) * 100
    
    Args:
        df_wo: Work orders dataframe
    
    Returns:
        Dictionary with compliance metrics
    """
    # Filter for preventive WOs with a schedule date
    scheduled_wo = df_wo[
        (df_wo['MaintenanceType'] == 'Preventive') & 
        (df_wo['ScheduledDate'].notna()) & 
        (df_wo['ScheduledDate'] != '')
    ].copy()
    
    if scheduled_wo.empty:
        return {'Compliance_Pct': 100.0, 'Late_Count': 0, 'OnTime_Count': 0, 'Total_Scheduled': 0}
        
    scheduled_wo['Date'] = pd.to_datetime(scheduled_wo['Date'])
    scheduled_wo['ScheduledDate'] = pd.to_datetime(scheduled_wo['ScheduledDate'])
    
    # Late if Actual Date > Scheduled Date + 1 day buffer
    scheduled_wo['IsLate'] = scheduled_wo['Date'] > (scheduled_wo['ScheduledDate'] + pd.Timedelta(days=1))
    
    late_count = scheduled_wo['IsLate'].sum()
    total = len(scheduled_wo)
    ontime = total - late_count
    
    compliance = (ontime / total) * 100
    
    return {
        'Compliance_Pct': round(compliance, 1),
        'Late_Count': late_count,
        'OnTime_Count': ontime,
        'Total_Scheduled': total
    }


def calculate_maintenance_mix(df_wo: pd.DataFrame) -> dict:
    """
    Calculate preventive vs breakdown maintenance ratio.
    
    Returns:
        Dictionary with maintenance type distribution
    """
    type_counts = df_wo['MaintenanceType'].value_counts()
    total = type_counts.sum()
    
    preventive = type_counts.get('Preventive', 0)
    breakdown = type_counts.get('Breakdown', 0)
    
    return {
        'Preventive_Count': preventive,
        'Breakdown_Count': breakdown,
        'Preventive_Pct': round((preventive / total) * 100, 1) if total > 0 else 0,
        'Breakdown_Pct': round((breakdown / total) * 100, 1) if total > 0 else 0,
        'Preventive_Cost': df_wo[df_wo['MaintenanceType'] == 'Preventive']['TotalCost'].sum(),
        'Breakdown_Cost': df_wo[df_wo['MaintenanceType'] == 'Breakdown']['TotalCost'].sum(),
        'Preventive_Downtime': df_wo[df_wo['MaintenanceType'] == 'Preventive']['DowntimeHours'].sum(),
        'Breakdown_Downtime': df_wo[df_wo['MaintenanceType'] == 'Breakdown']['DowntimeHours'].sum()
    }


# =============================================================================
# INVENTORY KPIs
# =============================================================================

def calculate_inventory_turnover(df_trans: pd.DataFrame, df_products: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Inventory Turnover Ratio per product.
    Turnover = Total Issues (COGS proxy) / Average Inventory Value
    
    Args:
        df_trans: Inventory transactions dataframe
        df_products: Products dimension with CurrentStock, UnitCost
    
    Returns:
        DataFrame with turnover ratio per product
    """
    # Get total issues (negative quantities = issues)
    issues = df_trans[df_trans['Type'] == 'Issue'].copy()
    issues['Issue_Value'] = abs(issues['Quantity']) * issues['UnitCost']
    
    issue_totals = issues.groupby('ProductID').agg(
        Total_Issues=('Quantity', lambda x: abs(x.sum())),
        Issue_Value=('Issue_Value', 'sum')
    ).reset_index()
    
    # Merge with products for average inventory
    result = df_products[['ProductID', 'ProductName', 'CurrentStock', 'UnitCost']].merge(
        issue_totals, on='ProductID', how='left'
    ).fillna(0)
    
    result['Avg_Inventory_Value'] = result['CurrentStock'] * result['UnitCost']
    result['Turnover_Ratio'] = np.where(
        result['Avg_Inventory_Value'] > 0,
        result['Issue_Value'] / result['Avg_Inventory_Value'],
        0
    )
    
    return result[['ProductID', 'ProductName', 'Total_Issues', 'Turnover_Ratio']]


def calculate_stock_coverage_days(df_trans: pd.DataFrame, df_products: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Stock Coverage Days per product.
    Coverage Days = Current Stock / Average Daily Usage
    
    Args:
        df_trans: Inventory transactions dataframe
        df_products: Products dimension with CurrentStock
    
    Returns:
        DataFrame with coverage days per product
    """
    # Calculate average daily usage from issues
    issues = df_trans[df_trans['Type'] == 'Issue'].copy()
    issues['Date'] = pd.to_datetime(issues['Date'])
    
    date_range = (issues['Date'].max() - issues['Date'].min()).days or 1
    
    daily_usage = issues.groupby('ProductID').agg(
        Total_Usage=('Quantity', lambda x: abs(x.sum()))
    ).reset_index()
    daily_usage['Avg_Daily_Usage'] = daily_usage['Total_Usage'] / date_range
    
    # Merge with products
    result = df_products[['ProductID', 'ProductName', 'CurrentStock', 'ReorderPoint']].merge(
        daily_usage, on='ProductID', how='left'
    ).fillna(0)
    
    result['Coverage_Days'] = np.where(
        result['Avg_Daily_Usage'] > 0,
        result['CurrentStock'] / result['Avg_Daily_Usage'],
        np.inf
    )
    
    # Status based on coverage
    def get_coverage_status(days):
        if days == np.inf:
            return 'No Usage'
        elif days <= 7:
            return 'Critical'
        elif days <= 30:
            return 'Warning'
        else:
            return 'Healthy'
    
    result['Coverage_Status'] = result['Coverage_Days'].apply(get_coverage_status)
    
    return result[['ProductID', 'ProductName', 'CurrentStock', 'Avg_Daily_Usage', 
                   'Coverage_Days', 'Coverage_Status']]


def get_reorder_alerts(df_products: pd.DataFrame) -> pd.DataFrame:
    """
    Get products that need reordering.
    
    Returns:
        DataFrame with products below reorder point
    """
    alerts = df_products[df_products['CurrentStock'] <= df_products['ReorderPoint']].copy()
    
    if not alerts.empty:
        alerts['Shortage_Qty'] = alerts['ReorderPoint'] - alerts['CurrentStock']
        alerts['Reorder_Qty'] = alerts[['Shortage_Qty', 'MOQ']].max(axis=1)
        alerts['Estimated_Cost'] = alerts['Reorder_Qty'] * alerts['UnitCost']
    
    return alerts


# =============================================================================
# COST & VENDOR KPIs
# =============================================================================

def calculate_payment_variance(df_costs: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate payment variance per vendor.
    Variance = Actual Payment - Contract Value
    
    Args:
        df_costs: Costs fact table with VendorID, ContractValue, ActualPayment
    
    Returns:
        DataFrame with variance analysis per vendor
    """
    variance = df_costs.groupby('VendorID').agg(
        Total_Contract=('ContractValue', 'sum'),
        Total_Actual=('ActualPayment', 'sum'),
        Transaction_Count=('CostID', 'count')
    ).reset_index()
    
    variance['Variance'] = variance['Total_Actual'] - variance['Total_Contract']
    variance['Variance_Pct'] = (variance['Variance'] / variance['Total_Contract']) * 100
    
    # Status based on variance
    def get_variance_status(pct):
        if pct > 5:
            return 'Over Budget'
        elif pct < -5:
            return 'Under Budget'
        else:
            return 'On Track'
    
    variance['Status'] = variance['Variance_Pct'].apply(get_variance_status)
    
    return variance


def calculate_budget_adherence(df_budget: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate budget adherence by cost center and GL account.
    
    Args:
        df_budget: Budget vs Actual fact table
    
    Returns:
        DataFrame with budget adherence metrics
    """
    adherence = df_budget.groupby(['CostCenter', 'GLAccount']).agg(
        Total_Budget=('BudgetAmount', 'sum'),
        Total_Actual=('ActualAmount', 'sum')
    ).reset_index()
    
    adherence['Variance'] = adherence['Total_Actual'] - adherence['Total_Budget']
    adherence['Variance_Pct'] = (adherence['Variance'] / adherence['Total_Budget']) * 100
    adherence['Adherence_Pct'] = 100 - abs(adherence['Variance_Pct'])
    
    return adherence


# =============================================================================
# SUMMARY FUNCTIONS
# =============================================================================

def calculate_all_kpis(df_wo: pd.DataFrame, df_trans: pd.DataFrame, 
                       df_products: pd.DataFrame, df_costs: pd.DataFrame,
                       df_budget: pd.DataFrame) -> dict:
    """
    Calculate all KPIs and return as a dictionary of dataframes.
    
    Returns:
        Dictionary with all KPI results
    """
    return {
        'mttr': calculate_mttr(df_wo),
        'mtbf': calculate_mtbf(df_wo),
        'availability': calculate_equipment_availability(df_wo),
        'maintenance_mix': calculate_maintenance_mix(df_wo),
        'inventory_turnover': calculate_inventory_turnover(df_trans, df_products),
        'stock_coverage': calculate_stock_coverage_days(df_trans, df_products),
        'reorder_alerts': get_reorder_alerts(df_products),
        'payment_variance': calculate_payment_variance(df_costs),
        'budget_adherence': calculate_budget_adherence(df_budget)
    }


def get_executive_summary(df_wo: pd.DataFrame, df_trans: pd.DataFrame,
                          df_products: pd.DataFrame, equipment_ids: list = None) -> dict:
    """
    Get high-level executive summary KPIs.
    
    Args:
        df_wo: Filtered work orders
        df_trans: Filtered transactions
        df_products: Products dimension
        equipment_ids: List of unique equipment IDs that should be considered for the timeframe
        
    Returns:
        Dictionary with key executive metrics
    """
    # Calculate timeframe days
    if not df_wo.empty:
        date_min = df_wo['Date'].min()
        date_max = df_wo['Date'].max()
        if isinstance(date_min, str):
            date_min = pd.to_datetime(date_min)
            date_max = pd.to_datetime(date_max)
        days = (date_max - date_min).days + 1
    else:
        days = 365 # Default fallback
        
    # Equipment count for availability
    if equipment_ids:
        eq_count = len(equipment_ids)
    else:
        eq_count = df_wo['EquipmentID'].nunique() if not df_wo.empty else 1
    
    availability = calculate_equipment_availability(df_wo, eq_count, days)
    maintenance_mix = calculate_maintenance_mix(df_wo)
    
    # Overall MTTR and MTBF
    breakdown_wo = df_wo[df_wo['MaintenanceType'] == 'Breakdown']
    overall_mttr = breakdown_wo['DowntimeHours'].mean() if not breakdown_wo.empty else 0
    
    failure_count = len(breakdown_wo)
    total_unplanned_downtime = breakdown_wo['DowntimeHours'].sum()
    
    # MTBF = (Total Equipment * Period Hours - Unplanned Downtime) / Failures
    total_period_hours = eq_count * days * 24
    overall_mtbf = (total_period_hours - total_unplanned_downtime) / failure_count if failure_count > 0 else total_period_hours
    
    # Stock health
    critical_stock = 0
    if df_products is not None:
        critical_stock = len(df_products[df_products['CurrentStock'] <= df_products['ReorderPoint']])
    
    return {
        'Total_Maintenance_Cost': df_wo['TotalCost'].sum(),
        'Preventive_Cost': maintenance_mix['Preventive_Cost'],
        'Breakdown_Cost': maintenance_mix['Breakdown_Cost'],
        'Availability_Pct': availability['Availability_Pct'],
        'Total_Downtime': availability['Total_Downtime_Hours'],
        'Unplanned_Downtime': maintenance_mix['Breakdown_Downtime'],
        'Planned_Downtime': maintenance_mix['Preventive_Downtime'],
        'MTTR_Hours': round(overall_mttr, 2),
        'MTBF_Hours': round(overall_mtbf, 2),
        'Total_Work_Orders': len(df_wo),
        'Breakdown_Count': maintenance_mix['Breakdown_Count'],
        'Preventive_Pct': maintenance_mix['Preventive_Pct'],
        'Critical_Stock_Items': critical_stock,
        'Days_In_Period': days,
        'Equipment_Count': eq_count
    }

def calculate_oee(df_prod: pd.DataFrame) -> dict:
    """
    Calculate Overall Equipment Effectiveness (OEE) from production data.
    OEE = Availability * Performance * Quality

    Args:
        df_prod: DataFrame with daily production data including:
                 - OperatingHours
                 - TotalPartsProduced
                 - GoodPartsProduced
                 - IdealCycleTime_s
    """
    if df_prod.empty:
        return {
            'OEE_Pct': 0,
            'Availability_Component': 0,
            'Performance_Component': 0,
            'Quality_Component': 0
        }

    # Assuming 24 scheduled hours per day entry for each piece of equipment
    total_scheduled_hours = len(df_prod) * 24
    total_operating_hours = df_prod['OperatingHours'].sum()

    # Availability
    availability = total_operating_hours / total_scheduled_hours if total_scheduled_hours > 0 else 0

    # Performance
    total_parts = df_prod['TotalPartsProduced'].sum()
    # Calculate potential parts based on average cycle time and actual operating hours
    avg_ideal_cycle_time_s = df_prod['IdealCycleTime_s'].mean()
    potential_parts = (total_operating_hours * 3600) / avg_ideal_cycle_time_s if avg_ideal_cycle_time_s > 0 else 0

    performance = total_parts / potential_parts if potential_parts > 0 else 0
    performance = min(performance, 1.0) # Cap at 100%

    # Quality
    good_parts = df_prod['GoodPartsProduced'].sum()
    quality = good_parts / total_parts if total_parts > 0 else 0

    oee = availability * performance * quality * 100

    return {
        'OEE_Pct': round(oee, 2),
        'Availability_Component': round(availability * 100, 2),
        'Performance_Component': round(performance * 100, 2),
        'Quality_Component': round(quality * 100, 2)
    }

def calculate_planned_maintenance_percentage(df_wo: pd.DataFrame) -> float:
    """
    Calculate the percentage of maintenance work that is planned.
    """

    planned = df_wo[df_wo['MaintenanceType'] == 'Preventive']['WorkOrderID'].count()
    total = df_wo['WorkOrderID'].count()

    if total == 0:
        return 100.0

    return round((planned / total) * 100, 2)
