import pandas as pd
import random
import os
from datetime import datetime, timedelta
import numpy as np

# Configuration
OUTPUT_DIR = "d:/data_science/power_bi/data"
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)
NUM_DAYS = (END_DATE - START_DATE).days + 1

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper function for random dates
def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

# 1. Dim_Product
products = [
    {"ProductID": "P001", "ProductName": "Hydraulic Pump X200", "Category": "Spare", "ReorderPoint": 5, "SafetyStock": 2, "UnitCost": 5000, "LeadTimeDays": 15, "MOQ": 1, "ABC_Class": "A", "UnitWeight": 25.5, "MaterialGroup": "Hydraulics"},
    {"ProductID": "P002", "ProductName": "Engine Oil 15W40 (L)", "Category": "Consumable", "ReorderPoint": 50, "SafetyStock": 20, "UnitCost": 500, "LeadTimeDays": 3, "MOQ": 20, "ABC_Class": "C", "UnitWeight": 0.9, "MaterialGroup": "Lubricants"},
    {"ProductID": "P003", "ProductName": "Conveyor Belt (m)", "Category": "Spare", "ReorderPoint": 10, "SafetyStock": 5, "UnitCost": 1500, "LeadTimeDays": 10, "MOQ": 10, "ABC_Class": "B", "UnitWeight": 5.0, "MaterialGroup": "Conveyors"},
    {"ProductID": "P004", "ProductName": "Bearing 6205-2RS", "Category": "Spare", "ReorderPoint": 20, "SafetyStock": 8, "UnitCost": 200, "LeadTimeDays": 5, "MOQ": 10, "ABC_Class": "C", "UnitWeight": 0.2, "MaterialGroup": "Bearings"},
    {"ProductID": "P005", "ProductName": "Air Filter AF-99", "Category": "Consumable", "ReorderPoint": 15, "SafetyStock": 5, "UnitCost": 800, "LeadTimeDays": 2, "MOQ": 5, "ABC_Class": "C", "UnitWeight": 1.2, "MaterialGroup": "Filters"},
    {"ProductID": "P006", "ProductName": "Gearbox Seal Kit", "Category": "Spare", "ReorderPoint": 8, "SafetyStock": 3, "UnitCost": 1200, "LeadTimeDays": 7, "MOQ": 1, "ABC_Class": "B", "UnitWeight": 0.5, "MaterialGroup": "Seals"},
    {"ProductID": "P007", "ProductName": "Drill Bit 150mm", "Category": "Consumable", "ReorderPoint": 10, "SafetyStock": 4, "UnitCost": 3500, "LeadTimeDays": 14, "MOQ": 5, "ABC_Class": "A", "UnitWeight": 12.0, "MaterialGroup": "Drilling"},
    {"ProductID": "P008", "ProductName": "Coolant (L)", "Category": "Consumable", "ReorderPoint": 40, "SafetyStock": 15, "UnitCost": 150, "LeadTimeDays": 2, "MOQ": 20, "ABC_Class": "C", "UnitWeight": 1.0, "MaterialGroup": "Fluids"},
]

# Add CurrentStock
for p in products:
    p["CurrentStock"] = random.randint(p["SafetyStock"], p["ReorderPoint"] + p["MOQ"])

df_product = pd.DataFrame(products)
df_product.to_csv(f"{OUTPUT_DIR}/Dim_Product.csv", index=False)
print("Generated Dim_Product.csv")

# 2. Dim_Equipment
equipment = [
    {"EquipmentID": "EX001", "EquipmentName": "Excavator 20T - Alpha", "Type": "Heavy Machinery", "Manufacturer": "CAT", "Model": "320D", "InstallDate": "2020-05-15", "Criticality": "High", "FunctionalLocation": "Mine_Pit_A"},
    {"EquipmentID": "DT001", "EquipmentName": "Dump Truck 100T - 01", "Type": "Heavy Machinery", "Manufacturer": "Komatsu", "Model": "HD785", "InstallDate": "2021-02-10", "Criticality": "High", "FunctionalLocation": "Haul_Road_1"},
    {"EquipmentID": "CR001", "EquipmentName": "Primary Crusher Unit", "Type": "Processing Plant", "Manufacturer": "Metso", "Model": "C120", "InstallDate": "2019-11-01", "Criticality": "High", "FunctionalLocation": "Crushing_Plant"},
    {"EquipmentID": "CV001", "EquipmentName": "Main Overland Conveyor", "Type": "Processing Plant", "Manufacturer": "Fenner", "Model": "CV-2000", "InstallDate": "2019-12-20", "Criticality": "Medium", "FunctionalLocation": "Transport_Zone"},
    {"EquipmentID": "DR001", "EquipmentName": "Drill Rig X5", "Type": "Heavy Machinery", "Manufacturer": "Sandvik", "Model": "D65", "InstallDate": "2022-06-01", "Criticality": "Medium", "FunctionalLocation": "Mine_Pit_B"},
    {"EquipmentID": "WL001", "EquipmentName": "Wheel Loader 980", "Type": "Heavy Machinery", "Manufacturer": "CAT", "Model": "980H", "InstallDate": "2021-08-15", "Criticality": "Medium", "FunctionalLocation": "Stockpile_Area"},
]
df_equipment = pd.DataFrame(equipment)
df_equipment.to_csv(f"{OUTPUT_DIR}/Dim_Equipment.csv", index=False)
print("Generated Dim_Equipment.csv")

