# Documentation: Random Forest Model for Predicting 'seen'

This notebook implements a Random Forest model to predict the `seen` variable for various indicators based on historical data. Below is a detailed explanation of the process:

---

## 1. **Data Loading and Preprocessing**
- **Data Source**: The dataset is loaded from a CSV file (`FullIndicatorMatrix.csv`).
- **Sorting**: Data is sorted by `indicator` and `date` to ensure chronological order.
- **Missing Values**: Missing values are forward-filled using `ffill()`.

---

## 2. **Feature Engineering**
Several features are created to capture historical patterns and trends:

### 2.1 **Time-Based Features**
- `days_since_last_seen`: Days since the indicator was last seen.
- `dayofweek`: Day of the week (0 = Monday, 6 = Sunday).
- `is_weekend`: Binary feature indicating whether the day is a weekend.

### 2.2 **Rolling and Exponential Weighted Moving Average (EWM) Features**
- `ewm_seen`: Exponential weighted moving average of `seen` with a short span (3 days).
- `seen_count_last_3`: Sum of `seen` values over the last 3 days.
- `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_30`: Rolling averages of `seen` over 7, 14, and 30 days.
- `ewm_seen_long`: EWM of `seen` with a longer span (10 days).
- `total_seen_last_7`: Total `seen` values over the last 7 days.
- `total_days_not_seen_last_7`: Days not seen in the last 7 days.

### 2.3 **Activity Features**
- `activity_score`: Total number of times the indicator was seen.
- `activity_score_normalized`: Normalized activity score (scaled between 0 and 1).

---

## 3. **Feature Scaling**
- **Scaler**: `MinMaxScaler` is used to normalize all features to a range of 0 to 1.

---

## 4. **Model Training**
- **Features**: A subset of engineered features is selected for training.
- **Target Variable**: `seen` (binary classification: 1 = seen, 0 = not seen).
- **Train-Test Split**: The first 80% of the data is used for training.
- **Model**: A `RandomForestClassifier` with `class_weight='balanced'` is trained to handle class imbalance.

---

## 5. **Real-History Evaluation**
- **Window-Based Prediction**: Predictions are made using a weighted window of the last 7 days of data.
- **Weights**: Exponential weights are applied to emphasize recent data.
- **Evaluation**: For each indicator:
  - The model predicts the `seen` value for the next day based on the weighted window.
  - True and predicted labels are stored for evaluation.

---

## 6. **Model Evaluation**
- **Metrics**:
  - **Classification Report**: Precision, recall, F1-score, and support for each class.
  - **Confusion Matrix**: Breakdown of true positives, true negatives, false positives, and false negatives.
- **Additional Metrics**:
  - Percentage of true positives among predicted positives.
  - Ratio of true positives to total predicted positives.

---

## 7. **Prediction Summary**
- A summary table is created for each indicator, showing:
  - `Indicator`: The unique identifier for the indicator.
  - `Actual Seen`: The true value of `seen`.
  - `Predicted Seen`: The model's prediction for `seen`.

---

## 8. **Insights**
- **True Positives**: Cases where the model correctly predicted `seen = 1`.
- **False Positives**: Cases where the model incorrectly predicted `seen = 1`.
- **Performance Metrics**:
  - Percentage of true positives among predicted positives.
  - Ratio of true positives to false positives.

---

## 9. **Code Outputs**
- **Classification Report**: Printed to the console.
- **Confusion Matrix**: Printed to the console.
- **Prediction Summary**: A DataFrame summarizing predictions for each indicator.
- **Additional Metrics**: Printed to the console for interpretability.

---

## 10. **Future Improvements**
- **Cross-Validation**: Use cross-validation to better evaluate model performance.
- **Hyperparameter Tuning**: Optimize the Random Forest model using `GridSearchCV` or `RandomizedSearchCV`.
- **Feature Importance**: Analyze feature importances to understand which features contribute most to predictions.
- **Visualization**: Add plots for feature importance, confusion matrix, and prediction trends.

This documentation provides a comprehensive overview of the process implemented in the notebook.