import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from lifelines import WeibullAFTFitter

def train_predict(model_cls, X, y):
    if len(np.unique(y)) < 2:
        return np.full(len(y), np.nan)
    model = Pipeline([('scaler', StandardScaler()), ('clf', model_cls())])
    model.fit(X, y)
    return model.predict_proba(X)[:, 1]

def train_gbt(X, y):
    if len(np.unique(y)) < 2:
        return np.full(len(y), np.nan)
    model = GradientBoostingClassifier()
    model.fit(X, y)
    return model.predict_proba(X)[:, 1]

def fit_weibull_aft(X, avg_gap, event):
    aft_df = X.copy()
    aft_df['duration'] = avg_gap
    aft_df['event'] = event
    aft = WeibullAFTFitter()
    aft.fit(aft_df, duration_col='duration', event_col='event')
    return aft

def get_model_outputs(features_df, df):
    df_pred = features_df.copy()
    X = df_pred[['last_seen', 'freq_7', 'freq_14' ,'freq_30', 'freq_45', 'avg_gap', 'burstiness']]
    y_7 = df_pred['label_7']
    y_14 = df_pred['label_14']
    y_30 = df_pred['label_30']
    y_45 = df_pred['label_45']

    # Logistic Regression, Estimate baseline probabilities
    df_pred['logistic_7'] = train_predict(LogisticRegression, X, y_7)
    df_pred['logistic_14'] = train_predict(LogisticRegression, X, y_14)
    df_pred['logistic_30'] = train_predict(LogisticRegression, X, y_30)
    df_pred['logistic_45'] = train_predict(LogisticRegression, X, y_45)


    # Gradient Boosted Trees, Non-linear patterns and feature interactions
    df_pred['gbt_7'] = train_gbt(X, y_7)
    df_pred['gbt_14'] = train_gbt(X, y_14)
    df_pred['gbt_30'] = train_gbt(X, y_30)
    df_pred['gbt_45'] = train_gbt(X, y_45)

    # Exponential Model, memoryless Poisson process for frequency
    rate = (df_pred['freq_30'] / 30).clip(lower=1e-6)
    df_pred['exp_7'] = 1 - np.exp(-rate * 7)
    df_pred['exp_14'] = 1 - np.exp(-rate * 14)
    df_pred['exp_30'] = 1 - np.exp(-rate * 30)
    df_pred['exp_45'] = 1 - np.exp(-rate * 45)
    df_pred['exp_today'] = 1 - np.exp(-rate * 1)

    # Weibull AFT Model, time-to-event behavor, burstiness
    aft = fit_weibull_aft(X, df_pred['avg_gap'], y_7)
    surv_func = aft.predict_survival_function(X.assign(duration=df_pred['avg_gap'], event=y_7), times=[1, 7, 14, 30, 45])
    df_pred['weibull_today'] = 1 - surv_func.loc[1].values
    df_pred['weibull_7'] = 1 - surv_func.loc[7].values
    df_pred['weibull_14'] = 1 - surv_func.loc[14].values
    df_pred['weibull_30'] = 1 - surv_func.loc[30].values
    df_pred['weibull_45'] = 1 - surv_func.loc[45].values

    # Today's forecast
    df_pred['logistic_today'] = train_predict(LogisticRegression, X, y_7)
    df_pred['gbt_today'] = train_gbt(X, y_7)

    # Merge in actual "seen" value for today's date
    latest_date = df['date'].max()
    today_seen = df[df['date'] == latest_date][['indicator', 'seen']].rename(columns={'seen': 'seen_today'})
    df_pred = df_pred.merge(today_seen, on='indicator', how='left')

    return df_pred