# 3. Dim_Vendor (Enriched)
vendors = [
    {"VendorID": "V001", "VendorName": "Global Spares Ltd", "Rating": 4.5, "PaymentTerms": "Net 30", "Category": "Parts Supplier", "AvgDeliveryDelay": 2, "QualityScore": 95},
    {"VendorID": "V002", "VendorName": "Industrial Lubes Co", "Rating": 3.8, "PaymentTerms": "Net 45", "Category": "Consumables", "AvgDeliveryDelay": 5, "QualityScore": 88},
    {"VendorID": "V003", "VendorName": "Heavy Mech Services", "Rating": 4.8, "PaymentTerms": "Net 15", "Category": "Service Provider", "AvgDeliveryDelay": 0, "QualityScore": 98},
    {"VendorID": "V004", "VendorName": "Safety First Supplies", "Rating": 4.2, "PaymentTerms": "Net 30", "Category": "Safety Equipment", "AvgDeliveryDelay": 1, "QualityScore": 92},
    {"VendorID": "V005", "VendorName": "TechEquip Solutions", "Rating": 3.5, "PaymentTerms": "Net 60", "Category": "Equipment Dealer", "AvgDeliveryDelay": 8, "QualityScore": 80},
]
df_vendor = pd.DataFrame(vendors)
df_vendor.to_csv(f"{OUTPUT_DIR}/Dim_Vendor.csv", index=False)
print("Generated Dim_Vendor.csv")

# 4. Dim_Technician (NEW)
technicians = [
    {"TechnicianID": "T001", "Name": "John Smith", "SkillLevel": "Senior", "HourlyRate": 85},
    {"TechnicianID": "T002", "Name": "Alice Johnson", "SkillLevel": "Junior", "HourlyRate": 45},
    {"TechnicianID": "T003", "Name": "Robert Davis", "SkillLevel": "Master", "HourlyRate": 120},
    {"TechnicianID": "T004", "Name": "Emily Wilson", "SkillLevel": "Mid-Level", "HourlyRate": 65},
    {"TechnicianID": "T005", "Name": "Michael Brown", "SkillLevel": "Senior", "HourlyRate": 90},
]
df_technician = pd.DataFrame(technicians)
df_technician.to_csv(f"{OUTPUT_DIR}/Dim_Technician.csv", index=False)
print("Generated Dim_Technician.csv")

# 5. Fact_Inventory_Transactions
transactions = []
transaction_id = 1

# Initial Stock
for p in products:
    transactions.append({
        "TransactionID": f"TX{transaction_id:06d}",
        "Date": START_DATE.strftime("%Y-%m-%d"),
        "ProductID": p["ProductID"],
        "Quantity": random.randint(p["ReorderPoint"] + 10, p["ReorderPoint"] + 50),
        "Type": "Receipt",
        "PurchaseOrderID": f"PO{random.randint(1000, 9999)}",
        "BatchNumber": f"B{random.randint(100, 999)}",
        "UnitCost": p["UnitCost"]
    })
    transaction_id += 1

# Daily Transactions
current_date = START_DATE
while current_date <= END_DATE:
    # Random Issues
    num_issues = random.randint(0, 5)
    for _ in range(num_issues):
        p = random.choice(products)
        qty = random.randint(1, 5)
        transactions.append({
            "TransactionID": f"TX{transaction_id:06d}",
            "Date": current_date.strftime("%Y-%m-%d"),
            "ProductID": p["ProductID"],
            "Quantity": -qty, # Negative for issues
            "Type": "Issue",
            "PurchaseOrderID": "",
            "BatchNumber": "",
            "UnitCost": p["UnitCost"]
        })
        transaction_id += 1
    
    # Random Receipts (Replenishment)
    if random.random() < 0.15: # 15% chance of receipt
        p = random.choice(products)
        qty = random.randint(p["MOQ"], p["MOQ"] * 3)
        transactions.append({
            "TransactionID": f"TX{transaction_id:06d}",
            "Date": current_date.strftime("%Y-%m-%d"),
            "ProductID": p["ProductID"],
            "Quantity": qty,
            "Type": "Receipt",
            "PurchaseOrderID": f"PO{random.randint(10000, 99999)}",
            "BatchNumber": f"B{random.randint(1000, 9999)}",
            "UnitCost": p["UnitCost"] * random.uniform(0.95, 1.05) # Slight cost variation
        })
        transaction_id += 1
        
    current_date += timedelta(days=1)

df_inv = pd.DataFrame(transactions)
df_inv.to_csv(f"{OUTPUT_DIR}/Fact_Inventory_Transactions.csv", index=False)
print("Generated Fact_Inventory_Transactions.csv")

