"""
tabs/tab_overview.py
────────────────────
Tab 1 — Overview: KPI cards, store comparison, trends, top categories.
"""

import streamlit as st
import plotly.express as px

from config import apply_theme, get_chart_globals


def render(P: dict, theme_mode: str, kpi, store_df, cust_seg_df, cat_df, trend_df, trend_type):
    cg = get_chart_globals(P, theme_mode)

    if not kpi.empty:
        rev_val  = float(kpi["revenue"][0] or 0)
        cust_val = int(kpi["customers"][0] or 0)
        rent_val = int(kpi["rentals"][0] or 0)
        inv_val  = int(kpi["inventory"][0] or 0)
        film_val = int(kpi["films"][0] or 0)
        avg_tx   = rev_val / rent_val if rent_val else 0

        k = st.columns(6)
        kpis = [
            ("💰", "Total Revenue",    f"${rev_val:,.0f}",  "From payments"),
            ("👥", "Active Customers", f"{cust_val:,}",     "Actual renters"),
            ("🎬", "Total Rentals",    f"{rent_val:,}",     "Transactions"),
            ("📦", "Inventory",        f"{inv_val:,}",      "Items in stock"),
            ("🎞️", "Film Titles",      f"{film_val:,}",     "Unique films"),
            ("💳", "Avg Transaction",  f"${avg_tx:.2f}",    "Per rental"),
        ]
        for col, (icon, lbl, val, sub) in zip(k, kpis):
            col.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-icon">{icon}</div>
              <div class="kpi-label">{lbl}</div>
              <div class="kpi-value">{val}</div>
              <div class="kpi-delta">{sub}</div>
            </div>""", unsafe_allow_html=True)

    month_f = st.session_state.get("mf", "All")

    if month_f == "2005-05":
        st.markdown(f"""
        <div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.4);
                    border-radius:10px;padding:10px 14px;font-size:0.74rem;color:#F59E0B;margin:10px 0;">
          ⚠️ <strong>May 2005:</strong> {rent_val:,} rentals recorded, but revenue = $0.
          This is a known data artifact — payment records for this period were not captured.
          Rental volume, patterns, and customer data remain fully valid.
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.markdown('<div class="section-hdr">Store Revenue</div>', unsafe_allow_html=True)
        fig = px.bar(store_df, x="store_id", y="revenue", text_auto=".3s",
                     color="store_id", color_discrete_sequence=["#1E3A8A", "#EC4899"])
        fig.update_traces(textfont_size=9)
        fig.update_layout(showlegend=False)
        st.plotly_chart(apply_theme(fig, P, theme_mode, h=190, t=8), use_container_width=True)

    with c2:
        st.markdown('<div class="section-hdr">Store Rentals</div>', unsafe_allow_html=True)
        fig = px.bar(store_df, x="store_id", y="rentals", text_auto=True,
                     color="store_id", color_discrete_sequence=["#1E3A8A", "#EC4899"])
        fig.update_traces(textfont_size=9)
        fig.update_layout(showlegend=False)
        st.plotly_chart(apply_theme(fig, P, theme_mode, h=190, t=8), use_container_width=True)

    with c3:
        st.markdown(f'<div class="section-hdr">{trend_type} Revenue Trend</div>', unsafe_allow_html=True)
        fig = px.line(trend_df, x="period", y="revenue", color="store",
                      color_discrete_sequence=["#1E3A8A", "#EC4899"], markers=True)
        fig.update_traces(line_width=2, marker_size=4)
        fig.update_layout(legend_title_text="")
        st.plotly_chart(apply_theme(fig, P, theme_mode, h=190, t=8), use_container_width=True)

    c4, c5, c6 = st.columns([1, 2, 1])
    with c4:
        st.markdown('<div class="section-hdr">Customer Distribution by Rental Volume</div>', unsafe_allow_html=True)
        if not cust_seg_df.empty:
            fig = px.pie(cust_seg_df, names="customer_segment", values="total_customers", hole=0.5,
                         color_discrete_sequence=["#1E3A8A", "#2E4FB8", "#EC4899", "#F9A8D4"])
            fig.update_traces(
                textinfo="percent", textfont_size=9,
                marker=dict(line=dict(color="#0A1628", width=2)),
                customdata=cust_seg_df[["total_rentals_by_segment"]].values,
                hovertemplate="<b>%{label}</b><br>Customers: %{value:,}<br>Share: %{percent}<br>Total Rentals: %{customdata[0]:,}<extra></extra>"
            )
            fig.update_layout(showlegend=True, legend=dict(font=dict(size=8), orientation="v"),
                               annotations=[dict(text="Customers", x=0.5, y=0.5,
                                                  font_size=10, font_color=P["text"], showarrow=False)])
            st.plotly_chart(apply_theme(fig, P, theme_mode, h=180, t=8), use_container_width=True)

    with c5:
        st.markdown(f'<div class="section-hdr">{trend_type} Rentals Trend</div>', unsafe_allow_html=True)
        fig = px.area(trend_df, x="period", y="rentals", color="store",
                      color_discrete_sequence=["#1E3A8A", "#EC4899"])
        fig.update_traces(line_width=2)
        fig.update_layout(legend_title_text="")
        st.plotly_chart(apply_theme(fig, P, theme_mode, h=180, t=8), use_container_width=True)

    with c6:
        st.markdown('<div class="section-hdr">Top Categories by Revenue</div>', unsafe_allow_html=True)
        if not cat_df.empty:
            top5 = cat_df.nlargest(5, "revenue")[["category", "revenue"]].sort_values("revenue")
            fig = px.bar(top5, x="revenue", y="category", orientation="h", text_auto=".3s",
                         color="revenue", color_continuous_scale=["#1E3A8A", "#F9A8D4"])
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            fig.update_traces(textfont_size=8)
            st.plotly_chart(apply_theme(fig, P, theme_mode, h=180, t=8), use_container_width=True)

    if not cat_df.empty:
        top_cat     = cat_df.iloc[0]["category"]
        top_rev     = cat_df.iloc[0]["revenue"]
        top_rentals = int(cat_df.iloc[0]["rentals"])

        store_insight = "Store filter active — showing single store data."
        if not store_df.empty and len(store_df) >= 2:
            s1 = store_df[store_df["store_id"] == "Store 1"]
            s2 = store_df[store_df["store_id"] == "Store 2"]
            if not s1.empty and not s2.empty:
                s1r, s2r = float(s1["revenue"].values[0]), float(s2["revenue"].values[0])
                leading = "Store 1" if s1r >= s2r else "Store 2"
                leading_rev = max(s1r, s2r)
                leading_rent = int(s1["rentals"].values[0]) if leading == "Store 1" else int(s2["rentals"].values[0])
                store_insight = (f"<strong>{leading}</strong> leads with "
                                 f"<strong>${leading_rev:,.0f}</strong> revenue and "
                                 f"<strong>{leading_rent:,}</strong> rentals.")

        period_label = f"for {month_f}" if month_f != "All" else "across all months"
        st.markdown(f"""
        <div class="insight-box">
          📌 <strong>Key Insight:</strong> <strong>{top_cat}</strong> leads all categories with
          <strong>${top_rev:,.0f}</strong> revenue from <strong>{top_rentals:,}</strong> rentals {period_label}.
          {store_insight}
          Customers are counted where they <em>rented</em>, not where they registered.
          Use the Month filter above to drill into daily patterns.
        </div>""", unsafe_allow_html=True)
