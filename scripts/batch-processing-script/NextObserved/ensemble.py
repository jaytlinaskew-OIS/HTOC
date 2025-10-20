import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def add_rule_and_ensemble(output):
    features = ['last_seen', 'freq_1', 'freq_7', 'freq_30', 'avg_gap', 'burstiness']
    X = output[features]

    # Rule-based labels
    output['rule_1d'] = output['last_seen'].apply(lambda x: 1 if x == 0 else 0)
    output['rule_7d'] = output['last_seen'].apply(lambda x: 1 if x <= 6 else 0)
    output['rule_14d'] = output['last_seen'].apply(lambda x: 1 if x <= 13 else 0)
    output['rule_30d'] = output['last_seen'].apply(lambda x: 1 if x <= 29 else 0)
    output['rule_45d'] = output['last_seen'].apply(lambda x: 1 if x <= 44 else 0)

    y_1 = output['rule_1d']
    y_7 = output['rule_7d']
    y_14 = output['rule_14d']
    y_30 = output['rule_30d']
    y_45 = output['rule_45d']

    def train_logistic_model(X, y):
        if len(np.unique(y)) < 2:
            return np.full(len(y), np.nan)
        model = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression())
        ])
        model.fit(X, y)
        return model.predict_proba(X)[:, 1]

    output['prob_1d'] = train_logistic_model(X, y_1)
    output['prob_7d'] = train_logistic_model(X, y_7)
    output['prob_14d'] = train_logistic_model(X, y_14)
    output['prob_30d'] = train_logistic_model(X, y_30)
    output['prob_45d'] = train_logistic_model(X, y_45)

    # Ensemble, combines predictions from all models and prevents overfitting
    output['ensemble_1d'] = (
        0.3 * output['prob_1d'].astype(float) +
        0.25 * output['gbt_1'] +
        0.25 * output['weibull_1'] +
        0.2 * output['exp_1']
    )
    output['ensemble_7d'] = (
        0.3 * output['prob_7d'].astype(float) +
        0.25 * output['gbt_7'] +
        0.25 * output['weibull_7'] +
        0.2 * output['exp_7']
    )
    output['ensemble_14d'] = (
        0.3 * output['prob_14d'].astype(float) +
        0.25 * output['gbt_14'] +
        0.25 * output['weibull_14'] +
        0.2 * output['exp_14']
    )
    output['ensemble_30d'] = (
        0.3 * output['prob_30d'].astype(float) +
        0.25 * output['gbt_30'] +
        0.25 * output['weibull_30'] +
        0.2 * output['exp_30']
    )
    output['ensemble_45d'] = (
        0.3 * output['prob_45d'].astype(float) +
        0.25 * output['gbt_45'] +
        0.25 * output['weibull_45'] +
        0.2 * output['exp_45']
    )
    return output

def classify_window(prob, freq, high_thresh, label):
    if prob >= high_thresh and freq >= 2:
        return f"{label}: Highly likely"
    elif prob >= 0.07 and freq >= 1:
        return f"{label}: Possibly active"
    else:
        return f"{label}: Low confidence"

def add_confidence_and_format(output):
    output['confidence_1d'] = output.apply(
        lambda row: classify_window(float(row['ensemble_1d']), row['freq_1'], 0.6, '1-Day'), axis=1
    )
    output['confidence_7d'] = output.apply(
        lambda row: classify_window(float(row['ensemble_7d']), row['freq_7'], 0.6, '7-Day'), axis=1
    )
    output['confidence_14d'] = output.apply(
        lambda row: classify_window(float(row['ensemble_14d']), row['freq_14'], 0.6, '14-Day'), axis=1
    )
    output['confidence_30d'] = output.apply(
        lambda row: classify_window(float(row['ensemble_30d']), row['freq_30'], 0.6, '30-Day'), axis=1
    )
    output['confidence_45d'] = output.apply(
        lambda row: classify_window(float(row['ensemble_45d']), row['freq_45'], 0.6, '45-Day'), axis=1
    )

    # Format percentages
    for col in ['prob_1d', 'prob_7d', 'prob_14d', 'prob_30d','prob_45d', 'ensemble_1d', 'ensemble_7d', 'ensemble_14d', 'ensemble_30d', 'ensemble_45d']:
        output[col] = np.clip(output[col].astype(float) * 100, 0, 100).round(2).astype(str) + '%'
    return output

def build_production_output(output):
    warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)
    production_output = output[[
        'indicator', 'seen_today', 'freq_1', 'freq_7', 'freq_30',
        'ensemble_1d', 'confidence_1d',
        'ensemble_7d', 'confidence_7d',
        'ensemble_14d', 'confidence_14d',
        'ensemble_30d', 'confidence_30d',
        'ensemble_45d', 'confidence_45d'
    ]].copy()
    production_output.rename(columns={
        'indicator': 'Indicator',
        'seen_today': 'Observed Today',
        'freq_1': 'Frequency (1d)',
        'freq_7': 'Frequency (7d)',
        'freq_30': 'Frequency (30d)',
        'freq_45': 'Frequency (45d)',
        'ensemble_1d': 'Probability: 1-Day',
        'confidence_1d': 'Confidence: 1-Day',
        'ensemble_7d': 'Probability: 7-Day',
        'confidence_7d': 'Confidence: 7-Day',
        'ensemble_14d': 'Probability: 14-Day',
        'confidence_14d': 'Confidence: 14-Day',
        'ensemble_30d': 'Probability: 30-Day',
        'confidence_30d': 'Confidence: 30-Day',
        'confidence_45d': 'Confidence: 45-Day'
    }, inplace=True)
    return production_output