# 6. Fact_Maintenance_WorkOrders (Enriched with Delays)
work_orders = []
wo_id = 1
current_date = START_DATE
failure_codes = ["MECH01", "ELEC02", "HYDR03", "OPER04", "TIRE05"]

while current_date <= END_DATE:
    # Random Work Orders
    if random.random() < 0.5: # 50% chance of a work order
        eq = random.choice(equipment)
        tech = random.choice(technicians)
        is_preventive = random.random() < 0.65 
        
        if is_preventive:
            m_type = "Preventive"
            downtime = random.uniform(2, 8)
            labor_hours = random.uniform(2, 6)
            parts_cost = random.randint(500, 2000)
            failure_code = ""
            # Scheduled date logic
            scheduled_date = current_date - timedelta(days=random.randint(1, 7))
        else:
            m_type = "Breakdown"
            downtime = random.uniform(4, 48)
            labor_hours = random.uniform(4, 20)
            parts_cost = random.randint(5000, 25000)
            failure_code = random.choice(failure_codes)
            scheduled_date = None
            
        labor_cost = labor_hours * tech["HourlyRate"]
        total_cost = parts_cost + labor_cost
        
        # New: Simulate Delays
        delay_min = 0
        if random.random() < 0.2: # 20% chance of delay
            delay_min = random.randint(30, 240)
            
        work_orders.append({
            "WorkOrderID": f"WO{wo_id:05d}",
            "EquipmentID": eq["EquipmentID"],
            "TechnicianID": tech["TechnicianID"],
            "Date": current_date.strftime("%Y-%m-%d"),
            "ScheduledDate": scheduled_date.strftime("%Y-%m-%d") if scheduled_date else "",
            "MaintenanceType": m_type,
            "FailureCode": failure_code,
            "DowntimeHours": round(downtime, 2),
            "LaborHours": round(labor_hours, 2),
            "PartsCost": round(parts_cost, 2),
            "LaborCost": round(labor_cost, 2),
            "TotalCost": round(total_cost, 2),
            "DelayMinutes": delay_min,
            "RestockingDelay": 1 if delay_min > 60 else 0
        })
        wo_id += 1
    current_date += timedelta(days=1)

df_wo = pd.DataFrame(work_orders)
df_wo.to_csv(f"{OUTPUT_DIR}/Fact_Maintenance_WorkOrders.csv", index=False)
print("Generated Fact_Maintenance_WorkOrders.csv")

# 7. Fact_Budget_vs_Actual (Replaces Fact_Costs)
budget_data = []
cost_centers = ["CC_Maint_Heavy", "CC_Maint_Plant", "CC_Ops_Mining", "CC_Ops_Process"]
gl_accounts = ["GL_5001_Spares", "GL_5002_Labor", "GL_5003_Contractors", "GL_5004_Consumables"]

current_month = START_DATE.replace(day=1)
while current_month <= END_DATE:
    month_str = current_month.strftime("%Y-%m-01")
    
    for cc in cost_centers:
        for gl in gl_accounts:
            budget = random.randint(10000, 50000)
            actual = budget * random.uniform(0.8, 1.2) # +/- 20% variance
            
            budget_data.append({
                "Date": month_str,
                "CostCenter": cc,
                "GLAccount": gl,
                "BudgetAmount": round(budget, 2),
                "ActualAmount": round(actual, 2)
            })
            
    # Move to next month
    if current_month.month == 12:
        current_month = current_month.replace(year=current_month.year + 1, month=1)
    else:
        current_month = current_month.replace(month=current_month.month + 1)

df_budget = pd.DataFrame(budget_data)
df_budget.to_csv(f"{OUTPUT_DIR}/Fact_Budget_vs_Actual.csv", index=False)
print("Generated Fact_Budget_vs_Actual.csv")

# 8. Fact_Sensor_Readings (NEW)
# Simulating hourly readings for key equipment
sensor_readings = []
sensor_start = END_DATE - timedelta(days=90) # Last 90 days only to keep size manageable

print("Generating Sensor Data...")
eq_list = [e for e in equipment if e["Criticality"] == "High"]
current_ts = sensor_start

while current_ts <= END_DATE:
    for eq in eq_list:
        # Base healthy values
        temp = 75 + random.uniform(-5, 5) # C
        vibration = 2.5 + random.uniform(-0.5, 0.5) # mm/s
        
        # Inject anomalies occasionally
        if random.random() < 0.05:
            temp += random.uniform(10, 30)
        if random.random() < 0.05:
            vibration += random.uniform(2, 5)
            
        sensor_readings.append({
            "Timestamp": current_ts.strftime("%Y-%m-%d %H:%M:%S"),
            "EquipmentID": eq["EquipmentID"],
            "Temperature_C": round(temp, 1),
            "Vibration_mm_s": round(vibration, 2),
            "Status": "Alert" if temp > 100 or vibration > 6 else "Normal"
        })
    current_ts += timedelta(hours=4) # Every 4 hours

df_sensor = pd.DataFrame(sensor_readings)
df_sensor.to_csv(f"{OUTPUT_DIR}/Fact_Sensor_Readings.csv", index=False)
print("Generated Fact_Sensor_Readings.csv")
