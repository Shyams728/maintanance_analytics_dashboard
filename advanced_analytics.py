"""
Advanced Analytics Module
Contains logic for predictive models, forecasting, and complex scoring.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =============================================================================
# PREDICTIVE MAINTENANCE
# =============================================================================

def predict_failure_probability(df_sensor: pd.DataFrame, window_hours: int = 24) -> pd.DataFrame:
    """
    Predict failure probability based on recent sensor readings.
    Uses a simple rule-based heuristics model for demonstration.
    
    Args:
        df_sensor: DataFrame with Timestamp, EquipmentID, Temperature_C, Vibration_mm_s
        window_hours: Lookback window in hours
    
    Returns:
        DataFrame with EquipmentID, Failure_Prob, Insight
    """
    latest_ts = pd.to_datetime(df_sensor['Timestamp']).max()
    cutoff_ts = latest_ts - timedelta(hours=window_hours)
    
    recent_readings = df_sensor[pd.to_datetime(df_sensor['Timestamp']) > cutoff_ts].copy()
    
    results = []
    
    for eq_id, group in recent_readings.groupby('EquipmentID'):
        avg_temp = group['Temperature_C'].mean()
        max_vibration = group['Vibration_mm_s'].max()
        
        prob = 0.0
        insight = "Normal Operation"
        
        # Heuristics
        if avg_temp > 95:
            prob += 0.6
            insight = "Critical Overheating Detected"
        elif avg_temp > 85:
            prob += 0.3
            insight = "High Operating Temperature"
            
        if max_vibration > 5.0:
            prob += 0.5
            insight = f"{insight} + Excessive Vibration" if prob > 0 else "Excessive Vibration Detected"
        elif max_vibration > 3.5:
            prob += 0.2
            
        prob = min(prob, 0.99) # Cap at 99%
        
        results.append({
            "EquipmentID": eq_id,
            "Avg_Temp": round(avg_temp, 1),
            "Max_Vibration": round(max_vibration, 2),
            "Failure_Probability": round(prob * 100, 1),
            "Insight": insight,
            "Status": "Critical" if prob > 0.6 else ("Warning" if prob > 0.3 else "Healthy")
        })
        
    return pd.DataFrame(results)

# =============================================================================
# FORECASTING
# =============================================================================

def forecast_maintenance_costs(df_budget: pd.DataFrame, months_ahead: int = 3) -> pd.DataFrame:
    """
    Forecast future maintenance costs using simple moving average.
    
    Args:
        df_budget: DataFrame with Date, ActualAmount
        months_ahead: Number of months to forecast
    
    Returns:
        DataFrame with Date (future), ForecastAmount, LowerBound, UpperBound
    """
    df = df_budget.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Aggregate to monthly total
    monthly_costs = df.groupby('Date')['ActualAmount'].sum().sort_index().reset_index()
    
    # Calculate simple stats
    last_6_months = monthly_costs.tail(6)
    avg_cost = last_6_months['ActualAmount'].mean()
    std_dev = last_6_months['ActualAmount'].std()
    
    # Generate future dates
    last_date = monthly_costs['Date'].max()
    future_data = []
    
    for i in range(1, months_ahead + 1):
        next_date = last_date + pd.DateOffset(months=i)
        
        # Add some trend/seasonality simulation
        trend_factor = 1 + (i * 0.02) # Assumes 2% monthly increase
        forecast = avg_cost * trend_factor
        
        future_data.append({
            "Date": next_date,
            "ForecastAmount": round(forecast, 2),
            "LowerBound": round(forecast - std_dev, 2),
            "UpperBound": round(forecast + std_dev, 2),
            "Type": "Forecast"
        })
        
    return pd.DataFrame(future_data)

# =============================================================================
# VENDOR RELIABILITY SCORING
# =============================================================================

def calculate_vendor_score(df_vendor: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate composite reliability score for vendors.
    Score = (Rating * 10) + (QualityScore * 0.4) + ((10 - Delay) * 2)
    
    Args:
        df_vendor: DataFrame with VendorID, Rating, AvgDeliveryDelay, QualityScore
        
    Returns:
        DataFrame including CompositeScore and Tier
    """
    df = df_vendor.copy()
    
    # Normalize delay score (Max delay usually around 10 days, so 10-Delay gives points)
    df['DelayScore'] = (10 - df['AvgDeliveryDelay']).clip(lower=0) * 2
    
    # Weighted calculation
    # Rating (1-5) -> Max 50 points
    # Quality (0-100) -> Max 40 points
    # Delay -> Max 20 points
    # Total potential ~110, we normalize to 100
    
    df['RawScore'] = (df['Rating'] * 10) + (df['QualityScore'] * 0.4) + df['DelayScore']
    df['CompositeScore'] = df['RawScore'].clip(upper=100).round(1)
    
    def get_tier(score):
        if score >= 90: return "Strategic Partner"
        elif score >= 80: return "Preferred"
        elif score >= 70: return "Standard"
        else: return "At Risk"
        
    df['VendorTier'] = df['CompositeScore'].apply(get_tier)
    
    return df

def get_failure_root_cause(df_wo: pd.DataFrame) -> pd.Series:
    """
    Analyze the root cause of failures.
    """

    breakdown_wo = df_wo[df_wo['MaintenanceType'] == 'Breakdown']

    if breakdown_wo.empty:
        return pd.Series(dtype=str)

    return breakdown_wo['FailureCode'].value_counts()
