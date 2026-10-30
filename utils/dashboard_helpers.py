"""Dashboard utility functions, custom UI components, and chart styling helpers."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Fintech Color Palette
COLOR_PRIMARY = "#1E3A8A"      # Deep Navy
COLOR_SECONDARY = "#0D9488"    # Teal Accent
COLOR_DANGER = "#BE123C"       # Crimson / Default Red
COLOR_SUCCESS = "#059669"      # Emerald / Paid Green
COLOR_WARNING = "#D97706"      # Amber
COLOR_MUTED = "#64748B"        # Slate Muted
COLOR_LIGHT_BG = "#F8FAFC"     # Off-white / light slate
COLOR_BORDER = "#E2E8F0"       # Subtle border


def set_custom_css():
    """Inject custom fintech CSS styling for a modern, crisp UI."""
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    /* Top Header Bar */
    .top-header-banner {{
        background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
        color: white;
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }}
    .top-header-title {{
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
        color: #FFFFFF;
    }}
    .top-header-subtitle {{
        font-size: 14px;
        color: #94A3B8;
        margin-top: 6px;
        margin-bottom: 0;
    }}
    
    /* KPI Metric Cards */
    .kpi-card {{
        background-color: #FFFFFF;
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        margin-bottom: 12px;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(30, 58, 138, 0.07);
        border-color: #CBD5E1;
    }}
    .kpi-label {{
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: {COLOR_MUTED};
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 24px;
        font-weight: 700;
        color: {COLOR_PRIMARY};
        line-height: 1.2;
    }}
    .kpi-subtext {{
        font-size: 12px;
        color: {COLOR_MUTED};
        margin-top: 6px;
    }}
    .badge-success {{
        color: {COLOR_SUCCESS};
        font-weight: 600;
    }}
    .badge-danger {{
        color: {COLOR_DANGER};
        font-weight: 600;
    }}
    .badge-warning {{
        color: {COLOR_WARNING};
        font-weight: 600;
    }}
    
    /* Container Box */
    .content-box {{
        background-color: #FFFFFF;
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
    }}
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: #0F172A;
    }}
    section[data-testid="stSidebar"] * {{
        color: #F1F5F9 !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox label, 
    section[data-testid="stSidebar"] .stMultiSelect label {{
        color: #CBD5E1 !important;
        font-weight: 500;
        font-size: 13px;
    }}
    
    /* Adjust Streamlit default padding */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_kpi(label: str, value: str, subtext: str = "", badge_type: str = "neutral"):
    """Render a modern fintech KPI card with crisp styling."""
    badge_class = {
        "success": "badge-success",
        "danger": "badge-danger",
        "warning": "badge-warning",
        "neutral": ""
    }.get(badge_type, "")

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-subtext {badge_class}">{subtext}</div>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)


def style_plot(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Apply consistent fintech design standards to Plotly figures."""
    fig.update_layout(
        title={
            "text": title,
            "y": 0.95,
            "x": 0.02,
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 16, "family": "Inter", "color": "#0F172A", "weight": "bold"}
        },
        height=height,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"family": "Inter", "color": "#334155", "size": 12},
        margin={"l": 40, "r": 25, "t": 60, "b": 40},
        xaxis=dict(
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            showline=True,
            linecolor="#CBD5E1"
        ),
        yaxis=dict(
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            showline=True,
            linecolor="#CBD5E1"
        ),
        legend=dict(
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor="#0F172A",
            font_size=12,
            font_family="Inter",
            font_color="#FFFFFF"
        )
    )
    return fig
