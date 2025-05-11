# Temporal and Mismatch Feature Engineering Documentation

## **Overview**
This document explains the temporal and mismatch features calculated for the dataset, their formulas, and their significance in forecasting and analysis.

---

## **1. Temporal Features**

### **1.1 Cumulative Seen**
- **Formula**:
  ```python
  df['cumulative_seen'] = df.groupby('indicator')['seen'].cumsum()
  ```
- **Description**: Tracks the cumulative count of `seen` events for each `indicator` over time.
- **Significance**: Helps identify the overall visibility trend of an indicator.

---

### **1.2 Days Since Last Seen**
- **Formula**:
  ```python
  df['days_since_last_seen'] = (
      df.groupby('indicator')['date']
      .transform(lambda x: x - x.where(df['seen'] == 1).ffill())
      .dt.days
  )
  ```
- **Description**: Measures the number of days since the last `seen` event for each `indicator`.
- **Significance**: Indicates how recently an indicator was observed, which can be useful for forecasting.

---

### **1.3 Seen Streak**
- **Formula**:
  ```python
  def compute_seen_streak(series):
      streak = 0
      output = []
      for val in series:
          if val == 1:
              streak += 1
          else:
              streak = 0
          output.append(streak)
      return output

  df['seen_streak'] = df.groupby('indicator')['seen'].transform(compute_seen_streak)
  ```
- **Description**: Tracks the current streak of consecutive `seen` events for each `indicator`.
- **Significance**: Highlights periods of consistent visibility.

---

### **1.4 Rolling Seen Ratio (14 Days)**
- **Formula**:
  ```python
  df['rolling_seen_ratio_14d'] = df.groupby('indicator')['seen'].transform(lambda x: x.rolling(14, min_periods=1).mean())
  ```
- **Description**: Computes the rolling average of `seen` events over the past 14 days.
- **Significance**: Captures short-term visibility trends.

---

### **1.5 Rolling Seen Standard Deviation (14 Days)**
- **Formula**:
  ```python
  df['rolling_seen_std_14d'] = df.groupby('indicator')['seen'].transform(lambda x: x.rolling(14, min_periods=1).std())
  ```
- **Description**: Measures the variability of `seen` events over the past 14 days.
- **Significance**: Indicates the stability or volatility of visibility.

---

### **1.6 Rolling Seen Ratio (7 Days)**
- **Formula**:
  ```python
  temporal_features_df['rolling_seen_ratio_7d'] = (
      temporal_features_df.groupby('indicator')['seen'].transform(lambda x: x.rolling(7, min_periods=1).mean())
  )
  ```
- **Description**: Computes the rolling average of `seen` events over the past 7 days.
- **Significance**: Provides a shorter-term view of visibility trends.

---

### **1.7 Seen Ratio Difference**
- **Formula**:
  ```python
  temporal_features_df['seen_ratio_diff'] = (
      temporal_features_df['rolling_seen_ratio_14d'] -
      temporal_features_df.groupby('indicator')['rolling_seen_ratio_14d'].shift(7)
  )
  ```
- **Description**: Calculates the difference in rolling seen ratios between the past 14 days and the previous 7 days.
- **Significance**: Highlights changes in visibility trends.

---

### **1.8 Observation Ratio Spike**
- **Formula**:
  ```python
  temporal_features_df['obs_ratio_spike'] = (
      temporal_features_df['rolling_obs_14d'] / (temporal_features_df['rolling_obs_7d'] + 1e-6)
  )
  ```
- **Description**: Measures the spike in observation activity by comparing 14-day and 7-day rolling averages.
- **Significance**: Identifies sudden increases in activity.

---

### **1.9 Recent Drop Flag**
- **Formula**:
  ```python
  temporal_features_df['recent_drop_flag'] = (
      ((temporal_features_df['seen_streak_prev'] >= 5) & (temporal_features_df['seen_streak'] == 0)).astype(int)
  )
  ```
- **Description**: Flags indicators that recently dropped visibility after a streak of at least 5 days.
- **Significance**: Useful for identifying sudden visibility drops.

---

### **1.10 Volatility Ratio**
- **Formula**:
  ```python
  temporal_features_df['volatility_ratio'] = temporal_features_df['rolling_seen_std_14d'] / (temporal_features_df['rolling_seen_ratio_14d'] + 1e-5)
  ```
- **Description**: Measures the ratio of visibility variability to the rolling average visibility.
- **Significance**: Highlights indicators with unstable visibility patterns.

---

## **2. Mismatch Features**

### **2.1 High Activity Not Seen**
- **Formula**:
  ```python
  df['high_activity_not_seen'] = ((df['observations'] >= high_thresh) & (df['seen'] == 0)).astype(int)
  ```
- **Description**: Flags instances where activity is high but the indicator is not seen.
- **Significance**: Identifies potential mismatches between activity and visibility.

---

### **2.2 Low Activity Seen**
- **Formula**:
  ```python
  df['low_activity_seen'] = ((df['observations'] <= low_thresh) & (df['seen'] == 1)).astype(int)
  ```
- **Description**: Flags instances where activity is low but the indicator is seen.
- **Significance**: Highlights unusual visibility patterns.

---

### **2.3 High Activity Not Seen Ratio (14 Days)**
- **Formula**:
  ```python
  df['high_activity_not_seen_ratio_14d'] = df.groupby('indicator')['high_activity_not_seen'].transform(
      lambda x: x.rolling(14, min_periods=1).mean()
  )
  ```
- **Description**: Computes the rolling average of high activity not seen over the past 14 days.
- **Significance**: Tracks the frequency of mismatches over time.

---

### **2.4 Low Activity Seen Ratio (14 Days)**
- **Formula**:
  ```python
  df['low_activity_seen_ratio_14d'] = df.groupby('indicator')['low_activity_seen'].transform(
      lambda x: x.rolling(14, min_periods=1).mean()
  )
  ```
- **Description**: Computes the rolling average of low activity seen over the past 14 days.
- **Significance**: Tracks the frequency of unusual visibility patterns.

---

## **3. Feature Engineering Summary**
The features described above are used to analyze and forecast visibility trends for indicators. Temporal features capture patterns over time, while mismatch features highlight discrepancies between activity and visibility. These features are combined to build predictive models and identify actionable insights.
