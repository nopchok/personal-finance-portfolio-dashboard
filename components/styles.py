"""
Minimal Light / Tailwind Aesthetic Theme & CSS Styling for Streamlit Finance Dashboard
Clean, crisp, readable, modern typography (Inter & Prompt) with soft slate borders and Tailwind cards.
"""

import streamlit as st

def apply_tailwind_light_theme():
    custom_css = """
    <style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Prompt:wght@300;400;500;600;700&display=swap');

    /* Global Typography & Light Background */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', 'Prompt', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        letter-spacing: -0.01em;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 3.5rem;
        padding-bottom: 3rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1400px;
    }

    /* Sidebar Clean Light Style (Tailwind slate-50 / white) */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
        box-shadow: 1px 0 3px rgba(0, 0, 0, 0.03);
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.75rem;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
    }

    /* Text Colors */
    h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    p, span, label, div {
        color: #334155;
    }
    .stCaption, small {
        color: #64748B !important;
    }

    /* Clean Tailwind Card */
    .tailwind-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
    }
    .tailwind-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-1px);
    }

    /* Hero / Highlight Banner Card */
    .hero-banner-light {
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%);
        border: 1px solid #E2E8F0;
        border-left: 5px solid #4F46E5;
        border-radius: 16px;
        padding: 1.5rem 1.85rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04);
    }

    /* Metric Header and Value */
    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }
    .metric-val {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.2;
        letter-spacing: -0.03em;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #64748B;
        margin-top: 0.35rem;
        font-weight: 400;
    }

    /* Tailwind Pill Badges */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-green {
        background: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
    }
    .badge-indigo {
        background: #EEF2FF;
        color: #4F46E5;
        border: 1px solid #C7D2FE;
    }
    .badge-amber {
        background: #FFFBEB;
        color: #D97706;
        border: 1px solid #FDE68A;
    }
    .badge-rose {
        background: #FFF1F2;
        color: #E11D48;
        border: 1px solid #FECDD3;
    }
    .badge-cyan {
        background: #F0F9FF;
        color: #0284C7;
        border: 1px solid #BAE6FD;
    }

    /* Tailwind Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #F1F5F9 !important;
        padding: 5px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 8px;
        padding: 0 16px;
        color: #64748B !important;
        font-weight: 500;
        font-size: 0.88rem;
        border: none !important;
        background: transparent;
        transition: all 0.15s ease;
    }
    .stTabs [aria-selected="true"] {
        background: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: -0.01em;
        transition: all 0.15s ease;
        border: 1px solid #E2E8F0;
    }
    .stButton>button[kind="primary"] {
        background: #4F46E5 !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(79, 70, 229, 0.2);
    }
    .stButton>button[kind="primary"]:hover {
        background: #4338CA !important;
        box-shadow: 0 4px 8px rgba(79, 70, 229, 0.3);
        transform: translateY(-1px);
    }
    .stButton>button[kind="secondary"] {
        background: #FFFFFF !important;
        color: #334155 !important;
    }
    .stButton>button[kind="secondary"]:hover {
        background: #F8FAFC !important;
        border-color: #CBD5E1 !important;
    }

    /* Form Inputs & Selects */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12) !important;
    }
    input {
        color: #0F172A !important;
    }

    /* Section Header */
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-left: 4px solid #4F46E5;
        padding-left: 0.65rem;
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4F46E5, #10B981);
        border-radius: 999px;
    }
    .stProgress > div > div > div {
        background-color: #E2E8F0;
        border-radius: 999px;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #E2E8F0 !important;
        font-weight: 600 !important;
        color: #0F172A !important;
    }

    /* Dataframe / Tables */
    .stDataFrame {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        overflow: hidden;
        background-color: #FFFFFF;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def render_metric_card(title: str, value: str, subtext: str = "", badge_text: str = "", badge_type: str = "indigo"):
    badge_html = f'<span class="badge-pill badge-{badge_type}">{badge_text}</span>' if badge_text else ""
    st.markdown(f"""
    <div class="tailwind-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="metric-title">{title}</div>
            {badge_html}
        </div>
        <div class="metric-val">{value}</div>
        <div class="metric-sub">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

def render_hero_banner(title: str, subtitle: str, net_worth: str, monthly_surplus: str, savings_rate: str):
    st.markdown(f"""
    <div class="hero-banner-light">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h1 style="margin: 0; font-size: 1.55rem; font-weight: 800; color: #0F172A; letter-spacing: -0.03em;">{title}</h1>
                <p style="margin: 0.3rem 0 0 0; color: #64748B; font-size: 0.9rem;">{subtitle}</p>
            </div>
            <div style="display: flex; gap: 1.5rem; align-items: center; flex-wrap: wrap;">
                <div style="text-align: right; background: #FFFFFF; padding: 8px 16px; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #64748B; font-weight: 700;">Net Worth (ความมั่งคั่งสุทธิ) <span style="color:#94A3B8; font-weight:400;">[สินทรัพย์ - หนี้]</span></div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: #0284C7;">{net_worth}</div>
                </div>
                <div style="text-align: right; background: #FFFFFF; padding: 8px 16px; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #64748B; font-weight: 700;">เงินออม/ลงทุนต่อเดือน <span style="color:#94A3B8; font-weight:400;">[รายได้ - จ่าย]</span></div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: #059669;">{monthly_surplus} <span style="font-size: 0.85rem; font-weight: 600; color: #10B981;">(ออม {savings_rate})</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
