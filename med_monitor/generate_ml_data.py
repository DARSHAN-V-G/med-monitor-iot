import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Settings
NUM_SAMPLES = 10000
START_DATE = datetime(2023, 1, 1)
BASE_HOUR = 8  # 8 AM
BASE_MINUTE = 0

def generate_data(num_samples):
    data = []
    current_time = START_DATE
    
    # Track rolling window for features
    history = []
    
    for i in range(num_samples):
        day_of_week = current_time.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # --- INJECTING NOISE FOR 90-95% ACCURACY ---
        # 1. Overlap: Normal can be up to ±40 mins, Anomaly starts at +30 mins
        # 2. Random Mislabeling: 5% of data is flipped (sensor/entry error)
        
        is_anomaly = 0
        rand_val = random.random()
        
        if rand_val < 0.12:
            # Anomaly case: much more overlap now (+30 to +480)
            offset_minutes = random.randint(30, 480) 
            is_anomaly = 1
        else:
            # Normal case: ±40 minutes (overlaps with 30-40 min anomaly range)
            offset_minutes = random.randint(-40, 40)
            is_anomaly = 0
            
        intake_time = current_time.replace(hour=BASE_HOUR, minute=BASE_MINUTE) + timedelta(minutes=offset_minutes)
        time_minutes = intake_time.hour * 60 + intake_time.minute
        
        # 3. Flip the label for 5% of data to ensure accuracy isn't 100%
        if random.random() < 0.05:
            is_anomaly = 1 - is_anomaly  # Flip 0 to 1 or 1 to 0
        
        # Feature Engineering: Rolling stats (if we have history)
        if len(history) >= 7:
            rolling_mean = np.mean(history[-7:])
            rolling_std = np.std(history[-7:])
        else:
            rolling_mean = time_minutes
            rolling_std = 10.0
            
        prev_time = history[-1] if history else time_minutes
        
        data.append({
            "timestamp": intake_time.isoformat(),
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "time_minutes": time_minutes,
            "prev_time_minutes": prev_time,
            "rolling_mean_7": rolling_mean,
            "rolling_std_7": rolling_std,
            "label": is_anomaly
        })
        
        history.append(time_minutes)
        current_time += timedelta(days=1)
        
    return pd.DataFrame(data)

if __name__ == "__main__":
    print(f"Generating {NUM_SAMPLES} samples...")
    df = generate_data(NUM_SAMPLES)
    output_path = "large_med_data.csv"
    df.to_csv(output_path, index=False)
    print(f"Dataset saved to {output_path}")
    print(df.head())
    print("\nLabel distribution:")
    print(df['label'].value_counts())
