# Medication Adherence ML Model Analysis

This document explains the machine learning model used for detecting anomalies and drift in patient medication adherence for the Med Monitor IoT system.

## 1. Algorithm Overview: Random Forest Classifier

We selected the **Random Forest Classifier** as the primary supervised learning model for this task.

### How it Works
Random Forest is an ensemble learning method that constructs a multitude of decision trees during training. It follows these key principles:
- **Bootstrap Aggregating (Bagging):** It trains multiple decision trees on different random subsets (with replacement) of the training data.
- **Random Feature Selection:** At each node split in a tree, it only considers a random subset of features, further increasing diversity among trees.
- **Voting:** For classification, the final output is determined by a majority vote of all individual trees.

### Detailed Analysis
The model uses features such as raw intake time, rolling averages, and historical time differences to identify "normal" behavior. When an intake occurs significantly outside the established pattern (detected via branching paths in the decision trees), the model flags it as an anomaly.

## 2. Why Random Forest?

We chose Random Forest over other common models for several critical reasons:

### Robustness to Outliers
Medication data can have "legitimate" one-off variations (e.g., a time zone change or a specific event). Random Forest is less sensitive to individual outliers compared to sensitive models like Linear Regression or SVM without careful kernel tuning.

### Capturing Non-Linear Relationships
Adherence patterns are often non-linear (e.g., someone might take medicine early on weekends but consistently late on weekdays). Random Forest handles these step-wise and non-linear interactions naturally without complex feature engineering.

### Feature Importance
Random Forest provides built-in metrics to understand which features drive the prediction. This is vital for medical transparency—knowing if a "drift" was flagged because of the `rolling_mean_7` or the `day_of_week`.

### High Accuracy & Low Overfitting
By averaging multiple trees, Random Forest significantly reduces the risk of overfitting the model to specific noise in the IoT data.

## 3. Dataset Features

The model utilizes the following features generated from raw IoT scans:
- **`time_minutes`**: The primary indicator (minutes from midnight).
- **`prev_time_minutes`**: Detects sudden jumps from the previous day's intake.
- **`rolling_mean_7`**: Establishes the baseline "normal" for the patient over the last week.
- **`rolling_std_7`**: Measures the consistency of the patient's habits.
- **`day_of_week` / `is_weekend`**: Accounts for lifestyle changes in scheduled routines.

## 4. Evaluation Metrics

In the analysis script, we report:
- **Accuracy**: Overall percentage of correct predictions.
- **Precision**: How many flagged anomalies were actually anomalies.
- **Recall**: How many of the actual anomalies were successfully flagged.
- **F1-Score**: The harmonic mean of precision and recall (ideal for imbalanced data like this).
- **Confusion Matrix**: Shows where the model is confusing normal behavior with drift.
