import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def train_and_evaluate(data_path):
    # Load dataset
    df = pd.read_csv(data_path)
    
    # Feature selection
    features = ['day_of_week', 'is_weekend', 'time_minutes', 'prev_time_minutes', 'rolling_mean_7', 'rolling_std_7']
    X = df[features]
    y = df['label']
    
    # Split data (80% training, 20% testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")
    
    # Initialize and train Random Forest Classifier
    # We choose Random Forest for its robustness to outliers and ability to capture non-linear relationships
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    
    # Evaluation metrics
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    # Feature Importance
    importances = model.feature_importances_
    feature_importance_df = pd.DataFrame({'Feature': features, 'Importance': importances})
    feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)
    print("\nFeature Importance:")
    print(feature_importance_df)
    
if __name__ == "__main__":
    data_path = "large_med_data.csv"
    try:
        train_and_evaluate(data_path)
    except FileNotFoundError:
        print(f"Error: {data_path} not found. Run generate_ml_data.py first.")
