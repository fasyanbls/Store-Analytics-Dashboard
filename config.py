"""
config.py
─────────
Central configuration: DB credentials, theme palettes, chart styling.
Import P (palette dict) and theme() from here — never duplicate them.

Credentials are loaded from environment variables (via .env file).
Never hardcode secrets in this file.
"""

import os
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# LOAD ENVIRONMENT VARIABLES
# ─────────────────────────────────────────────
load_dotenv()  # Reads from .env file automatically

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "dvdrental"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),          # No fallback — must be set
}

MODEL_PATH = os.getenv("MODEL_PATH", "revenue_forecast_model.pkl")

# Validate critical config on startup
if not DB_CONFIG["password"]:
    raise EnvironmentError(
        "DB_PASSWORD is not set. "
        "Copy .env.example → .env and fill in your credentials."
    )

# ─────────────────────────────────────────────
# THEME PALETTES
# ─────────────────────────────────────────────
PALETTES = {
    "Dark": {
        "bg_grad": "linear-gradient(135deg, #0A1628 0%, #142347 50%, #1B1733 100%)",
        "text": "#EAF0FA",
        "muted": "#9AB0D1",
        "surface": "rgba(255,255,255,0.05)",
        "surface_2": "rgba(255,255,255,0.03)",
        "border": "rgba(249,168,212,0.25)",
        "border_soft": "rgba(249,168,212,0.18)",
        "navy": "#1E3A8A",
        "navy_2": "#2E4FB8",
        "pink": "#F9A8D4",
        "pink_soft": "#FBCFE8",
        "pink_hot": "#EC4899",
        "accent_text": "#F9A8D4",
        "kpi_text": "#FBCFE8",
        "ok": "#86EFAC",
        "sidebar_bg": "#0A1628",
        "scrollbar": "rgba(249,168,212,0.45)",
    },
    "Light": {
        "bg_grad": "linear-gradient(135deg, #FFF5F8 0%, #FFE9F1 50%, #EEF3FF 100%)",
        "text": "#1E2A4A",
        "muted": "#6B7BA8",
        "surface": "rgba(255,255,255,0.75)",
        "surface_2": "rgba(255,255,255,0.55)",
        "border": "rgba(30,58,138,0.22)",
        "border_soft": "rgba(236,72,153,0.20)",
        "navy": "#1E3A8A",
        "navy_2": "#3B5BCC",
        "pink": "#EC4899",
        "pink_soft": "#F9A8D4",
        "pink_hot": "#DB2777",
        "accent_text": "#1E3A8A",
        "kpi_text": "#1E3A8A",
        "ok": "#16A34A",
        "sidebar_bg": "#FFE9F1",
        "scrollbar": "rgba(30,58,138,0.35)",
    },
}


def get_palette() -> dict:
    """Return the active theme palette based on session state."""
    return PALETTES[st.session_state.get("theme_mode", "Dark")]


# ─────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────
def get_chart_globals(P: dict, theme_mode: str) -> dict:
    """Return chart-level constants derived from the active palette."""
    return {
        "DARK_BG":   "rgba(0,0,0,0)",
        "PLOT_BG":   "rgba(255,255,255,0.02)" if theme_mode == "Dark" else "rgba(255,255,255,0.55)",
        "FONT_COL":  P["text"],
        "GRID_COL":  P["border_soft"],
        "COLORS":    [P["navy"], P["pink_hot"], P["pink_soft"], P["navy_2"], P["pink"], "#7DD3FC"],
        "TITLE_COL": P["accent_text"],
    }


def apply_theme(fig: go.Figure, P: dict, theme_mode: str, h=260, t=30, b=8, l=8, r=8) -> go.Figure:
    """Apply consistent styling to any Plotly figure."""
    cg = get_chart_globals(P, theme_mode)
    fig.update_layout(
        paper_bgcolor=cg["DARK_BG"],
        plot_bgcolor=cg["PLOT_BG"],
        font=dict(family="Inter, sans-serif", color=cg["FONT_COL"], size=10),
        title=dict(text="", font=dict(size=11, color=cg["TITLE_COL"])),
        height=h,
        margin=dict(t=t, b=b, l=l, r=r),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
        xaxis_title="",
        yaxis_title="",
    )
    fig.update_xaxes(
        gridcolor=cg["GRID_COL"], linecolor=cg["GRID_COL"],
        tickfont=dict(size=9), title_text=""
    )
    fig.update_yaxes(
        gridcolor=cg["GRID_COL"], linecolor=cg["GRID_COL"],
        tickfont=dict(size=9), title_text=""
    )
    return fig
