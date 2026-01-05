import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

# Configuration
DATA_DIR = "d:/data_science/power_bi/data"
MODEL_PATH = "d:/data_science/power_bi/rul_model.joblib"

def load_data():
    """Loads sensor data and filters for valid RUL training samples."""
    df = pd.read_csv(os.path.join(DATA_DIR, "Fact_Sensor_Readings.csv"))
    
    # We want to train on data that has a valid RUL closer to failure
    # and also some healthy data (RUL=999) to teach it "safe" state.
    # For regression, we might cap RUL at 30 days or similar for stability,
    # but for this demo, let's just use the raw values but cap 999 at 100.
    
    df['Training_RUL'] = df['_RUL_Days'].apply(lambda x: 50 if x > 50 else x)
    
    # Filter out extremely noisy outliers if any
    df = df[(df['Temperature_C'] > 0) & (df['Temperature_C'] < 200)]
    
    return df

def train_model():
    """Trains a Random Forest Regressor to predict RUL."""
    print("Loading data...")
    df = load_data()
    
    # Features & Target
    X = df[['Temperature_C', 'Vibration_mm_s']]
    y = df['Training_RUL']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train
    print("Training Random Forest Model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Model Trained. MAE: {mae:.2f} days, R2: {r2:.2f}")
    
    # Save
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return model

def predict_rul_single(temp, vib):
    """Predicts RUL for a single reading."""
    if not os.path.exists(MODEL_PATH):
        return None
        
    model = joblib.load(MODEL_PATH)
    prediction = model.predict([[temp, vib]])[0]
    
    # Post-process: If prediction is close to max cap, return "Healthy"
    if prediction > 40:
        return "Healthy (> 40 days)"
    else:
        return f"{prediction:.1f} days"

def predict_rul_batch(df_input):
    """Predicts RUL for a dataframe with Temperature_C and Vibration_mm_s."""
    if not os.path.exists(MODEL_PATH):
        return [None] * len(df_input)
        
    model = joblib.load(MODEL_PATH)
    predictions = model.predict(df_input[['Temperature_C', 'Vibration_mm_s']])
    return predictions

if __name__ == "__main__":
    train_model()
