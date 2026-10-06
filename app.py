"""
Minimal Light Personal Finance & Portfolio Dashboard
Built with Streamlit, Tailwind Aesthetics, Plotly, SQLite
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize Database
from database import (
    init_db, seed_sample_data_if_empty, 
    get_monthly_profile, get_all_assets, get_all_liabilities, 
    get_all_income_items, get_all_expense_items
)
from components.styles import apply_tailwind_light_theme, render_hero_banner
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

# Initialize DB & Seed Data
init_db()
seed_sample_data_if_empty()

# Apply Minimal Light / Tailwind Theme CSS
apply_tailwind_light_theme()

def main():
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
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem;">
            <div style="background: #EEF2FF; width: 42px; height: 42px; border-radius: 10px; border: 1px solid #C7D2FE; display: flex; align-items: center; justify-content: center; font-size: 1.35rem;">
                💼
            </div>
            <div>
                <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; letter-spacing: -0.02em;">MINIMAL FINANCE</div>
                <div style="font-size: 0.75rem; color: #64748B;">Personal Wealth Dashboard</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        current_date_str = datetime.now().strftime("%B %Y")
        st.caption(f"🗓️ รอบเดือนปัจจุบัน: **{current_date_str}**")

        st.markdown("---")

        menu = st.radio(
            "เมนูหลัก (Navigation)",
            [
                "📊 ภาพรวมรายเดือน (Monthly Estimate)",
                "📈 พอร์ตการลงทุน (Portfolio)",
                "🏛️ ความมั่งคั่ง & อิสรภาพการเงิน (Net Worth & FIRE)",
                "📜 ประวัติ & สำรองข้อมูล (History & Backup)"
            ],
            index=0
        )

        st.markdown("---")
        
        # Sidebar mini-summary card
        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px;">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: #4F46E5; font-weight: 700;">💡 Minimalist Approach</div>
            <div style="font-size: 0.8rem; color: #475569; margin-top: 4px; line-height: 1.45;">
                วางแผนรายเดือนแบบ <b>Estimate ภาพรวม</b> ไม่ต้องเสียเวลากรอกรายจ่ายรายวัน เน้นจัดสรร Asset Allocation และสะสมความมั่งคั่งสู่อิสรภาพทางการเงิน
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Top Hero Banner
    render_hero_banner(
        title="แดชบอร์ดสถานะการเงิน & พอร์ตการลงทุน",
        subtitle="ระบบบริหารจัดการเงินออม ลงทุน และประมาณการความมั่งคั่ง",
        net_worth=f"฿{net_worth:,.0f}",
        monthly_surplus=f"฿{monthly_surplus:,.0f}",
        savings_rate=f"{savings_rate_str}"
    )

    # Main Page Routing
    if "📊 ภาพรวมรายเดือน" in menu:
        render_monthly_planner()
    elif "📈 พอร์ตการลงทุน" in menu:
        render_portfolio()
    elif "🏛️ ความมั่งคั่ง" in menu:
        render_networth_fire()
    elif "📜 ประวัติ & สำรองข้อมูล" in menu:
        render_settings_data()

if __name__ == "__main__":
    main()
