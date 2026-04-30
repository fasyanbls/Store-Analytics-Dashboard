#!/usr/bin/env python3
"""
train_revenue_model.py
Train revenue forecast model from dvdrental database.
Optimized for small dataset (5 months).
Output: revenue_forecast_model.pkl
"""

import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import joblib
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ─────────────────────────────────────────────
# DB CONFIG 
# ─────────────────────────────────────────────
from config import DB_CONFIG, MODEL_PATH

MIN_MONTHS = 5 


def get_engine():
    """Create SQLAlchemy engine for pandas compatibility."""
    conn_str = (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    )
    return create_engine(conn_str)


def qry(sql):
    """Execute SQL query and return DataFrame."""
    engine = get_engine()
    df = pd.read_sql(sql, engine)
    engine.dispose()
    return df


def build_features():
    """
    Build rich feature set from dvdrental database.
    Optimized for small dataset — extract maximum signal.
    """
    print("Fetching base monthly aggregations")
    base = qry("""
        SELECT
            DATE_TRUNC('month', r.rental_date)::date AS month,
            COALESCE(SUM(p.amount), 0) AS revenue,
            COUNT(r.rental_id) AS transactions,
            COUNT(DISTINCT r.customer_id) AS unique_customers,
            COUNT(DISTINCT i.film_id) AS unique_films_rented,
            COUNT(DISTINCT cat.category_id) AS categories_active,
            ROUND(AVG(p.amount), 2) AS avg_payment,
            ROUND(AVG(EXTRACT(EPOCH FROM (r.return_date - r.rental_date))/3600), 1) AS avg_rental_hours
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        LEFT JOIN payment p ON p.rental_id = r.rental_id
        LEFT JOIN film_category fc ON i.film_id = fc.film_id
        LEFT JOIN category cat ON fc.category_id = cat.category_id
        WHERE r.rental_date BETWEEN '2005-01-01' AND '2006-12-31'
        GROUP BY 1 ORDER BY 1
    """)

    print("Fetching store distribution")
    store_mix = qry("""
        SELECT
            DATE_TRUNC('month', r.rental_date)::date AS month,
            COUNT(DISTINCT CASE WHEN i.store_id = 1 THEN r.rental_id END)::float / 
                NULLIF(COUNT(r.rental_id), 0) AS store1_ratio,
            COUNT(DISTINCT CASE WHEN i.store_id = 2 THEN r.rental_id END)::float / 
                NULLIF(COUNT(r.rental_id), 0) AS store2_ratio
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        GROUP BY 1 ORDER BY 1
    """)

    print("Fetching customer behavior")
    cust_behavior = qry("""
        SELECT
            DATE_TRUNC('month', r.rental_date)::date AS month,
            COUNT(DISTINCT CASE WHEN cr.cust_rentals > 5 THEN r.customer_id END)::float /
                NULLIF(COUNT(DISTINCT r.customer_id), 0) AS high_value_cust_ratio,
            AVG(cr.cust_rentals) AS avg_cust_rentals
        FROM rental r
        JOIN (
            SELECT customer_id, COUNT(*) AS cust_rentals
            FROM rental
            GROUP BY customer_id
        ) cr ON r.customer_id = cr.customer_id
        GROUP BY 1 ORDER BY 1
    """)

    print("Fetching category dominance")
    cat_dominance = qry("""
        SELECT
            DATE_TRUNC('month', r.rental_date)::date AS month,
            MAX(cat_stats.cat_rentals)::float / NULLIF(SUM(cat_stats.cat_rentals), 0) AS top_category_share
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        JOIN film_category fc ON i.film_id = fc.film_id
        JOIN (
            SELECT 
                fc2.category_id,
                c.name AS category_name,
                COUNT(r2.rental_id) AS cat_rentals
            FROM rental r2
            JOIN inventory i2 ON r2.inventory_id = i2.inventory_id
            JOIN film_category fc2 ON i2.film_id = fc2.film_id
            JOIN category c ON fc2.category_id = c.category_id
            GROUP BY fc2.category_id, c.name
        ) cat_stats ON fc.category_id = cat_stats.category_id
        GROUP BY 1 ORDER BY 1
    """)

    print("Fetching day-of-week patterns")
    dow_pattern = qry("""
        SELECT
            DATE_TRUNC('month', r.rental_date)::date AS month,
            COUNT(DISTINCT CASE WHEN EXTRACT(DOW FROM r.rental_date) IN (0,6) THEN r.rental_id END)::float /
                NULLIF(COUNT(r.rental_id), 0) AS weekend_ratio
        FROM rental r
        GROUP BY 1 ORDER BY 1
    """)

    print("Fetching hourly peak intensity")
    hourly_peak = qry("""
        SELECT
            sub.month,
            MAX(sub.hourly_rentals)::float / NULLIF(AVG(sub.hourly_rentals), 0) AS peak_hour_intensity
        FROM (
            SELECT 
                DATE_TRUNC('month', rental_date)::date AS month,
                EXTRACT(HOUR FROM rental_date) AS hr,
                COUNT(*) AS hourly_rentals
            FROM rental
            GROUP BY 1, 2
        ) sub
        GROUP BY 1 ORDER BY 1
    """)

    print("Fetching inventory turnover")
    inv_turnover = qry("""
        SELECT
            DATE_TRUNC('month', r.rental_date)::date AS month,
            COUNT(DISTINCT r.inventory_id)::float / 
                NULLIF((SELECT COUNT(*) FROM inventory), 0) AS inventory_turnover_ratio
        FROM rental r
        GROUP BY 1 ORDER BY 1
    """)

    print("Fetching payment method diversity")
    pay_diversity = qry("""
        SELECT
            DATE_TRUNC('month', r.rental_date)::date AS month,
            COUNT(DISTINCT p.payment_id)::float / NULLIF(COUNT(DISTINCT r.rental_id), 0) AS payment_per_rental
        FROM rental r
        LEFT JOIN payment p ON p.rental_id = r.rental_id
        GROUP BY 1 ORDER BY 1
    """)

    # Merge all features
    print("Merging features")
    df = base.merge(store_mix, on="month", how="left")
    df = df.merge(cust_behavior, on="month", how="left")
    df = df.merge(cat_dominance, on="month", how="left")
    df = df.merge(dow_pattern, on="month", how="left")
    df = df.merge(hourly_peak, on="month", how="left")
    df = df.merge(inv_turnover, on="month", how="left")
    df = df.merge(pay_diversity, on="month", how="left")
    df = df.fillna(0)

    # Time-based features
    df["month_num"] = range(1, len(df) + 1)
    df["month_of_year"] = pd.to_datetime(df["month"]).dt.month
    df["quarter"] = pd.to_datetime(df["month"]).dt.quarter

    # Cyclical encoding for month
    df["month_sin"] = np.sin(2 * np.pi * df["month_of_year"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month_of_year"] / 12)

    # Lag features (previous month)
    df["revenue_lag1"] = df["revenue"].shift(1).fillna(df["revenue"].iloc[0])
    df["transactions_lag1"] = df["transactions"].shift(1).fillna(df["transactions"].iloc[0])
    df["customers_lag1"] = df["unique_customers"].shift(1).fillna(df["unique_customers"].iloc[0])

    # Rolling statistics (2-month window karena data cuma 5 bulan)
    df["revenue_rolling_mean2"] = df["revenue"].shift(1).rolling(2, min_periods=1).mean().fillna(df["revenue"].iloc[0])
    df["revenue_rolling_std2"] = df["revenue"].shift(1).rolling(2, min_periods=1).std().fillna(0)

    # Growth rates
    df["revenue_growth"] = df["revenue"].pct_change().fillna(0).replace([np.inf, -np.inf], 0)
    df["customer_growth"] = df["unique_customers"].pct_change().fillna(0).replace([np.inf, -np.inf], 0)

    # Revenue per customer/metrics
    df["revenue_per_customer"] = (df["revenue"] / df["unique_customers"].replace(0, 1)).fillna(0)
    df["revenue_per_transaction"] = (df["revenue"] / df["transactions"].replace(0, 1)).fillna(0)

    return df.sort_values("month").reset_index(drop=True)


def train_model(df):
    """
    Train model optimized for very small dataset (5 months).
    Uses Leave-One-Out CV instead of train/test split.
    """
    feature_cols = [
        "month_num", "transactions", "unique_customers", "unique_films_rented",
        "categories_active", "avg_payment", "avg_rental_hours",
        "store1_ratio", "store2_ratio", "high_value_cust_ratio", "avg_cust_rentals",
        "top_category_share", "weekend_ratio", "peak_hour_intensity",
        "inventory_turnover_ratio", "payment_per_rental",
        "month_sin", "month_cos", "quarter",
        "revenue_lag1", "transactions_lag1", "customers_lag1",
        "revenue_rolling_mean2", "revenue_rolling_std2",
        "revenue_growth", "customer_growth",
        "revenue_per_customer", "revenue_per_transaction"
    ]

    X = df[feature_cols].values
    y = df["revenue"].values

    print(f"\nDataset: {len(y)} months (small dataset mode)")
    print("Training Gradient Boosting Regressor")

    # For 5 months: use all data for training
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Conservative hyperparameters for small data
    model = GradientBoostingRegressor(
        n_estimators=50,        # Reduced to prevent overfitting
        max_depth=2,            # Shallow trees
        learning_rate=0.05,     # Slower learning
        min_samples_split=2,
        min_samples_leaf=1,
        subsample=0.8,          # Stochastic boosting
        random_state=42
    )
    model.fit(X_scaled, y)

    # Leave-One-Out Cross-Validation (best for n=5)
    print("Running Leave-One-Out Cross-Validation...")
    loo = LeaveOneOut()
    cv_scores = cross_val_score(model, X_scaled, y, cv=loo, scoring='neg_mean_absolute_error')

    # Fit on all data for final model
    y_pred = model.predict(X_scaled)

    metrics = {
        "train_mae": mean_absolute_error(y, y_pred),
        "train_rmse": np.sqrt(mean_squared_error(y, y_pred)),
        "train_r2": r2_score(y, y_pred),
        "loo_mae": -cv_scores.mean(),
        "loo_mae_std": cv_scores.std(),
        "loo_scores": -cv_scores,  # Individual fold scores
        "n_samples": len(y),
        "feature_importance": dict(zip(feature_cols, model.feature_importances_)),
        "feature_cols": feature_cols,
        "last_row": df.iloc[-1].to_dict(),
    }

    print(f"\n{'='*50}")
    print("MODEL PERFORMANCE (Small Dataset)")
    print(f"{'='*50}")
    print(f"Samples:    {metrics['n_samples']} months")
    print(f"Train MAE:  ${metrics['train_mae']:,.2f}")
    print(f"Train RMSE: ${metrics['train_rmse']:,.2f}")
    print(f"Train R²:   {metrics['train_r2']:.4f}")
    print(f"LOO-CV MAE: ${metrics['loo_mae']:,.2f} (±{metrics['loo_mae_std']:,.2f})")
    print(f"\nLOO-CV Fold Results:")
    for i, score in enumerate(metrics['loo_scores']):
        actual = y[i]
        print(f"  Fold {i+1}: Actual=${actual:,.0f}, MAE=${score:,.2f}")
    print(f"{'='*50}")

    # Feature importance
    print("\nTOP 10 FEATURE IMPORTANCE:")
    fi_sorted = sorted(metrics["feature_importance"].items(), key=lambda x: x[1], reverse=True)[:10]
    for feat, imp in fi_sorted:
        print(f"  {feat:25s}: {imp:.1%}")

    return model, scaler, metrics, df


def save_model(model, scaler, metrics, df):
    """Save model artifact to disk."""
    artifact = {
        "model": model,
        "scaler": scaler,
        "metrics": metrics,
        "feature_cols": metrics["feature_cols"],
        "history": df,
        "version": "2.1-dvdrental-small",
        "created_at": pd.Timestamp.now().isoformat(),
    }

    joblib.dump(artifact, MODEL_PATH)
    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"   Size: {os.path.getsize(MODEL_PATH) / 1024:.1f} KB")


def main():
    print("=" * 60)
    print(" DVDRENTAL REVENUE FORECAST MODEL TRAINER")
    print(" (Optimized for Small Dataset)")
    print("=" * 60)

    df = build_features()
    print(f"\nData range: {df['month'].min()} to {df['month'].max()}")
    print(f"Total months: {len(df)}")

    if len(df) < MIN_MONTHS:
        print(f"❌ ERROR: Need minimum {MIN_MONTHS} months of data! Got {len(df)}.")
        return

    model, scaler, metrics, df = train_model(df)
    save_model(model, scaler, metrics, df)

    print("\nTraining complete! Run Streamlit app to use the model.")


if __name__ == "__main__":
    main()