"""
app.py
──────
Entry point. Thin orchestrator — no business logic here.

Run with:
    streamlit run app.py
"""

import streamlit as st

# ─────────────────────────────────────────────
# PAGE CONFIG 
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Store Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# IMPORTS 
# ─────────────────────────────────────────────
from config  import get_palette
from styles  import inject_css
from queries import (
    get_months,
    load_kpi,
    load_store_compare,
    load_customer_segment_dist,
    load_trend,
    load_category,
    load_geo,
)
import tabs.tab_overview  as tab_overview
import tabs.tab_inventory as tab_inventory
import tabs.tab_customers as tab_customers
import tabs.tab_patterns  as tab_patterns
import tabs.tab_forecast     as tab_forecast
import tabs.tab_ai_insights  as tab_ai_insights

# ─────────────────────────────────────────────
# THEME 
# ─────────────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"

P          = get_palette()
theme_mode = st.session_state.theme_mode
inject_css(P)

# ─────────────────────────────────────────────
# TOP NAV
# ─────────────────────────────────────────────
with st.container(border=True):
    _nav_l, _nav_r = st.columns([5, 1.2], vertical_alignment="center")
    with _nav_l:
        st.markdown("""
        <div style="padding:2px 6px;">
          <div class="nav-brand">🎬 Store Analytics Dashboard</div>
          <div class="nav-subtitle">DVD Rental Database · Rental-Based Analytics</div>
        </div>
        """, unsafe_allow_html=True)
    with _nav_r:
        _is_dark   = st.toggle("🌙 Dark Mode", value=(theme_mode == "Dark"),
                               key="theme_toggle", help="Toggle Dark / Light mode")
        _new_mode  = "Dark" if _is_dark else "Light"
        if _new_mode != st.session_state.theme_mode:
            st.session_state.theme_mode = _new_mode
            st.rerun()

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GLOBAL FILTERS
# ─────────────────────────────────────────────
fc1, fc2, fc3 = st.columns([1, 1, 5])
with fc1:
    store_f = st.selectbox("🏪 Store", ["All", "1", "2"],
                           label_visibility="collapsed", key="sf")
with fc2:
    month_f = st.selectbox("📅 Month", get_months(),
                           label_visibility="collapsed", key="mf")
with fc3:
    if month_f == "2005-05":
        st.markdown("""<div style="padding-top:6px;font-size:0.68rem;color:#F59E0B;">
            ⚠️ May 2005: Rental activity available but revenue = $0 (payments recorded post-period).
        </div>""", unsafe_allow_html=True)
    else: 
        store_label = f"Store {store_f}" if store_f != "All" else "All Stores"
        month_label = month_f if month_f != "All" else "All Months (May 2005 – Feb 2006)"
        st.markdown(f"""<div style="padding-top:6px;font-size:0.68rem;color:{P['muted']};">
            {store_label} &nbsp;|&nbsp; {month_label}
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADS  (shared across multiple tabs)
# ─────────────────────────────────────────────
kpi         = load_kpi(store_f, month_f)
store_df    = load_store_compare(month_f)
store_df["store_id"] = "Store " + store_df["store_id"]
cust_seg_df = load_customer_segment_dist(store_f, month_f)
trend_df, trend_type = load_trend(store_f, month_f)
trend_df["store"] = "Store " + trend_df["store"]
cat_df      = load_category(store_f, month_f)
geo_df      = load_geo(store_f, month_f)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "📦 Inventory & Categories",
    "👥 Customers & Geo",
    "⏱️ Rental Patterns",
    "🤖 ML Predictions",
    "💬 AI Insights",
])

with tab1:
    tab_overview.render(P, theme_mode, kpi, store_df, cust_seg_df, cat_df, trend_df, trend_type)

with tab2:
    tab_inventory.render(P, theme_mode, cat_df)

with tab3:
    tab_customers.render(P, theme_mode, geo_df, store_f, month_f)

with tab4:
    tab_patterns.render(P, theme_mode, store_f, month_f)

with tab5:
    tab_forecast.render(P, theme_mode)

with tab6:
    tab_ai_insights.render(P, theme_mode, kpi, store_df, cust_seg_df, cat_df, trend_df, geo_df, store_f, month_f)
