"""
Minimal Light Personal Finance & Portfolio Dashboard
Built with Streamlit, Tailwind Aesthetics, Plotly, Supabase & Multi-User Isolation
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize Database & Authentication
from database import (
    init_db, clear_db_cache, get_current_user,
    get_monthly_profile, get_all_assets, get_all_liabilities, 
    get_all_income_items, get_all_expense_items
)
from components.styles import apply_tailwind_light_theme, render_hero_banner
from components.auth import render_auth_page, render_sidebar_user_profile
from components.overview import render_overview
from components.monthly_planner import render_monthly_planner
from components.portfolio import render_portfolio
from components.networth_fire import render_networth_fire
from components.settings_data import render_settings_data

# Set Page Config
st.set_page_config(
    page_title="Minimal Finance | สถานะการเงิน & พอร์ตการลงทุน",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB connection check
init_db()

# Apply Minimal Light / Tailwind Theme CSS
apply_tailwind_light_theme()

def main():
    current_user = get_current_user()

    # -------------------------------------------------------------
    # AUTHENTICATION GATE: Require Login if not authenticated
    # -------------------------------------------------------------
    if not current_user:
        render_auth_page()
        return

    # User is authenticated
    display_name = current_user.get("display_name", "ผู้ใช้งาน")

    # Fetch high-level numbers for hero banner
    profile = get_monthly_profile()
    assets = get_all_assets()
    liabilities = get_all_liabilities()
    income_items = get_all_income_items()
    expense_items = get_all_expense_items()

    total_assets = sum(a["current_value"] for a in assets)
    total_liabilities = sum(l["total_balance"] for l in liabilities)
    net_worth = total_assets - total_liabilities

    if income_items:
        total_income = sum(i["estimated_amount"] for i in income_items)
    else:
        total_income = profile.get("salary", 0) + profile.get("bonus_or_other_income", 0) + profile.get("passive_income", 0)
    
    if expense_items:
        total_expenses = sum(e["estimated_amount"] for e in expense_items)
    else:
        total_expenses = profile.get("fixed_expenses", 0) + profile.get("variable_expense_estimate", 0)
        
    monthly_surplus = total_income - total_expenses
    savings_rate_val = (monthly_surplus / total_income * 100) if total_income > 0 else 0
    savings_rate_str = f"{savings_rate_val:.0f}%"

    # Sidebar Navigation & Quick Info
    with st.sidebar:
        st.markdown("""<div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
<div style="background: #EEF2FF; width: 42px; height: 42px; border-radius: 10px; border: 1px solid #C7D2FE; display: flex; align-items: center; justify-content: center; font-size: 1.35rem;">
💼
</div>
<div>
<div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; letter-spacing: -0.02em;">MINIMAL FINANCE</div>
<div style="font-size: 0.75rem; color: #64748B;">Personal Wealth Dashboard</div>
</div>
</div>""", unsafe_allow_html=True)

        # Logged-in User Profile Card & Sign Out
        render_sidebar_user_profile()

        current_date_str = datetime.now().strftime("%B %Y")
        st.caption(f"🗓️ รอบเดือนปัจจุบัน: **{current_date_str}**")

        st.markdown("---")

        MENU_OPTIONS = [
            "🏠 สรุปภาพรวม & ตรวจสุขภาพการเงิน (Overview & Health Check)",
            "📊 ประมาณการรายเดือน (Monthly Planner)",
            "📈 พอร์ตการลงทุน (Portfolio)",
            "🏛️ ความมั่งคั่ง & อิสรภาพการเงิน (Net Worth & FIRE)",
            "📜 ประวัติ & สำรองข้อมูล (History & Backup)"
        ]

        if "redirect_nav" in st.session_state and st.session_state["redirect_nav"] in MENU_OPTIONS:
            st.session_state["nav_menu"] = st.session_state.pop("redirect_nav")

        if "nav_menu" not in st.session_state or st.session_state["nav_menu"] not in MENU_OPTIONS:
            st.session_state["nav_menu"] = MENU_OPTIONS[0]

        menu = st.radio(
            "เมนูหลัก (Navigation)",
            MENU_OPTIONS,
            key="nav_menu"
        )

        st.markdown("---")
        if st.button("🔄 ซิงค์ข้อมูลล่าสุดจาก Cloud", use_container_width=True, key="btn_sidebar_sync"):
            clear_db_cache()
            st.toast("ซิงค์ข้อมูลล่าสุดจาก Supabase สำเร็จ!", icon="☁️")
            st.rerun()
        
        # Sidebar mini-summary card
        st.markdown("""<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; margin-top: 0.5rem;">
<div style="font-size: 0.75rem; text-transform: uppercase; color: #4F46E5; font-weight: 700;">💡 Minimalist Approach</div>
<div style="font-size: 0.8rem; color: #475569; margin-top: 4px; line-height: 1.45;">
วางแผนรายเดือนแบบ <b>Estimate ภาพรวม</b> แยกข้อมูลส่วนบุคคลปลอดภัย เน้นจัดสรร Asset Allocation และสะสมความมั่งคั่งสู่อิสรภาพทางการเงิน
</div>
</div>""", unsafe_allow_html=True)

    # Top Hero Banner
    render_hero_banner(
        title=f"แดชบอร์ดสถานะการเงิน — คุณ{display_name}",
        subtitle="ระบบบริหารจัดการเงินออม ลงทุน และประมาณการความมั่งคั่งส่วนบุคคล",
        net_worth=f"฿{net_worth:,.0f}",
        monthly_surplus=f"฿{monthly_surplus:,.0f}",
        savings_rate=f"{savings_rate_str}"
    )

    # Main Page Routing
    if "🏠 สรุปภาพรวม" in menu:
        render_overview()
    elif "📊 ประมาณการรายเดือน" in menu:
        render_monthly_planner()
    elif "📈 พอร์ตการลงทุน" in menu:
        render_portfolio()
    elif "🏛️ ความมั่งคั่ง" in menu:
        render_networth_fire()
    elif "📜 ประวัติ & สำรองข้อมูล" in menu:
        render_settings_data()

if __name__ == "__main__":
    main()
