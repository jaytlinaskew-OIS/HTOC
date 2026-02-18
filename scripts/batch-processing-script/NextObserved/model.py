import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from lifelines import WeibullAFTFitter

def _as_numeric_df(X: pd.DataFrame) -> pd.DataFrame:
    """Ensure X is numeric (coerce anything weird to NaN)."""
    Xn = X.copy()
    for c in Xn.columns:
        Xn[c] = pd.to_numeric(Xn[c], errors="coerce")
    return Xn


def train_predict_logistic(X: pd.DataFrame, y: pd.Series) -> np.ndarray:
    """
    Logistic regression probability predictions on the same X.
    Returns NaNs if y is single-class or empty after dropping NaNs.
    Robust to NaNs in X via imputation.
    """
    yv = pd.to_numeric(y, errors="coerce")
    mask = yv.notna()
    y_fit = yv.loc[mask].astype(int)

    if y_fit.nunique() < 2:
        return np.full(len(X), np.nan)

    X_fit = _as_numeric_df(X.loc[mask])

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000)),
        ]
    )
    model.fit(X_fit, y_fit)

    X_pred = _as_numeric_df(X)
    return model.predict_proba(X_pred)[:, 1]


def train_predict_gbt(X: pd.DataFrame, y: pd.Series) -> np.ndarray:
    """
    Gradient boosted trees probability predictions on the same X.
    Returns NaNs if y is single-class or empty after dropping NaNs.
    Robust to NaNs in X via median imputation.
    """
    yv = pd.to_numeric(y, errors="coerce")
    mask = yv.notna()
    y_fit = yv.loc[mask].astype(int)

    if y_fit.nunique() < 2:
        return np.full(len(X), np.nan)

    X_fit = _as_numeric_df(X.loc[mask])
    imp = SimpleImputer(strategy="median")
    X_fit_i = imp.fit_transform(X_fit)

    model = GradientBoostingClassifier()
    model.fit(X_fit_i, y_fit)

    X_pred = _as_numeric_df(X)
    X_pred_i = imp.transform(X_pred)
    return model.predict_proba(X_pred_i)[:, 1]


def fit_weibull_aft(X: pd.DataFrame, duration_days: pd.Series, event: pd.Series, duration_scale: float = 100.0):
    """
    Fit a Weibull AFT model.
    - duration_days is scaled down for numerical stability by duration_scale.
    - returns (aft_model, duration_scale)
    """
    Xn = _as_numeric_df(X)

    d = pd.to_numeric(duration_days, errors="coerce")
    e = pd.to_numeric(event, errors="coerce")

    # Only fit on rows with valid duration & event
    fit_mask = d.notna() & e.notna()
    if fit_mask.sum() < 5:
        return None, duration_scale

    aft_df = Xn.loc[fit_mask].copy()
    aft_df["duration"] = (d.loc[fit_mask] / duration_scale).clip(lower=1e-6)
    aft_df["event"] = e.loc[fit_mask].astype(int)

    # Lifelines can't handle NaNs in covariates; impute
    aft_df = aft_df.fillna(aft_df.median(numeric_only=True))

    aft = WeibullAFTFitter(penalizer=0.01)
    # optional: keep your method choice
    aft._scipy_fit_method = "SLSQP"
    aft.fit(aft_df, duration_col="duration", event_col="event", show_progress=False)

    return aft, duration_scale


def predict_weibull_event_prob(
    aft: WeibullAFTFitter,
    X: pd.DataFrame,
    times_days: list,
    duration_scale: float = 100.0
) -> dict:
    """
    Returns dict: {t_days: P(event by t_days)} for each t in times_days.
    If aft is None, returns NaNs.
    """
    out = {t: np.full(len(X), np.nan) for t in times_days}
    if aft is None:
        return out

    Xn = _as_numeric_df(X).copy()
    Xn = Xn.fillna(Xn.median(numeric_only=True))

    times_scaled = [t / duration_scale for t in times_days]
    surv = aft.predict_survival_function(Xn, times=times_scaled)

    # surv index is scaled time; convert back by matching the scaled values
    for t_days, t_scaled in zip(times_days, times_scaled):
        # lifelines stores index exactly as provided, so loc should work
        out[t_days] = 1.0 - surv.loc[t_scaled].to_numpy()

    return out


