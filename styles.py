"""
styles.py
"""

import streamlit as st


def inject_css(P: dict) -> None:
    """Inject all custom CSS using the active palette dict P."""
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*, body, .stApp {{ font-family: 'Inter', sans-serif !important; }}
.stApp {{ background: {P["bg_grad"]}; color: {P["text"]}; }}
.block-container {{ padding: 0.6rem 1.2rem 0.5rem 1.2rem !important; max-width: 100% !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* ── Nav bar ── */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.nav-brand) {{
    background: linear-gradient(135deg, {P["surface"]} 0%, {P["surface_2"]} 100%) !important;
    border: 1.5px solid {P["pink_hot"]} !important; border-radius: 18px !important;
    padding: 18px 22px !important; margin-bottom: 14px !important;
    box-shadow: 0 8px 32px -8px color-mix(in oklab, {P["pink_hot"]} 45%, transparent),
        0 2px 10px color-mix(in oklab, {P["navy"]} 25%, transparent),
        inset 0 1px 0 rgba(255,255,255,0.08) !important;
    backdrop-filter: blur(14px); position: relative; overflow: hidden;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.nav-brand)::before {{
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, {P["navy"]}, {P["pink_hot"]}, {P["pink_soft"]});
}}
.nav-brand {{
    font-size: 1.55rem; font-weight: 800;
    background: linear-gradient(90deg, {P["navy"]}, {P["pink_hot"]}, {P["pink_soft"]});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -0.025em; line-height: 1.15;
}}
.nav-subtitle {{ font-size: 0.82rem; color: {P["muted"]}; margin-top: 4px; font-weight: 500; letter-spacing: 0.02em; }}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {P["surface"]} !important; border-radius: 12px !important;
    padding: 4px !important; gap: 2px !important;
    border: 1px solid {P["border"]} !important; margin-bottom: 10px !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 9px !important; color: {P["muted"]} !important;
    font-size: 0.78rem !important; font-weight: 600 !important;
    padding: 6px 14px !important; border: none !important;
    background: transparent !important; letter-spacing: 0.02em; transition: all 0.2s ease !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {P["navy"]}, {P["pink_hot"]}) !important;
    color: #fff !important; box-shadow: 0 2px 10px {P["border"]} !important;
}}

/* ── KPI Cards ── */
.kpi-card {{
    background: {P["surface"]}; border: 1px solid {P["border"]}; border-radius: 14px;
    padding: 14px 16px; text-align: center; backdrop-filter: blur(8px);
    transition: all 0.25s ease; position: relative; overflow: hidden;
}}
.kpi-card::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, {P["navy"]}, {P["pink_hot"]});
}}
.kpi-label {{ font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: {P["muted"]}; margin-bottom: 4px; }}
.kpi-value {{
    font-size: 1.5rem; font-weight: 800;
    background: linear-gradient(135deg, {P["navy"]}, {P["pink_hot"]});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1;
}}
.kpi-delta {{ font-size: 0.68rem; color: {P["ok"]}; margin-top: 2px; font-weight: 600; }}
.kpi-icon {{ font-size: 1.1rem; margin-bottom: 4px; }}

/* ── Section headers ── */
.section-hdr {{
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
    color: {P["accent_text"]}; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;
}}
.section-hdr::after {{ content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, {P["border"]}, transparent); }}

/* ── Insight box ── */
.insight-box {{
    background: linear-gradient(135deg, {P["surface"]}, {P["surface_2"]});
    border-left: 3px solid {P["pink_hot"]}; border-radius: 0 10px 10px 0;
    padding: 12px 16px; font-size: 0.78rem; color: {P["text"]}; line-height: 1.65;
    margin-top: 10px; margin-bottom: 14px; word-wrap: break-word; overflow-wrap: break-word;
}}
.insight-box strong {{ color: {P["pink_hot"]}; }}

/* ── Prediction card ── */
.pred-card {{
    background: linear-gradient(135deg, {P["surface"]}, {P["surface_2"]});
    border: 1px solid {P["border"]}; border-radius: 16px; padding: 18px; text-align: center;
}}
.pred-label {{ font-size: 0.7rem; font-weight: 700; color: {P["muted"]}; text-transform: uppercase; letter-spacing: 0.08em; }}
.pred-val {{ font-size: 2rem; font-weight: 800; color: {P["pink_hot"]}; }}
.pred-sub {{ font-size: 0.72rem; color: {P["navy_2"]}; margin-top: 4px; }}

/* ── Streamlit metric overrides ── */
div[data-testid="metric-container"] {{
    background: {P["surface"]}; border: 1px solid {P["border"]}; border-radius: 12px; padding: 10px 14px;
}}
div[data-testid="metric-container"] label {{ color: {P["muted"]} !important; font-size: 0.68rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }}
div[data-testid="stMetricValue"] {{ color: {P["pink_hot"]} !important; font-size: 1.3rem !important; font-weight: 800 !important; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{ background: {P["sidebar_bg"]}; border-right: 1px solid {P["border"]}; }}
section[data-testid="stSidebar"] * {{ color: {P["text"]} !important; }}

/* ── Inputs ── */
.stSelectbox div[data-baseweb="select"] > div {{ background: {P["surface"]} !important; border-color: {P["border"]} !important; border-radius: 10px !important; color: {P["text"]} !important; }}
.stRadio label {{ font-size: 0.78rem !important; color: {P["text"]} !important; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {P["scrollbar"]}; border-radius: 4px; }}

/* ── DataFrame ── */
.dataframe {{ font-size: 0.72rem !important; }}
div[data-testid="stDataFrame"] {{ background: {P["surface"]}; border: 1px solid {P["border"]}; border-radius: 12px; padding: 4px; overflow: hidden; }}
div[data-testid="stDataFrame"] [role="columnheader"] {{ background: linear-gradient(135deg, {P["surface_2"]}, {P["surface"]}) !important; color: {P["pink_hot"]} !important; font-weight: 700 !important; font-size: 0.7rem !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; border-bottom: 1px solid {P["border"]} !important; }}
div[data-testid="stDataFrame"] [role="gridcell"] {{ color: {P["text"]} !important; border-bottom: 1px solid {P["border"]} !important; background: transparent !important; }}
div[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {{ background: {P["surface_2"]} !important; }}
div[data-testid="stToggle"] label {{ color: {P["muted"]} !important; font-size: 0.72rem !important; font-weight: 700 !important; letter-spacing: 0.05em !important; }}

/* ── Data note banner ── */
.data-note {{
    background: linear-gradient(135deg, rgba(30,58,138,0.15), rgba(236,72,153,0.10));
    border: 1px solid rgba(236,72,153,0.30);
    border-radius: 10px; padding: 8px 14px;
    font-size: 0.68rem; color: {P["muted"]}; line-height: 1.6;
    margin-bottom: 10px;
}}
.data-note strong {{ color: {P["accent_text"]}; }}
</style>
""", unsafe_allow_html=True)
