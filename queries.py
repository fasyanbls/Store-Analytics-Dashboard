"""
queries.py
──────────
All database query functions.
Every function is cached with st.cache_data and accepts only hashable
arguments (strings/ints) so Streamlit can cache them correctly.

Filter conventions:
  - Store filter → i.store_id  (actual transaction store, not registration)
  - Time filter  → r.rental_date
  - Revenue      → SUM(p.amount) via JOIN on rental, NO payment_date filter
"""

import streamlit as st
import pandas as pd
import psycopg2

from config import DB_CONFIG


# ─────────────────────────────────────────────
# BASE CONNECTOR
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def qry(sql: str) -> pd.DataFrame:
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ─────────────────────────────────────────────
# FILTER CLAUSE BUILDERS
# ─────────────────────────────────────────────
def _store_clause(sf: str, alias: str = "i") -> str:
    return f"AND {alias}.store_id = {int(sf)}" if sf != "All" else ""


def _month_clause(mf: str, alias: str = "r") -> str:
    return f"AND TO_CHAR({alias}.rental_date, 'YYYY-MM') = '{mf}'" if mf != "All" else ""


# ─────────────────────────────────────────────
# GLOBAL FILTER DATA
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_months() -> list:
    df = qry("SELECT DISTINCT TO_CHAR(rental_date,'YYYY-MM') AS m FROM rental ORDER BY m")
    return ["All"] + df["m"].tolist()


# ─────────────────────────────────────────────
# KPI BLOCK
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_kpi(sf: str, mf: str) -> pd.DataFrame:
    sc = _store_clause(sf)
    mc = _month_clause(mf)
    return qry(f"""
        SELECT
          (SELECT COUNT(DISTINCT r2.customer_id)
           FROM rental r2
           JOIN inventory i2 ON r2.inventory_id = i2.inventory_id
           WHERE 1=1
             {f"AND i2.store_id = {int(sf)}" if sf != "All" else ""}
             {f"AND TO_CHAR(r2.rental_date, 'YYYY-MM') = '{mf}'" if mf != "All" else ""}
          ) AS customers,

          (SELECT COUNT(DISTINCT r.rental_id)
           FROM rental r
           JOIN inventory i ON r.inventory_id = i.inventory_id
           WHERE 1=1 {sc} {mc}
          ) AS rentals,

          (SELECT COALESCE(SUM(p.amount), 0)
           FROM payment p
           JOIN rental r ON p.rental_id = r.rental_id
           JOIN inventory i ON r.inventory_id = i.inventory_id
           WHERE 1=1 {sc} {mc}
          ) AS revenue,

          (SELECT COUNT(DISTINCT i.inventory_id)
           FROM inventory i
           WHERE 1=1 {sc}
          ) AS inventory,

          (SELECT COUNT(DISTINCT i.film_id)
           FROM inventory i
           WHERE 1=1 {sc}
          ) AS films
    """)


# ─────────────────────────────────────────────
# STORE COMPARISON
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_store_compare(mf: str) -> pd.DataFrame:
    mc = _month_clause(mf)
    return qry(f"""
        SELECT
            i.store_id::text AS store_id,
            COALESCE(SUM(p.amount), 0) AS revenue,
            COUNT(DISTINCT r.rental_id) AS rentals,
            COUNT(DISTINCT r.customer_id) AS customers
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        LEFT JOIN payment p ON p.rental_id = r.rental_id
        WHERE 1=1 {mc}
        GROUP BY i.store_id
        ORDER BY i.store_id
    """)


# ─────────────────────────────────────────────
# CUSTOMER SEGMENT DISTRIBUTION
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_customer_segment_dist(sf: str, mf: str) -> pd.DataFrame:
    sc = _store_clause(sf)
    mc = _month_clause(mf)
    return qry(f"""
        SELECT
            CASE
                WHEN rental_count > 40 THEN '1. Elite (40+ Rentals)'
                WHEN rental_count BETWEEN 30 AND 40 THEN '2. Frequent (30-40)'
                WHEN rental_count BETWEEN 20 AND 29 THEN '3. Regular (20-29)'
                ELSE '4. Casual (<20)'
            END AS customer_segment,
            COUNT(customer_id) AS total_customers,
            SUM(rental_count) AS total_rentals_by_segment
        FROM (
            SELECT r.customer_id, COUNT(r.rental_id) AS rental_count
            FROM rental r
            JOIN inventory i ON r.inventory_id = i.inventory_id
            WHERE 1=1 {sc} {mc}
            GROUP BY r.customer_id
        ) AS cs
        GROUP BY customer_segment
        ORDER BY customer_segment
    """)


# ─────────────────────────────────────────────
# REVENUE & RENTAL TREND
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_trend(sf: str, mf: str) -> tuple[pd.DataFrame, str]:
    """Returns (dataframe, trend_type) where trend_type is 'Monthly' or 'Daily'."""
    sc = _store_clause(sf)
    if mf == "All":
        df = qry(f"""
            SELECT
                DATE_TRUNC('month', r.rental_date) AS period,
                i.store_id::text AS store,
                COUNT(r.rental_id) AS rentals,
                COALESCE(SUM(p.amount), 0) AS revenue
            FROM rental r
            JOIN inventory i ON r.inventory_id = i.inventory_id
            LEFT JOIN payment p ON r.rental_id = p.rental_id
            WHERE 1=1 {sc}
            GROUP BY 1, 2 ORDER BY 1, 2
        """)
        return df, "Monthly"
    else:
        df = qry(f"""
            SELECT
                r.rental_date::date AS period,
                i.store_id::text AS store,
                COUNT(r.rental_id) AS rentals,
                COALESCE(SUM(p.amount), 0) AS revenue
            FROM rental r
            JOIN inventory i ON r.inventory_id = i.inventory_id
            LEFT JOIN payment p ON r.rental_id = p.rental_id
            WHERE TO_CHAR(r.rental_date, 'YYYY-MM') = '{mf}' {sc}
            GROUP BY 1, 2 ORDER BY 1, 2
        """)
        return df, "Daily"


