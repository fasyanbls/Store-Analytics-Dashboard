"""
tabs/tab_inventory.py
─────────────────────
Tab 2 — Inventory & Categories.
"""

import streamlit as st
import plotly.express as px

from config import apply_theme, get_chart_globals
from queries import load_inventory_util


def render(P: dict, theme_mode: str, cat_df):
    cg = get_chart_globals(P, theme_mode)
    inv_df = load_inventory_util()

    st.markdown('<div class="section-hdr">Revenue per Inventory Unit</div>', unsafe_allow_html=True)
    cat_sorted = cat_df.sort_values("rev_per_inv", ascending=True)
    fig = px.bar(cat_sorted, x="rev_per_inv", y="category", orientation="h",
                 text_auto=".1f", color="rev_per_inv",
                 color_continuous_scale=["#1E3A8A", "#F9A8D4"])
    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(textfont_size=9)
    st.plotly_chart(apply_theme(fig, P, theme_mode, h=360, t=10), use_container_width=True)

    c3, c4 = st.columns([2, 3])
    with c3:
        st.markdown('<div class="section-hdr">Category Rental Share</div>', unsafe_allow_html=True)
        fig = px.pie(cat_df, names="category", values="rentals", hole=0.45,
                     color_discrete_sequence=cg["COLORS"])
        fig.update_traces(textinfo="percent", textfont_size=8,
                           marker=dict(line=dict(color="#0A1628", width=1)))
        fig.update_layout(legend=dict(font=dict(size=8)))
        st.plotly_chart(apply_theme(fig, P, theme_mode, h=200, t=10), use_container_width=True)

    with c4:
        st.markdown('<div class="section-hdr">Top 15 Films by Utilization Rate</div>', unsafe_allow_html=True)
        top_util = inv_df.nlargest(15, "util_rate")[["title", "category", "copies", "times_rented", "util_rate", "revenue"]].copy()
        top_util.columns = ["Film", "Category", "Copies", "Rentals", "Util Rate", "Revenue ($)"]
        top_util["Revenue ($)"] = top_util["Revenue ($)"].apply(lambda x: f"${x:,.0f}" if __import__('pandas').notna(x) else "$0")
        st.dataframe(top_util, use_container_width=True, height=200, hide_index=True)

    low_util  = inv_df[inv_df["util_rate"] < 1].shape[0]
    high_util = inv_df[inv_df["util_rate"] >= 5].shape[0]
    st.markdown(f"""
    <div class="insight-box">
      📌 <strong>Inventory Intelligence:</strong> <strong>{high_util}</strong> films achieve ≥5× utilization (top performers).
      <strong>{low_util}</strong> films have &lt;1 rental per copy — repositioning or liquidating these titles
      would free up capital. Focus stocking on high-revenue-per-inventory categories.
    </div>""", unsafe_allow_html=True)
