
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from kpi_calculations import calculate_equipment_availability, calculate_mtbf

def test_availability():
    print("Testing Availability Logic...")
    # Mock data: 1 machine, 10 days, 24 hours downtime total
    df_mock = pd.DataFrame({
        'DowntimeHours': [24],
        'EquipmentID': ['E1']
    })
    
    # 1 machine * 10 days * 24h = 240h total. 24h downtime = 90% availability
    res = calculate_equipment_availability(df_mock, equipment_count=1, days=10)
    print(f"Result for 10 days, 1 machine, 24h downtime: {res['Availability_Pct']}%")
    assert res['Availability_Pct'] == 90.0
    
    # 2 machines * 5 days * 24h = 240h total. 24h downtime = 90% availability
    res2 = calculate_equipment_availability(df_mock, equipment_count=2, days=5)
    print(f"Result for 5 days, 2 machines, 24h downtime: {res2['Availability_Pct']}%")
    assert res2['Availability_Pct'] == 90.0
    print("Availability Test Passed!\n")

def test_mtbf():
    print("Testing MTBF Logic...")
    # Mock data: 10 days period. 1 failure. 10 hours unplanned downtime.
    df_mock = pd.DataFrame({
        'WorkOrderID': ['W1'],
        'DowntimeHours': [10.0],
        'EquipmentID': ['E1'],
        'MaintenanceType': ['Breakdown']
    })
    
    # MTBF = (10 days * 24h - 10h) / 1 failure = 230h
    res = calculate_mtbf(df_mock, days=10)
    print(f"Result for 10 days, 1 failure, 10h downtime: {res['MTBF_Hours'].values[0]} hrs")
    assert res['MTBF_Hours'].values[0] == 230.0
    print("MTBF Test Passed!\n")

if __name__ == "__main__":
    try:
        test_availability()
        test_mtbf()
        print("All KPI Verifications Passed!")
    except Exception as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)
