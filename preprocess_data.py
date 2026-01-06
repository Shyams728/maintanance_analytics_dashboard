
import pandas as pd
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def create_dim_date(start_date, end_date):
    """Creates a Date Dimension table."""
    date_range = pd.date_range(start=start_date, end=end_date)
    dim_date = pd.DataFrame({'Date': date_range})
    
    dim_date['Date'] = dim_date['Date'].dt.date
    dim_date['Year'] = pd.to_datetime(dim_date['Date']).dt.year
    dim_date['MonthName'] = pd.to_datetime(dim_date['Date']).dt.strftime('%B')
    dim_date['MonthNumber'] = pd.to_datetime(dim_date['Date']).dt.month
    dim_date['Quarter'] = pd.to_datetime(dim_date['Date']).dt.quarter
    dim_date['WeekNumber'] = pd.to_datetime(dim_date['Date']).dt.isocalendar().week
    dim_date['DayOfWeek'] = pd.to_datetime(dim_date['Date']).dt.day_name()
    dim_date['IsWorkingDay'] = pd.to_datetime(dim_date['Date']).dt.dayofweek < 5 # Mon=0, Sun=6
    
    return dim_date

def process_work_orders():
    """Enriches Fact_Maintenance_WorkOrders."""
    df = pd.read_csv(os.path.join(DATA_DIR, "Fact_Maintenance_WorkOrders.csv"))
    
    # 1. Maintenance Category
    df['Maintenance Category'] = df['MaintenanceType'].apply(
        lambda x: "Planned" if x == "Preventive" else "Unplanned"
    )
    
    # 2. Cost Segment
    def get_cost_segment(cost):
        if cost > 10000: return "High"
        if cost > 2000: return "Medium"
        return "Low"
        
    df['Cost Segment'] = df['TotalCost'].apply(get_cost_segment)
    
    return df

def process_products():
    """Enriches Dim_Product."""
    df = pd.read_csv(os.path.join(DATA_DIR, "Dim_Product.csv"))
    
    # 3. Stock Status
    def get_stock_status(row):
        if row['CurrentStock'] <= row['ReorderPoint']: return "Critical"
        if row['CurrentStock'] <= row['SafetyStock']: return "Stockout Risk"
        return "Healthy"

    df['Stock Status'] = df.apply(get_stock_status, axis=1)
    
    return df

def main():
    print("Preprocessing data...")
    
    # 0. Generate Dim_Date
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    df_date = create_dim_date(start_date, end_date)
    df_date.to_csv(os.path.join(DATA_DIR, "Dim_Date.csv"), index=False)
    print(f"Generated Dim_Date.csv ({len(df_date)} rows)")
    
    # 1. Process Work Orders
    df_wo = process_work_orders()
    df_wo.to_csv(os.path.join(DATA_DIR, "Fact_Maintenance_WorkOrders_Enriched.csv"), index=False)
    print(f"Generated Fact_Maintenance_WorkOrders_Enriched.csv ({len(df_wo)} rows)")
    
    # 2. Process Products
    df_prod = process_products()
    df_prod.to_csv(os.path.join(DATA_DIR, "Dim_Product_Enriched.csv"), index=False)
    print(f"Generated Dim_Product_Enriched.csv ({len(df_prod)} rows)")
    
    print("Preprocessing complete.")

if __name__ == "__main__":
    main()
