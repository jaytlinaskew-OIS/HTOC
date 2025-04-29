# Documentation: LSTM-Based Time Series Forecasting

This document provides an in-depth overview of the key features, preprocessing steps, and modeling techniques used in the LSTM-based time series forecasting process. It explains the significance of each feature, its role in the model, and the modeling components utilized. Additionally, it includes detailed explanations of the rationale behind each step and the potential challenges encountered during implementation.

## 1. Features and Their Importance

### 1.1 days_since_last_seen
- **Description**: The number of days since the indicator was last observed (`seen == 1`).
- **Importance**: Captures temporal gaps in activity, which can indicate patterns of inactivity or resurgence.
- **Calculation**: Derived by subtracting the last observed date from the current date for each indicator.

### 1.2 ewm_seen (Exponential Weighted Mean of seen)
- **Description**: A short-term exponentially weighted moving average of the `seen` column.
- **Importance**: Highlights recent activity trends while giving more weight to recent observations.
- **Parameters**: The smoothing factor (`alpha`) is tuned to balance sensitivity to recent changes versus long-term trends.

### 1.3 rolling_mean_X (Rolling Averages)
- **Description**: Rolling averages of the `seen` column over different time windows (e.g., 7, 14, 30 days).
- **Importance**: Provides a smoothed view of activity over specific time periods, helping to identify periodic patterns.
- **Challenges**: Selecting appropriate window sizes to capture meaningful trends without over-smoothing.

### 1.4 total_seen_last_X
- **Description**: Total occurrences of `seen == 1` in the last X days (e.g., 3, 7, 14, 30 days).
- **Importance**: Quantifies recent activity levels, which can be used to detect bursts of activity.
- **Use Case**: Particularly useful for identifying short-term spikes in activity.

### 1.5 activity_score
- **Description**: The total number of times an indicator has been observed (`seen == 1`) over its entire history.
- **Importance**: Serves as a cumulative measure of an indicator's overall activity.
- **Normalization**: Often combined with `activity_score_normalized` for better interpretability.

### 1.6 activity_score_normalized
- **Description**: A normalized version of `activity_score` scaled between 0 and 1.
- **Importance**: Ensures comparability across indicators with different activity levels.
- **Normalization Method**: Min-max scaling is applied to bring all scores into the [0, 1] range.

### 1.7 smoothed_days_since_last_seen
- **Description**: A smoothed version of `days_since_last_seen` using an exponential smoothing function.
- **Importance**: Reduces noise in the raw `days_since_last_seen` values, making trends more apparent.
- **Implementation**: Uses a smoothing factor to control the degree of noise reduction.

## 2. Preprocessing Steps

### 2.1 Data Cleaning
- **Steps**:
    - Drop unnecessary columns (e.g., `API_UserName`, `observations`, `day`, `month`).
    - Ensure the `date` column is in datetime format.
    - Handle missing values by forward-filling or imputing based on domain knowledge.
- **Purpose**: Simplifies the dataset and ensures consistency in date handling.
- **Challenges**: Dealing with missing or inconsistent data entries.

### 2.2 Feature Engineering
- **Steps**:
    - Calculate `days_since_last_seen` for each indicator.
    - Compute rolling averages (`rolling_mean_X`) and exponential moving averages (`ewm_seen`).
    - Generate lagged features for key columns (e.g., `ewm_seen`, `rolling_mean_30`).
    - Create interaction terms between features to capture complex relationships.
- **Purpose**: Extract meaningful patterns and trends from raw data.
- **Challenges**: Avoiding overfitting by limiting the number of engineered features.

### 2.3 Sequence Generation
- **Steps**:
    - Create sequences of lagged features for each indicator with a fixed window size (e.g., 15 lags).
    - Include the target label (`seen`) for each sequence.
    - Ensure sequences are padded or truncated to maintain uniform length.
- **Purpose**: Prepare the data in a format suitable for LSTM input.
- **Challenges**: Balancing sequence length to capture sufficient context without introducing excessive noise.

## 3. Modeling Components

### 3.1 LSTM Model Architecture
- **Layers**:
    - **Bidirectional LSTM**: Captures both forward and backward temporal dependencies.
    - **Batch Normalization**: Normalizes activations to improve training stability.
    - **Dropout**: Reduces overfitting by randomly deactivating neurons during training.
    - **Dense Layer**: Maps the LSTM output to a single prediction (`seen`).
- **Purpose**: Leverages the temporal structure of the data to predict future activity.
- **Challenges**: Tuning hyperparameters such as the number of LSTM units and dropout rate.

### 3.2 Loss Function
- **Type**: Focal Loss
- **Purpose**: Addresses class imbalance by focusing more on hard-to-classify examples.
- **Implementation**: Includes a tunable focusing parameter to control the degree of emphasis on difficult examples.

### 3.3 Metrics
- **Accuracy**: Measures the proportion of correct predictions.
- **AUC**: Evaluates the model's ability to distinguish between classes.
- **Precision and Recall**: Provide additional insights into the model's performance on imbalanced datasets.

## 4. Evaluation and Post-Processing

### 4.1 Threshold Adjustment
- **Description**: Adjusts the prediction threshold dynamically based on `activity_score_normalized`.
- **Purpose**: Tailors the decision boundary for each indicator based on its historical activity.
- **Implementation**: Uses a scaling factor to modulate the threshold for each indicator.

### 4.2 False Positives and Negatives
- **Description**: Identifies and analyzes incorrect predictions.
- **Purpose**: Provides insights into model weaknesses and areas for improvement.
- **Analysis**: Includes feature importance analysis to understand the root causes of misclassifications.

### 4.3 Visualization
- **Description**: Plots activity trends for false positives and negatives.
- **Purpose**: Helps understand the temporal patterns leading to misclassifications.
- **Tools**: Uses libraries like Matplotlib or Seaborn for detailed visualizations.

## 5. Summary

This process combines robust feature engineering, sequence generation, and LSTM modeling to predict the future activity of indicators. By leveraging temporal patterns, dynamic thresholds, and advanced evaluation techniques, the model achieves high accuracy while addressing class imbalance and variability across indicators. The detailed preprocessing and modeling steps ensure the framework is adaptable to a wide range of time series forecasting tasks.