# ─────────────────────────────────────────────
# CATEGORY ANALYTICS
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_category(sf: str, mf: str) -> pd.DataFrame:
    sc = _store_clause(sf)
    mc = _month_clause(mf)
    return qry(f"""
        SELECT
            cat.name AS category,
            COUNT(DISTINCT i.inventory_id) AS inventory,
            COALESCE(SUM(p.amount), 0) AS revenue,
            COUNT(r.rental_id) AS rentals,
            ROUND(COALESCE(SUM(p.amount), 0) / NULLIF(COUNT(DISTINCT i.inventory_id), 0), 2) AS rev_per_inv
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        JOIN film_category fc ON i.film_id = fc.film_id
        JOIN category cat ON fc.category_id = cat.category_id
        LEFT JOIN payment p ON p.rental_id = r.rental_id
        WHERE 1=1 {sc} {mc}
        GROUP BY cat.name
        ORDER BY revenue DESC
    """)


# ─────────────────────────────────────────────
# GEOGRAPHIC REVENUE
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_geo(sf: str, mf: str) -> pd.DataFrame:
    sc = _store_clause(sf)
    mc = _month_clause(mf)
    return qry(f"""
        SELECT
            co.country,
            COUNT(DISTINCT r.customer_id) AS customers,
            COALESCE(SUM(p.amount), 0) AS revenue,
            COUNT(r.rental_id) AS rentals
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        JOIN customer cu ON r.customer_id = cu.customer_id
        LEFT JOIN payment p ON p.rental_id = r.rental_id
        JOIN address a ON cu.address_id = a.address_id
        JOIN city ci ON a.city_id = ci.city_id
        JOIN country co ON ci.country_id = co.country_id
        WHERE co.country IS NOT NULL {sc} {mc}
        GROUP BY co.country
        ORDER BY revenue DESC
    """)


# ─────────────────────────────────────────────
# HOURLY / DOW PATTERNS
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_hourly(sf: str, mf: str) -> pd.DataFrame:
    sc = _store_clause(sf)
    mc = _month_clause(mf)
    return qry(f"""
        SELECT
            EXTRACT(HOUR FROM r.rental_date) AS hour,
            EXTRACT(DOW FROM r.rental_date) AS dow,
            COUNT(r.rental_id) AS rentals,
            COALESCE(SUM(p.amount), 0) AS revenue
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        LEFT JOIN payment p ON p.rental_id = r.rental_id
        WHERE 1=1 {sc} {mc}
        GROUP BY 1, 2 ORDER BY 1, 2
    """)


# ─────────────────────────────────────────────
# RENTAL DURATION BY DAY OF WEEK
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_rental_duration(sf: str, mf: str) -> pd.DataFrame:
    sc = _store_clause(sf)
    mc = _month_clause(mf)
    return qry(f"""
        SELECT
            EXTRACT(DOW FROM r.rental_date) AS dow,
            ROUND(AVG(EXTRACT(EPOCH FROM (r.return_date - r.rental_date)) / 3600)::numeric, 1) AS avg_hours,
            COUNT(r.rental_id) AS rentals
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        WHERE r.return_date IS NOT NULL {sc} {mc}
        GROUP BY 1 ORDER BY 1
    """)


# ─────────────────────────────────────────────
# TOP CUSTOMERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_top_customers(sf: str, mf: str) -> pd.DataFrame:
    sc = _store_clause(sf)
    mc = _month_clause(mf)
    return qry(f"""
        SELECT
            r.customer_id,
            cu.first_name || ' ' || cu.last_name AS name,
            COUNT(r.rental_id) AS rentals,
            COALESCE(SUM(p.amount), 0) AS revenue,
            MAX(r.rental_date)::date AS last_rental
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        JOIN customer cu ON r.customer_id = cu.customer_id
        LEFT JOIN payment p ON r.rental_id = p.rental_id
        WHERE 1=1 {sc} {mc}
        GROUP BY r.customer_id, cu.first_name, cu.last_name
        ORDER BY revenue DESC
        LIMIT 15
    """)


# ─────────────────────────────────────────────
# INVENTORY UTILISATION (global, no filter)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_inventory_util() -> pd.DataFrame:
    return qry("""
        SELECT
            f.title,
            cat.name AS category,
            COUNT(DISTINCT i.inventory_id) AS copies,
            COUNT(r.rental_id) AS times_rented,
            ROUND(COUNT(r.rental_id)::numeric / NULLIF(COUNT(DISTINCT i.inventory_id), 0), 1) AS util_rate,
            COALESCE(SUM(p.amount), 0) AS revenue
        FROM film f
        JOIN inventory i ON f.film_id = i.film_id
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category cat ON fc.category_id = cat.category_id
        LEFT JOIN rental r ON i.inventory_id = r.inventory_id
        LEFT JOIN payment p ON r.rental_id = p.rental_id
        GROUP BY f.film_id, f.title, cat.name
        ORDER BY util_rate DESC
        LIMIT 100
    """)