def exp_event_prob_from_freq30(freq_30: pd.Series, horizon_days: int) -> np.ndarray:
    """
    Memoryless exponential model using freq_30/30 as rate.
    Safe for NaNs (treat missing freq as 0).
    """
    f30 = pd.to_numeric(freq_30, errors="coerce").fillna(0.0)
    rate = (f30 / 30.0).clip(lower=1e-6)
    return 1.0 - np.exp(-rate * float(horizon_days))


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def get_model_outputs(features_df: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """
    Produces per-indicator model probabilities for horizons [1,7,14,30,45].
    Fixes:
      - robust NaN handling via imputers
      - single-class y returns NaNs (explicit)
      - exponential model no longer returns NaNs from missing freq_30
      - Weibull predict uses covariates only and uses scaled time consistently
      - logistic_1 / gbt_1 uses label_1 if available, else falls back to label_7
    """
    df_pred = features_df.copy()

    feature_cols = ["last_seen", "freq_1", "freq_7", "freq_14", "freq_30", "freq_45", "avg_gap", "burstiness"]
    missing = [c for c in feature_cols if c not in df_pred.columns]
    if missing:
        raise KeyError(f"features_df is missing required columns: {missing}")

    X = df_pred[feature_cols]
    y_7 = df_pred["label_7"] if "label_7" in df_pred.columns else None
    y_14 = df_pred["label_14"] if "label_14" in df_pred.columns else None
    y_30 = df_pred["label_30"] if "label_30" in df_pred.columns else None
    y_45 = df_pred["label_45"] if "label_45" in df_pred.columns else None

    # Prefer a true 1-day label if present; otherwise fall back
    y_1 = df_pred["label_1"] if "label_1" in df_pred.columns else y_7

    # ── Logistic
    if y_7 is not None:
        df_pred["logistic_7"] = train_predict_logistic(X, y_7)
    if y_14 is not None:
        df_pred["logistic_14"] = train_predict_logistic(X, y_14)
    if y_30 is not None:
        df_pred["logistic_30"] = train_predict_logistic(X, y_30)
    if y_45 is not None:
        df_pred["logistic_45"] = train_predict_logistic(X, y_45)

    # 1-day logistic (true label_1 if available)
    if y_1 is not None:
        df_pred["logistic_1"] = train_predict_logistic(X, y_1)

    # ── GBT
    if y_7 is not None:
        df_pred["gbt_7"] = train_predict_gbt(X, y_7)
    if y_14 is not None:
        df_pred["gbt_14"] = train_predict_gbt(X, y_14)
    if y_30 is not None:
        df_pred["gbt_30"] = train_predict_gbt(X, y_30)
    if y_45 is not None:
        df_pred["gbt_45"] = train_predict_gbt(X, y_45)

    # 1-day gbt (true label_1 if available)
    if y_1 is not None:
        df_pred["gbt_1"] = train_predict_gbt(X, y_1)

    # ── Exponential (safe for NaNs)
    for h in [1, 7, 14, 30, 45]:
        df_pred[f"exp_{h}"] = exp_event_prob_from_freq30(df_pred["freq_30"], h)

    # ── Weibull AFT
    # Keep your reduced feature set for stability
    X_weibull_cols = ["last_seen", "freq_1", "freq_14", "freq_30", "freq_45", "burstiness"]
    X_weibull = df_pred[X_weibull_cols]

    # Use avg_gap as duration; use y_7 as event label (your original intent)
    if y_7 is not None:
        aft, scale = fit_weibull_aft(X_weibull, df_pred["avg_gap"], y_7, duration_scale=100.0)
        probs = predict_weibull_event_prob(aft, X_weibull, times_days=[1, 7, 14, 30, 45], duration_scale=scale)
        for t in [1, 7, 14, 30, 45]:
            df_pred[f"weibull_{t}"] = probs[t]
    else:
        for t in [1, 7, 14, 30, 45]:
            df_pred[f"weibull_{t}"] = np.full(len(df_pred), np.nan)

    # ── Merge in today's seen value
    if "date" in df.columns and "indicator" in df.columns and "seen" in df.columns:
        latest_date = df["date"].max()
        today_seen = (
            df.loc[df["date"] == latest_date, ["indicator", "seen"]]
              .rename(columns={"seen": "seen_today"})
              .drop_duplicates(subset=["indicator"])
        )
        df_pred = df_pred.merge(today_seen, on="indicator", how="left")

    return df_pred