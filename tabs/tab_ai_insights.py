"""
tabs/tab_ai_insights.py
───────────────────────
Tab 6 — AI Business Insights Chatbot.
Uses Groq (free, fast LLM API) to provide intelligent, data-driven insights
and recommendations based on the dashboard's live data.
"""

import streamlit as st
import os

from config import get_chart_globals


# ─────────────────────────────────────────────
# DATA CONTEXT BUILDER
# ─────────────────────────────────────────────
def _build_data_context(kpi, store_df, cust_seg_df, cat_df, trend_df, geo_df, store_f, month_f) -> str:
    """Build a rich text summary of all dashboard data for the AI context."""
    lines = []
    lines.append("=== STORE ANALYTICS DATA SNAPSHOT ===")
    lines.append(f"Active Filters: Store={store_f}, Month={month_f}")
    lines.append("")

    # KPI Summary
    if not kpi.empty:
        rev  = float(kpi["revenue"].iloc[0] or 0)
        cust = int(kpi["customers"].iloc[0] or 0)
        rent = int(kpi["rentals"].iloc[0] or 0)
        inv  = int(kpi["inventory"].iloc[0] or 0)
        films = int(kpi["films"].iloc[0] or 0)
        avg_tx = rev / rent if rent else 0
        lines.append("--- KEY PERFORMANCE INDICATORS ---")
        lines.append(f"Total Revenue: ${rev:,.2f}")
        lines.append(f"Active Customers: {cust:,}")
        lines.append(f"Total Rentals: {rent:,}")
        lines.append(f"Inventory Items: {inv:,}")
        lines.append(f"Unique Film Titles: {films:,}")
        lines.append(f"Avg Transaction Value: ${avg_tx:.2f}")
        lines.append("")

    # Store Comparison
    if not store_df.empty:
        lines.append("--- STORE COMPARISON ---")
        for _, row in store_df.iterrows():
            lines.append(
                f"  {row['store_id']}: Revenue=${float(row['revenue']):,.2f}, "
                f"Rentals={int(row['rentals']):,}, Customers={int(row['customers']):,}"
            )
        lines.append("")

    # Customer Segments
    if not cust_seg_df.empty:
        lines.append("--- CUSTOMER SEGMENTS ---")
        for _, row in cust_seg_df.iterrows():
            lines.append(
                f"  {row['customer_segment']}: "
                f"{int(row['total_customers']):,} customers, "
                f"{int(row['total_rentals_by_segment']):,} rentals"
            )
        lines.append("")

    # Category Performance (top 10)
    if not cat_df.empty:
        lines.append("--- CATEGORY PERFORMANCE (Top 10) ---")
        for _, row in cat_df.head(10).iterrows():
            lines.append(
                f"  {row['category']}: Revenue=${float(row['revenue']):,.2f}, "
                f"Rentals={int(row['rentals']):,}, Inventory={int(row['inventory'])}, "
                f"Rev/Inv=${float(row['rev_per_inv']):.2f}"
            )
        lines.append("")

    # Trend Summary
    if not trend_df.empty:
        lines.append("--- REVENUE TREND ---")
        trend_summary = trend_df.groupby("store").agg(
            total_revenue=("revenue", "sum"),
            total_rentals=("rentals", "sum"),
            periods=("period", "count"),
        ).reset_index()
        for _, row in trend_summary.iterrows():
            lines.append(
                f"  {row['store']}: Total Rev=${float(row['total_revenue']):,.2f}, "
                f"Rentals={int(row['total_rentals']):,} over {int(row['periods'])} periods"
            )
        lines.append("")

    # Geographic Data (top 10)
    if not geo_df.empty:
        lines.append("--- TOP 10 COUNTRIES BY REVENUE ---")
        for _, row in geo_df.head(10).iterrows():
            lines.append(
                f"  {row['country']}: Revenue=${float(row['revenue']):,.2f}, "
                f"Customers={int(row['customers']):,}"
            )
        lines.append(f"  Total countries with customers: {len(geo_df)}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert DVD rental store business analyst AI assistant embedded 
in a Store Analytics Dashboard. You have access to real-time store performance data.

Your role:
1. Answer questions about store performance using the provided data
2. Provide actionable business recommendations
3. Identify trends, patterns, and opportunities
4. Compare store performance and suggest improvements
5. Help with strategic decisions (pricing, inventory, marketing)

Rules:
- Always ground your answers in the actual data provided
- Use specific numbers and percentages from the data
- Be concise but thorough — use bullet points for clarity
- When making recommendations, explain the reasoning
- If asked about data you don't have, say so clearly
- Format monetary values as $X,XXX.XX
- Use markdown formatting for readability (bold, bullets, headers)
- Be proactive — if you notice something interesting in the data, mention it
- Respond in the same language the user uses (English or Indonesian)

Data context about this business:
- This is a DVD rental business with 2 stores
- Data covers May 2005 to February 2006
- May 2005 has rental activity but $0 revenue (payment data not captured for that period)
- Revenue comes from rental payments
- Customer location is based on where they live, store attribution is based on where they rented
"""

# ─────────────────────────────────────────────
# AVAILABLE MODELS
# ─────────────────────────────────────────────
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]


# ─────────────────────────────────────────────
# QUICK PROMPTS
# ─────────────────────────────────────────────
QUICK_PROMPTS = [
    ("📊 Performance Summary", "Give me a comprehensive performance summary of the store data. Highlight key strengths and areas of concern."),
    ("🏆 Top Recommendations", "Based on the data, what are your top 5 actionable business recommendations to increase revenue?"),
    ("📦 Inventory Strategy", "Analyze the category performance and suggest an optimal inventory strategy. Which categories should we invest more in and which should we reduce?"),
    ("👥 Customer Insights", "Analyze the customer segments and geographic distribution. What customer retention and acquisition strategies do you recommend?"),
    ("📈 Growth Opportunities", "Identify the biggest growth opportunities based on the data. Where is the untapped potential?"),
    ("⚖️ Store Comparison", "Compare the two stores in detail. Which store is performing better and why? What can the weaker store learn?"),
]


# ─────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────
def render(P: dict, theme_mode: str, kpi, store_df, cust_seg_df, cat_df, trend_df, geo_df, store_f, month_f):
    cg = get_chart_globals(P, theme_mode)

    # ── Check API key ─────────────────────────
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    # Also check session state for temp key
    if not api_key and "groq_api_key_temp" in st.session_state:
        api_key = st.session_state["groq_api_key_temp"]

    if not api_key:
        st.markdown(f"""
        <div style="background:{P['surface']};border:1px solid {P['border']};border-radius:14px;
                    padding:24px;text-align:center;margin-bottom:16px;">
          <div style="font-size:2.5rem;margin-bottom:16px;">🤖</div>
          <div style="font-size:1.1rem;font-weight:800;color:{P['accent_text']};margin-bottom:12px;">
            AI Business Insights — Setup Required
          </div>
          <div style="font-size:0.82rem;color:{P['text']};line-height:1.8;max-width:600px;margin:0 auto;">
            To enable AI-powered insights, you need a free <strong>Groq API key</strong>:
          </div>
          <div style="margin:16px auto;max-width:500px;text-align:left;">
            <div style="background:{P['surface_2']};border:1px solid {P['border']};border-radius:10px;
                        padding:14px 20px;margin-bottom:12px;">
              <div style="font-size:0.72rem;font-weight:700;color:{P['muted']};margin-bottom:8px;">
                STEP 1: Get your free API key
              </div>
              <div style="font-size:0.78rem;color:{P['text']};line-height:1.7;">
                Go to <a href="https://console.groq.com/keys" target="_blank"
                   style="color:{P['pink_hot']};font-weight:600;">console.groq.com/keys</a>
                and create a free key.
              </div>
            </div>
            <div style="background:{P['surface_2']};border:1px solid {P['border']};border-radius:10px;
                        padding:14px 20px;">
              <div style="font-size:0.72rem;font-weight:700;color:{P['muted']};margin-bottom:8px;">
                STEP 2: Add to .env file
              </div>
              <code style="font-size:0.78rem;color:{P['pink_hot']};">GROQ_API_KEY=gsk_your_key_here</code>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Allow manual entry as fallback
        st.markdown(f"""
        <div style="font-size:0.72rem;font-weight:700;color:{P['accent_text']};
                    letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">
          Or paste your API key below (session only)
        </div>
        """, unsafe_allow_html=True)

        temp_key = st.text_input(
            "Groq API Key", type="password",
            placeholder="gsk_...",
            key="temp_groq_key_input",
            label_visibility="collapsed"
        )
        if temp_key:
            st.session_state["groq_api_key_temp"] = temp_key.strip()
            st.rerun()

        return

    # ── Initialize Groq client ────────────────
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize Groq: {e}")
        return

    # ── Build data context ────────────────────
    data_context = _build_data_context(
        kpi, store_df, cust_seg_df, cat_df, trend_df, geo_df, store_f, month_f
    )

    # ── Header with model selector ─────────────
    hdr_left, hdr_right = st.columns([4, 1.5])
    with hdr_left:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, {P['surface']} 0%, {P['surface_2']} 100%);
                    border:1px solid {P['border']};border-radius:14px;
                    padding:18px 22px;position:relative;overflow:hidden;">
          <div style="position:absolute;top:0;left:0;right:0;height:3px;
                      background:linear-gradient(90deg, {P['navy']}, {P['pink_hot']}, {P['pink_soft']});"></div>
          <div style="display:flex;align-items:center;gap:12px;">
            <div style="font-size:1.8rem;">🤖</div>
            <div>
              <div style="font-size:1rem;font-weight:800;color:{P['accent_text']};line-height:1.2;">
                AI Business Insights
              </div>
              <div style="font-size:0.74rem;color:{P['muted']};margin-top:4px;line-height:1.5;">
                Powered by Groq · Ask anything about your store data
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with hdr_right:
        selected_model = st.selectbox(
            "Model", GROQ_MODELS,
            index=0, key="ai_model_select",
            help="llama-3.3-70b = smartest, llama-3.1-8b = fastest"
        )

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ── Quick prompts ─────────────────────────
    st.markdown(f"""
    <div style="font-size:0.7rem;font-weight:700;color:{P['accent_text']};
                letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;">
      Quick Analysis
    </div>
    """, unsafe_allow_html=True)

    qp_cols = st.columns(3)
    for i, (label, prompt) in enumerate(QUICK_PROMPTS):
        col = qp_cols[i % 3]
        if col.button(label, key=f"qp_{i}", use_container_width=True):
            st.session_state["ai_pending_prompt"] = prompt

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── Initialize chat history ───────────────
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # ── Handle pending quick prompt BEFORE rendering ──
    pending_prompt = None
    if "ai_pending_prompt" in st.session_state:
        pending_prompt = st.session_state.pop("ai_pending_prompt")

    # ── Process new message (quick prompt or from previous input) ──
    if pending_prompt:
        st.session_state.ai_chat_history.append({"role": "user", "content": pending_prompt})
        _generate_response(client, data_context, st.session_state.ai_chat_history, selected_model)

    # ── Chat display area ─────────────────────
    chat_container = st.container(height=420, border=True)

    with chat_container:
        if not st.session_state.ai_chat_history:
            st.markdown(f"""
            <div style="text-align:center;padding:60px 20px;">
              <div style="font-size:2.5rem;margin-bottom:16px;">💡</div>
              <div style="font-size:0.88rem;font-weight:600;color:{P['text']};margin-bottom:8px;">
                Ready to analyze your store data!
              </div>
              <div style="font-size:0.76rem;color:{P['muted']};line-height:1.7;max-width:450px;margin:0 auto;">
                Ask me anything about your revenue, customers, inventory, or trends.
                I can also provide strategic recommendations and identify growth opportunities.
                <br><br>Try a <strong style="color:{P['pink_hot']};">Quick Analysis</strong> button above,
                or type your question below.
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.ai_chat_history:
                avatar = "🧑‍💼" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

    # ── Bottom controls ───────────────────────
    col_input, col_clear = st.columns([6, 1])

    with col_clear:
        if st.button("🗑️ Clear", key="clear_chat", use_container_width=True):
            st.session_state.ai_chat_history = []
            st.rerun()

    # ── Chat input ────────────────────────────
    user_input = st.chat_input(
        "Ask about your store data... (e.g., 'Which category should I invest in?')"
    )

    if user_input:
        st.session_state.ai_chat_history.append({"role": "user", "content": user_input})
        _generate_response(client, data_context, st.session_state.ai_chat_history, selected_model)
        st.rerun()

    # ── Data context info ─────────────────────
    with st.expander("Data context sent to AI", expanded=False):
        st.caption(f"Filters: Store={store_f}, Month={month_f}")
        st.code(data_context, language="text")


# ─────────────────────────────────────────────
# RESPONSE GENERATOR (Groq)
# ─────────────────────────────────────────────
def _generate_response(client, data_context: str, chat_history: list, model_name: str):
    """Generate an AI response via Groq and append it to chat_history."""
    # Build messages in OpenAI-compatible format (Groq uses this)
    messages = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nCURRENT DATA:\n{data_context}"
        }
    ]

    # Add conversation history
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Try selected model, fallback to others
    models_to_try = [model_name] + [m for m in GROQ_MODELS if m != model_name]

    for model in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            ai_response = response.choices[0].message.content
            if model != model_name:
                ai_response = f"*[Auto-switched to `{model}`]*\n\n" + ai_response
            chat_history.append({"role": "assistant", "content": ai_response})
            return
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                continue
            else:
                chat_history.append({"role": "assistant", "content":
                    f"⚠️ Error: {error_str}\n\nPlease check your API key and try again."
                })
                return

    # All models failed
    chat_history.append({"role": "assistant", "content":
        "⚠️ **Rate limit reached** — All models are busy.\n\n"
        "Please wait a moment and try again."
    })
