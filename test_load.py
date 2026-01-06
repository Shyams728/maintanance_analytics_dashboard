import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

files = [
    "Fact_Maintenance_WorkOrders_Enriched.csv",
    "Fact_Sensor_Readings.csv",
    "Dim_Equipment.csv",
    "Fact_Budget_vs_Actual.csv"
]

for f in files:
    path = os.path.join(DATA_DIR, f)
    print(f"Loading {f} from {path}...")
    try:
        df = pd.read_csv(path)
        print(f"  Successfully loaded {f}, shape: {df.shape}")
    except Exception as e:
        print(f"  Error loading {f}: {e}")
