"""
tabs/tab_customers.py
─────────────────────
Tab 3 — Customers & Geo.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from config import apply_theme, get_chart_globals
from queries import load_top_customers


def render(P: dict, theme_mode: str, geo_df, store_f: str, month_f: str):
    cg = get_chart_globals(P, theme_mode)
    top_custs = load_top_customers(store_f, month_f)

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown('<div class="section-hdr">Global Revenue Distribution</div>', unsafe_allow_html=True)
        fig = px.choropleth(geo_df, locations="country", locationmode="country names",
                            color="revenue", hover_name="country",
                            hover_data={"customers": True, "revenue": ":.2f"},
                            color_continuous_scale=["#0A1628", "#1E3A8A", "#F9A8D4", "#FBCFE8"])
        fig.update_layout(
            paper_bgcolor=cg["DARK_BG"], plot_bgcolor=cg["DARK_BG"],
            title=dict(text=""),
            geo=dict(showframe=False, showcoastlines=True, bgcolor=cg["DARK_BG"],
                     projection_type="natural earth",
                     showland=True, landcolor="rgba(30,27,75,0.6)",
                     showocean=True, oceancolor="rgba(13,13,26,0.8)"),
            coloraxis_colorbar=dict(title="Revenue", title_font=dict(size=9),
                                     tickfont=dict(size=8), len=0.6),
            height=270, margin=dict(t=5, b=0, l=0, r=0),
            font=dict(color=cg["FONT_COL"], size=9),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-hdr">Top 10 Countries by Revenue</div>', unsafe_allow_html=True)
        top_geo = geo_df.nlargest(10, "revenue").sort_values("revenue")
        fig = px.bar(top_geo, x="revenue", y="country", orientation="h", text_auto=".3s",
                     color="revenue", color_continuous_scale=["#1E3A8A", "#F9A8D4"])
        fig.update_layout(coloraxis_showscale=False)
        fig.update_traces(textfont_size=8)
        st.plotly_chart(apply_theme(fig, P, theme_mode, h=270, t=10), use_container_width=True)

    c3, c4 = st.columns([2, 3])
    with c3:
        st.markdown('<div class="section-hdr">Customer Value Segments</div>', unsafe_allow_html=True)
        if not top_custs.empty:
            top_custs_seg = top_custs.copy()
            try:
                top_custs_seg["tier"] = pd.qcut(
                    top_custs_seg["revenue"], q=3,
                    labels=["🥉 Low Value", "🥈 Mid Value", "🥇 High Value"],
                    duplicates="drop"
                )
            except Exception:
                top_custs_seg["tier"] = "🥈 Mid Value"
            tier_agg = top_custs_seg.groupby("tier", observed=True).agg(
                customers=("customer_id", "count"),
                avg_revenue=("revenue", "mean"),
                avg_rentals=("rentals", "mean"),
            ).reset_index()
            fig = px.scatter(tier_agg, x="avg_rentals", y="avg_revenue",
                              size="customers", color="tier",
                              color_discrete_sequence=["#1E3A8A", "#EC4899", "#FBCFE8"],
                              text="tier")
            fig.update_traces(textposition="top center", textfont_size=8, marker=dict(sizemin=10))
            fig.update_layout(showlegend=False)
            st.plotly_chart(apply_theme(fig, P, theme_mode, h=200, t=10), use_container_width=True)

    with c4:
        st.markdown('<div class="section-hdr">Top 15 Customers by Revenue</div>', unsafe_allow_html=True)
        if not top_custs.empty:
            disp = top_custs[["customer_id", "name", "rentals", "revenue", "last_rental"]].copy()
            disp["revenue"] = disp["revenue"].apply(lambda x: f"${x:,.2f}")
            disp.columns = ["ID", "Customer", "Rentals", "Revenue", "Last Rental"]
            st.dataframe(disp, use_container_width=True, height=200, hide_index=True)

    if not geo_df.empty:
        top_country     = geo_df.iloc[0]["country"]
        top_country_rev = geo_df.iloc[0]["revenue"]
        num_countries   = len(geo_df)
        st.markdown(f"""
        <div class="insight-box">
          🌍 <strong>Geographic Reach:</strong> Revenue spans <strong>{num_countries}</strong> countries.
          <strong>{top_country}</strong> is the top market at <strong>${top_country_rev:,.0f}</strong>.
          Geographic data reflects where customers <em>live</em>, while store attribution reflects
          where they <em>rented</em> — these are tracked independently for accuracy.
          Loyalty programs targeting top-spending customers would drive disproportionate revenue impact.
        </div>""", unsafe_allow_html=True)
