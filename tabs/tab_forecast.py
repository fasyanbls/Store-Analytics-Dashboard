"""
tabs/tab_forecast.py
────────────────────
Tab 5 — Revenue Forecast & Business Decision Simulator.
Loads the pre-trained model artifact and generates a 3-month outlook,
then lets the user run what-if scenarios.
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import joblib

from config import MODEL_PATH, apply_theme, get_chart_globals


# ─────────────────────────────────────────────
# FORECAST HELPERS
# ─────────────────────────────────────────────
def _generate_future_preds(model, scaler, feature_cols, last_row, rev_history):
    """Roll the model forward 3 months and return (fut_dates, fut_labels, fut_preds)."""
    last_date = pd.to_datetime(last_row["month"])
    last_num  = int(last_row["month_num"])

    fut_dates  = [last_date + pd.DateOffset(months=i) for i in range(1, 4)]
    fut_labels = [d.strftime("%b %Y") for d in fut_dates]

    fut_preds   = []
    current_row = last_row.copy()

    for i in range(1, 4):
        current_row["month_num"]     = last_num + i
        current_row["month_of_year"] = fut_dates[i - 1].month
        current_row["quarter"]       = (fut_dates[i - 1].month - 1) // 3 + 1
        current_row["month_sin"]     = np.sin(2 * np.pi * current_row["month_of_year"] / 12)
        current_row["month_cos"]     = np.cos(2 * np.pi * current_row["month_of_year"] / 12)

        gf = 1 + (0.02 * i)
        current_row["transactions"]        *= gf
        current_row["unique_customers"]    *= gf
        current_row["unique_films_rented"] *= gf

        if i == 1:
            current_row["revenue_lag1"]      = last_row["revenue"]
            current_row["transactions_lag1"] = last_row["transactions"]
            current_row["customers_lag1"]    = last_row["unique_customers"]
        else:
            current_row["revenue_lag1"]      = fut_preds[-1]
            current_row["transactions_lag1"] = current_row["transactions"] / gf
            current_row["customers_lag1"]    = current_row["unique_customers"] / gf

        recent_revs = list(rev_history["revenue"].tail(1).values) + [current_row["revenue_lag1"]]
        current_row["revenue_rolling_mean2"] = np.mean(recent_revs)
        current_row["revenue_rolling_std2"]  = np.std(recent_revs) if len(recent_revs) > 1 else 0

        current_row["revenue_per_customer"]    = current_row["revenue_lag1"] / max(current_row["customers_lag1"], 1)
        current_row["revenue_per_transaction"] = current_row["revenue_lag1"] / max(current_row["transactions_lag1"], 1)
        current_row["revenue_growth"]  = 0.02
        current_row["customer_growth"] = 0.015

        X     = np.array([[current_row.get(c, 0) for c in feature_cols]])
        pred  = max(0, model.predict(scaler.transform(X))[0])
        fut_preds.append(pred)
        current_row["revenue"] = pred

    return fut_dates, fut_labels, np.array(fut_preds)


# ─────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────
def render(P: dict, theme_mode: str):
    cg = get_chart_globals(P, theme_mode)

    # ── Model loading ────────────────────────
    if not os.path.exists(MODEL_PATH):
        st.error("""
        **Forecast Model Not Found**

        Please run the training script first:
        ```bash
        python train_revenue_model.py
        ```
        """)
        st.stop()

    try:
        artifact    = joblib.load(MODEL_PATH)
        model       = artifact["model"]
        scaler      = artifact["scaler"]
        metrics     = artifact["metrics"]
        rev_ml      = artifact["history"]
        feature_cols = artifact["feature_cols"]
    except Exception:
        st.error("Failed to load forecast model. Please contact IT support.")
        st.stop()

    # ── Header ───────────────────────────────
    st.markdown(f"""
    <div style="background:{P['surface']};border:1px solid {P['border']};border-radius:14px;
                padding:18px 22px;margin-bottom:16px;">
      <div style="font-size:1rem;font-weight:800;color:{P['accent_text']};margin-bottom:8px;">
        Revenue Forecast & Business Simulator
      </div>
      <div style="font-size:0.78rem;color:{P['muted']};line-height:1.7;">
        Predict next 3 months revenue and test business scenarios before spending money.
        Based on historical store data (May 2005 – Feb 2006).
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Reliability block ────────────────────
    st.markdown(f"""
    <div style="background:{P['surface']};border:1px solid {P['border']};border-radius:12px;
                padding:14px 18px;margin:12px 0;">
      <div style="font-size:0.72rem;font-weight:700;color:{P['accent_text']};
                  letter-spacing:0.06em;text-transform:uppercase;margin-bottom:10px;">
        How Reliable Is This Forecast?
      </div>
      <div style="font-size:0.74rem;color:{P['text']};line-height:1.8;">
        • <strong>Confidence Level:</strong> {metrics['train_r2']*100:.1f}% — How well past patterns predict future. Higher = better.<br>
        • <strong>History Used:</strong> {metrics['n_samples']} months of store data.<br><br>
        <em style="color:{P['muted']};">💡 Forecasts are estimates. Real results may vary 10-20% due to market conditions.</em>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Generate predictions ─────────────────
    last_row   = metrics["last_row"]
    fut_dates, fut_labels, fut_preds = _generate_future_preds(
        model, scaler, feature_cols, last_row, rev_ml
    )
    fut_x_str  = [d.strftime("%Y-%m") for d in fut_dates]
    hist_x     = [pd.to_datetime(m).strftime("%Y-%m") for m in rev_ml["month"]]
    mae        = metrics["loo_mae"]
    last_actual = float(rev_ml["revenue"].iloc[-1])

    # ── Forecast chart ───────────────────────
    st.markdown(f"""
    <div style="font-size:0.72rem;font-weight:700;color:{P['accent_text']};
                letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;">
      3-Month Revenue Outlook
    </div>
    <div style="font-size:0.7rem;color:{P['muted']};margin-bottom:10px;">
      Solid line = past revenue &nbsp;|&nbsp; Stars = forecast &nbsp;|&nbsp; Shaded area = expected range
    </div>
    """, unsafe_allow_html=True)

    connect_x = [hist_x[-1]] + fut_x_str
    connect_y = [last_actual] + list(fut_preds)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fut_x_str + fut_x_str[::-1],
        y=list(fut_preds + mae) + list((fut_preds - mae)[::-1]),
        fill="toself", fillcolor="rgba(236,72,153,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name=f"Expected Range (±${mae:,.0f})", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=hist_x, y=rev_ml["revenue"], name="Past Revenue",
        mode="lines+markers", line=dict(color=P["navy"], width=2.5),
        marker=dict(size=5, color=P["navy"]),
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
    ))
    zero_df = rev_ml[rev_ml["revenue"] == 0]
    if not zero_df.empty:
        zero_x = [pd.to_datetime(m).strftime("%Y-%m") for m in zero_df["month"]]
        fig.add_trace(go.Scatter(
            x=zero_x, y=zero_df["revenue"], mode="markers",
            name="No Payment Data", marker=dict(size=10, color="#F59E0B", symbol="x"),
            hovertemplate="<b>%{x}</b><br>$0 — Missing payments<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=connect_x, y=connect_y, mode="lines",
        line=dict(color=P["pink_hot"], width=1.5, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=fut_x_str, y=fut_preds, name="Forecast",
        mode="markers+text",
        marker=dict(size=14, symbol="star", color=P["pink_hot"],
                    line=dict(color="white", width=1.5)),
        text=[f"<b>${v:,.0f}</b>" for v in fut_preds],
        textposition="top center", textfont=dict(size=10, color=P["pink_hot"]),
        hovertemplate="<b>%{x}</b><br>Forecast: $%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        legend=dict(font=dict(size=9), orientation="h", y=1.08, x=0),
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor=cg["GRID_COL"], tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor=cg["GRID_COL"], tickfont=dict(size=9),
                   tickprefix="$", tickformat=",.0f"),
    )
    st.plotly_chart(apply_theme(fig, P, theme_mode, h=300, t=20), use_container_width=True)

    # ── Forecast cards ───────────────────────
    st.markdown(f"""
    <div style="font-size:0.7rem;color:{P['muted']};margin-bottom:8px;">
      <strong>What to expect:</strong> Projected revenue numbers with best/worst case range.
    </div>""", unsafe_allow_html=True)

    card_cols = st.columns(3)
    for i, (lbl, pred) in enumerate(zip(fut_labels, fut_preds)):
        base  = last_actual if i == 0 else fut_preds[i - 1]
        delta = (pred - base) / base * 100 if base else 0
        dsym  = "▲" if delta >= 0 else "▼"
        dcol  = P["ok"] if delta >= 0 else "#EF4444"
        low, high = max(0, pred - mae), pred + mae
        card_cols[i].markdown(f"""
        <div class="pred-card">
          <div class="pred-label">{lbl}</div>
          <div class="pred-val">${pred:,.0f}</div>
          <div style="font-size:0.72rem;font-weight:700;color:{dcol};margin:4px 0;">
            {dsym} {abs(delta):.1f}% vs previous
          </div>
          <div style="font-size:0.68rem;color:{P['muted']};margin-top:6px;line-height:1.7;">
            Likely Range:<br><strong style="color:{P['text']};">${low:,.0f} – ${high:,.0f}</strong>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # BUSINESS DECISION SIMULATOR
    # ─────────────────────────────────────────────
    avg_rpt = float((rev_ml["revenue"] / rev_ml["transactions"].replace(0, np.nan)).mean())

    st.markdown(f"""
    <div style="background:{P['surface']};border:1px solid {P['border']};border-radius:14px;
                padding:16px 20px;margin-bottom:16px;">
      <div style="font-size:1rem;font-weight:800;color:{P['accent_text']};margin-bottom:8px;">
        Business Decision Simulator
      </div>
      <div style="font-size:0.78rem;color:{P['muted']};line-height:1.7;">
        <strong>Test your ideas before spending money.</strong> Adjust the values below
        to simulate different scenarios. Current baseline:
        <strong style="color:{P['text']};">${fut_preds[0]:,.0f}</strong>.
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form(key="whatif_form", border=True):
        st.markdown(f"""
        <div style="font-size:0.78rem;font-weight:700;color:{P['text']};margin-bottom:12px;">
          Adjust Your Business Levers
        </div>
        <div style="font-size:0.7rem;color:{P['muted']};margin-bottom:16px;">
          <strong>Tip:</strong> Start with small changes (5-10%) to see impact,
          then experiment with bigger moves.
        </div>
        """, unsafe_allow_html=True)

        wif1, wif2, wif3 = st.columns(3)
        with wif1:
            price_adj = st.number_input("Rental Price Change (%)", min_value=-20, max_value=50,
                                        value=0, step=5,
                                        help="Increase or decrease your average rental price.")
        with wif2:
            promo_pct = st.number_input("Discount/Promo (%)", min_value=0, max_value=50,
                                        value=0, step=5,
                                        help="How much discount are you giving?")
        with wif3:
            new_custs = st.number_input("New Customers Target", min_value=0, max_value=500,
                                        value=0, step=10,
                                        help="How many NEW customers do you plan to attract? Each brings ~1.5 rentals.")

        wif4, wif5 = st.columns(2)
        with wif4:
            inventory_add = st.number_input("New Movie Titles", min_value=0, max_value=100,
                                            value=0, step=5,
                                            help="New films attract more rentals. Each title adds ~$15/month revenue.")
        with wif5:
            staff_add = st.number_input("Extra Staff Hired", min_value=0, max_value=10,
                                        value=0, step=1,
                                        help="More staff = better service = ~2% revenue boost per person.")

        _, btn_col, _ = st.columns([1, 1, 1])
        with btn_col:
            submitted = st.form_submit_button("SEE MY FORECAST", use_container_width=True, type="primary")

    if submitted:
        baseline        = float(fut_preds[0])
        price_impact    = baseline * (price_adj / 100)
        promo_impact    = baseline * (promo_pct / 100) * -1
        newcust_impact  = new_custs * avg_rpt * 1.5
        inventory_impact = inventory_add * 15
        staff_impact    = baseline * (staff_add * 0.02)

        final_sim    = baseline + price_impact + promo_impact + newcust_impact + inventory_impact + staff_impact
        total_delta  = final_sim - baseline
        total_pct    = (total_delta / baseline * 100) if baseline else 0
        sim_col      = P["ok"] if total_delta >= 0 else "#EF4444"
        sim_sym      = "▲" if total_delta >= 0 else "▼"

        st.markdown(f"""
        <div style="background:{P['surface']};border:1px solid {P['border']};border-radius:14px;
                    padding:16px 20px;margin:16px 0;">
          <div style="font-size:0.78rem;font-weight:700;color:{P['accent_text']};
                      text-transform:uppercase;letter-spacing:0.06em;margin-bottom:12px;">
            YOUR SIMULATION RESULT
          </div>
        """, unsafe_allow_html=True)

        r1, r2 = st.columns([2, 3])
        with r1:
            st.markdown(f"""
            <div class="pred-card" style="margin-top:4px;">
              <div class="pred-label">Projected Revenue — Next Month</div>
              <div class="pred-val">${final_sim:,.0f}</div>
              <div style="font-size:0.9rem;font-weight:700;color:{sim_col};margin:6px 0;">
                {sim_sym} {abs(total_pct):.1f}% from baseline
              </div>
              <div style="font-size:0.68rem;color:{P['muted']};line-height:1.9;text-align:left;padding:4px 2px;">
                {'🟢' if price_impact >= 0 else '🔴'} Price change: <strong>${price_impact:+,.0f}</strong><br>
                🔴 Discount cost: <strong>${promo_impact:,.0f}</strong><br>
                🟢 New customers: <strong>{new_custs} people (+${newcust_impact:,.0f})</strong><br>
                {'🟢' if inventory_impact >= 0 else '⚪'} New titles: <strong>{inventory_add} titles (+${inventory_impact:,.0f})</strong><br>
                {'🟢' if staff_impact >= 0 else '⚪'} Extra staff: <strong>{staff_add} people (+${staff_impact:,.0f})</strong>
              </div>
            </div>""", unsafe_allow_html=True)

        with r2:
            if abs(total_pct) < 2:
                msg_icon, msg_title = "⚖️", "Minimal Change Expected"
                msg = (f"Your plan keeps revenue around <strong>${baseline:,.0f}</strong>. "
                       f"For bigger growth, try combining price increase + new titles + more customers.")
            elif total_delta > 0 and total_pct > 15:
                msg_icon, msg_title = "🚀", "Strong Growth Opportunity!"
                msg = (f"This plan could grow revenue by <strong>${total_delta:,.0f}</strong>! "
                       f"Make sure you have enough staff and inventory to handle the extra demand.")
            elif total_delta > 0:
                msg_icon, msg_title = "✅", "Solid Improvement"
                msg = (f"Revenue should increase by <strong>${total_delta:,.0f}</strong>. "
                       + (f"Watch your margins — the {promo_pct}% discount costs ${abs(promo_impact):,.0f}. "
                          f"Make sure you're not giving away too much." if promo_pct > 10
                          else "Good balance of growth and profitability."))
            else:
                msg_icon, msg_title = "⚠️", "Revenue Will Drop"
                msg = (f"This plan loses <strong>${abs(total_delta):,.0f}</strong>. "
                       + (f"The {promo_pct}% discount is too deep without enough new customers." if promo_pct > 15
                          else "Review your pricing — are you undercharging?" if price_adj < 0
                          else "Your costs outweigh gains. Focus on customer acquisition first."))

            st.markdown(f"""
            <div style="background:{P['surface']};border:1px solid {P['border']};border-radius:14px;
                        padding:16px 18px;height:100%;box-sizing:border-box;margin-top:4px;">
              <div style="font-size:1.3rem;margin-bottom:8px;">{msg_icon}</div>
              <div style="font-size:0.78rem;font-weight:700;color:{P['accent_text']};
                          text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">
                {msg_title}
              </div>
              <div style="font-size:0.76rem;color:{P['text']};line-height:1.8;">{msg}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-size:0.7rem;color:{P['muted']};margin-top:12px;line-height:1.6;">
          <strong>Remember:</strong> These are estimates based on past patterns.
          Actual results depend on execution quality, competition, and market conditions.
        </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div style="background:{P['surface_2']};border:1px dashed {P['border']};border-radius:14px;
                    padding:24px;text-align:center;margin-top:8px;">
          <div style="font-size:2rem;margin-bottom:12px;">🎯</div>
          <div style="font-size:0.82rem;color:{P['text']};font-weight:600;margin-bottom:8px;">
            Ready to Test Your Business Ideas?
          </div>
          <div style="font-size:0.74rem;color:{P['muted']};line-height:1.7;">
            Try scenarios like:<br>
            <em>"What if I raise prices 10% and add 50 new customers?"</em><br>
            <em>"What if I run a 20% promo with 20 new movie titles?"</em><br><br>
            Fill the form above and click <strong style="color:{P['pink_hot']};">SEE MY FORECAST</strong>.
          </div>
        </div>
        """, unsafe_allow_html=True)
