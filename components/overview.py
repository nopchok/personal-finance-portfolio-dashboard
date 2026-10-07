"""
Overview & Financial Health Executive Summary Module.
Provides an all-in-one financial health checkup, diagnostic score, balance sheet snapshot,
cash flow assessment, and personalized actionable guidance.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any
from database import (
    get_monthly_profile, get_all_assets, get_all_liabilities,
    get_all_income_items, get_all_expense_items, safe_float
)
from components.styles import render_metric_card
from components.charts import CHART_LAYOUT_BASE

def render_overview():
    # 1. Fetch current live data
    profile = get_monthly_profile()
    assets = get_all_assets()
    liabilities = get_all_liabilities()
    income_items = get_all_income_items()
    expense_items = get_all_expense_items()

    # Asset classifications
    liquid_assets = [a for a in assets if a.get("asset_type", "investment") == "investment"]
    fixed_assets = [a for a in assets if a.get("asset_type", "investment") == "fixed_asset"]

    total_liquid = sum(a["current_value"] for a in liquid_assets)
    total_fixed = sum(a["current_value"] for a in fixed_assets)
    total_assets = total_liquid + total_fixed

    total_liabilities = sum(l["total_balance"] for l in liabilities)
    total_monthly_debt = sum(l.get("monthly_payment", 0) for l in liabilities)
    net_worth = total_assets - total_liabilities

    # Cash flow calculations
    if income_items:
        total_income = sum(i["estimated_amount"] for i in income_items)
    else:
        total_income = profile.get("salary", 0) + profile.get("bonus_or_other_income", 0) + profile.get("passive_income", 0)

    if expense_items:
        total_expenses = sum(e["estimated_amount"] for e in expense_items)
    else:
        total_expenses = profile.get("fixed_expenses", 0) + profile.get("variable_expense_estimate", 0)

    monthly_surplus = total_income - total_expenses
    savings_rate = (monthly_surplus / total_income * 100) if total_income > 0 else 0

    # Emergency fund calculation (Cash category)
    cash_categories = ["เงินสด / บัญชีออมทรัพย์ (Cash & Savings)", "เงินสด/ฉุกเฉิน (Cash & Emergency)", "เงินฝากออมทรัพย์", "Cash"]
    emergency_cash = sum(
        a["current_value"] for a in liquid_assets 
        if any(c.lower() in str(a.get("category", "")).lower() or c.lower() in str(a.get("name", "")).lower() for c in ["เงินสด", "ออมทรัพย์", "cash", "emergency", "ฝาก"])
    )
    # If no specific cash detected, use 15% of liquid assets as minimum estimate
    emergency_cash = max(emergency_cash, 0)
    emergency_months = (emergency_cash / total_expenses) if total_expenses > 0 else 0
    target_emergency_months = profile.get("emergency_fund_target_months", 6)

    # Debt-to-Income (DTI) ratio
    dti_ratio = (total_monthly_debt / total_income * 100) if total_income > 0 else 0

    # Solvency Ratio (Assets / Liabilities)
    solvency_ratio = (total_assets / total_liabilities * 100) if total_liabilities > 0 else 999.0

    # FIRE Target (4% Rule: 25x Annual Expenses)
    fire_spend = profile.get("fire_target_monthly_spend", total_expenses if total_expenses > 0 else 35000)
    fire_target_today = fire_spend * 12 * 25
    fire_progress = min(1.0, (total_liquid / fire_target_today)) if fire_target_today > 0 else 0

    # -------------------------------------------------------------------------
    # 2. FINANCIAL HEALTH SCORE ALGORITHM (0 - 100)
    # -------------------------------------------------------------------------
    score = 0
    
    # 1) Savings Rate (Max 25 pts)
    if savings_rate >= 30:
        score += 25
    elif savings_rate >= 20:
        score += 20
    elif savings_rate >= 10:
        score += 12
    elif savings_rate > 0:
        score += 5

    # 2) Emergency Fund (Max 25 pts)
    if emergency_months >= target_emergency_months:
        score += 25
    elif emergency_months >= target_emergency_months * 0.5:
        score += 15
    elif emergency_months >= 1:
        score += 8

    # 3) Debt Health (Max 25 pts)
    if total_liabilities == 0:
        score += 25
    elif dti_ratio <= 20:
        score += 22
    elif dti_ratio <= 35:
        score += 15
    elif dti_ratio <= 50:
        score += 8

    # 4) Investment & Net Worth Health (Max 25 pts)
    if net_worth > 0:
        score += 10
    if total_liquid >= total_expenses * 12:
        score += 15
    elif total_liquid >= total_expenses * 6:
        score += 10
    elif total_liquid > 0:
        score += 5

    # Health Grade & Color
    if score >= 85:
        grade = "A (ดีเยี่ยม / มั่นคงสูงมาก)"
        grade_badge = "green"
        grade_desc = "สุขภาพการเงินแข็งแกร่งมาก มีการออมสม่ำเสมอ หนี้สินต่ำ และมีสภาพคล่องพร้อมเติบโต"
    elif score >= 70:
        grade = "B (ดี / มีเสถียรภาพ)"
        grade_badge = "cyan"
        grade_desc = "สถานะการเงินอยู่ในเกณฑ์ดี มีเงินเหลือออม ควบคุมหนี้สินได้ดี ควรเน้นขยายพอร์ตลงทุนเพิ่ม"
    elif score >= 50:
        grade = "C (ปานกลาง / เฝ้าระวัง)"
        grade_badge = "amber"
        grade_desc = "สถานะการเงินพอใช้ ควรเพิ่มสัดส่วนเงินออมฉุกเฉินและลดรายจ่ายฟุ่มเฟือยเพื่อเสริมสภาพคล่อง"
    else:
        grade = "D (ต้องปรับปรุงเร่งด่วน)"
        grade_badge = "rose"
        grade_desc = "มีความเสี่ยงด้านสภาพคล่องหรือภาระหนี้สูง ควรจัดทำงบประมาณฉุกเฉินและลดภาระหนี้เป็นอันดับแรก"

    # -------------------------------------------------------------------------
    # 3. RENDER UI
    # -------------------------------------------------------------------------
    st.markdown('<div class="section-header">🧭 หน้าแรก: สรุปภาพรวม & ตรวจสุขภาพการเงิน (Financial Health Summary)</div>', unsafe_allow_html=True)
    st.caption("แดชบอร์ดสรุปสถานะการเงินทุกมิติแบบองค์รวม ประเมินคะแนนสุขภาพ วิเคราะห์จุดแข็ง และแนวทางบริหารจัดการ")

    # Top Health Score Banner
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%); border-radius: 16px; padding: 1.5rem 1.75rem; color: #FFFFFF; margin-bottom: 1.5rem; box-shadow: 0 10px 25px -5px rgba(67, 56, 202, 0.25);">
        <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem;">
            <div>
                <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #A5B4FC; margin-bottom: 0.25rem;">
                    🩺 FINANCIAL HEALTH CHECKUP SCORE
                </div>
                <div style="font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em; color: #FFFFFF;">
                    เกรด {grade}
                </div>
                <div style="font-size: 0.9rem; color: #E0E7FF; margin-top: 0.35rem; max-width: 680px; line-height: 1.45;">
                    {grade_desc}
                </div>
            </div>
            <div style="background: rgba(255, 255, 255, 0.12); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 14px; padding: 0.75rem 1.5rem; text-align: center; min-width: 140px;">
                <div style="font-size: 0.75rem; color: #C7D2FE; font-weight: 600;">คะแนนสุขภาพรวม</div>
                <div style="font-size: 2.3rem; font-weight: 900; color: #34D399; line-height: 1.1;">{score}<span style="font-size: 1.1rem; color: #A7F3D0;">/100</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Key Dimension Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            title="ความมั่งคั่งสุทธิ (Net Worth)",
            value=f"฿{net_worth:,.0f}",
            subtext=f"สินทรัพย์ ฿{total_assets:,.0f} - หนี้ ฿{total_liabilities:,.0f}",
            badge_text="ทรัพย์สินสุทธิ",
            badge_type="indigo"
        )
    with c2:
        surplus_badge = "green" if monthly_surplus >= 0 else "rose"
        render_metric_card(
            title="เงินเหลือออม/เดือน (Net Cashflow)",
            value=f"฿{monthly_surplus:,.0f}",
            subtext=f"รายได้ ฿{total_income:,.0f} | จ่าย ฿{total_expenses:,.0f}",
            badge_text=f"ออม {savings_rate:.0f}%",
            badge_type=surplus_badge
        )
    with c3:
        debt_badge = "green" if total_liabilities == 0 else ("amber" if dti_ratio <= 35 else "rose")
        debt_status_txt = "ปลอดหนี้ 100%" if total_liabilities == 0 else f"ผ่อน ฿{total_monthly_debt:,.0f}/ด."
        render_metric_card(
            title="ภาระหนี้สินรวม (Liabilities)",
            value=f"฿{total_liabilities:,.0f}",
            subtext=f"ภาระผ่อน/รายได้: {dti_ratio:.1f}%",
            badge_text=debt_status_txt,
            badge_type=debt_badge
        )
    with c4:
        render_metric_card(
            title="เป้าหมาย FIRE Number (4%)",
            value=f"฿{fire_target_today:,.0f}",
            subtext=f"พอร์ตปัจจุบันมี ฿{total_liquid:,.0f}",
            badge_text=f"บรรลุ {fire_progress*100:.1f}%",
            badge_type="cyan"
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 4. TWO-COLUMN SUMMARY VISUALIZATION & DIAGNOSIS
    # -------------------------------------------------------------------------
    col_chart, col_diagnosis = st.columns([1.1, 0.9])

    with col_chart:
        st.markdown("##### 📊 โครงสร้างงบดุล & กระแสเงินสด (Balance Sheet & Flow)")
        
        # Breakdown Bar Chart (Assets vs Debts vs Net Worth)
        fig_bs = go.Figure()
        fig_bs.add_trace(go.Bar(
            name="สินทรัพย์และหนี้สิน",
            x=["พอร์ตลงทุนสภาพคล่อง", "สินทรัพย์ถาวร/บ้าน", "หนี้สินรวม", "ความมั่งคั่งสุทธิ (Net Worth)"],
            y=[total_liquid, total_fixed, total_liabilities, net_worth],
            marker_color=["#4F46E5", "#0284C7", "#E11D48", "#10B981"],
            text=[f"฿{total_liquid:,.0f}", f"฿{total_fixed:,.0f}", f"฿{total_liabilities:,.0f}", f"฿{net_worth:,.0f}"],
            textposition="auto",
            textfont=dict(size=11, family="Plus Jakarta Sans")
        ))
        fig_bs.update_layout(
            **CHART_LAYOUT_BASE,
            height=310,
            showlegend=False,
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickformat=",.0f")
        )
        st.plotly_chart(fig_bs, use_container_width=True)

        # Mini Progress Checklists
        st.markdown("##### 📌 เกณฑ์มาตรฐานสุขภาพการเงิน 4 มิติ")
        
        # 1. Savings Rate
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:2px;">
            <span>💰 <b>อัตราการออม (Savings Rate)</b></span>
            <span><b>{savings_rate:.1f}%</b> (เกณฑ์แนะนำ: > 20%)</span>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(1.0, max(0.0, savings_rate / 40.0)))

        # 2. Emergency Buffer
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-top:8px; margin-bottom:2px;">
            <span>🛡️ <b>เงินสำรองฉุกเฉิน (Emergency Buffer)</b></span>
            <span><b>{emergency_months:.1f} เดือน</b> (เป้าหมาย: {target_emergency_months} เดือน)</span>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(1.0, max(0.0, emergency_months / max(1, target_emergency_months))))

        # 3. Debt-to-Income
        dti_health = max(0.0, 1.0 - (dti_ratio / 50.0))
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-top:8px; margin-bottom:2px;">
            <span>💳 <b>ความปลอดภัยด้านหนี้สิน (DTI Safety)</b></span>
            <span>ภาระผ่อน <b>{dti_ratio:.1f}%</b> ของรายได้ (เกณฑ์ปลอดภัย: < 30%)</span>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(1.0, dti_health))

    with col_diagnosis:
        st.markdown("##### 🧠 บทวิเคราะห์ & คำแนะนำเฉพาะบุคคล (Financial Advice)")

        # Generate smart personalized insights
        strengths = []
        alerts = []
        recommendations = []

        # Analyze Savings
        if savings_rate >= 30:
            strengths.append("อัตราการออมอยู่ในระดับ **ยอดเยี่ยม (> 30%)** ช่วยเร่งเวลาสู่อิสรภาพการเงินได้เร็วมาก")
        elif savings_rate >= 20:
            strengths.append("อัตราการออมอยู่ในเกณฑ์ **ดีตามมาตรฐาน (20-30%)** มีเงินเหลือต่อยอดลงทุนสม่ำเสมอ")
        elif savings_rate > 0:
            alerts.append("อัตราการออมยังค่อนข้างต่ำ (ต่ำกว่า 20%) แนะนำสำรวจลดรายจ่ายผันแปรเพื่อเพิ่มเงินเก็บ")
        else:
            alerts.append("กระแสเงินสดรายเดือน **ติดลบ (รายจ่ายสูงกว่ารายได้)** ต้องตัดรายจ่ายไม่จำเป็นทันที")

        # Analyze Debts
        if total_liabilities == 0:
            strengths.append("คุณอยู่ในสถานะ **ปลอดหนี้ 100%** ไม่มีภาระดอกเบี้ยจ่าย ทำให้มีความคล่องตัวทางการเงินสูงสุด")
        elif dti_ratio <= 30:
            strengths.append(f"ภาระผ่อนหนี้ ({dti_ratio:.1f}%) อยู่ในเกณฑ์ **ปลอดภัย** ไม่กระทบต่อการใช้ชีวิตประจำวัน")
        else:
            alerts.append(f"ภาระผ่อนหนี้ต่อเดือนสูง ({dti_ratio:.1f}% ของรายได้) ควรชะลอการก่อหนี้ใหม่และเน้นโปะหนี้ดอกเบี้ยสูง")

        # Analyze Net Worth & Portfolio
        if total_liquid > 0:
            strengths.append(f"มีพอร์ตลงทุนสภาพคล่อง ฿{total_liquid:,.0f} พร้อมต่อยอดสร้างผลตอบแทนทบต้น")
        else:
            alerts.append("ยังไม่มีสินทรัพย์ลงทุนในระบบ ควรเริ่มจัดสรรเงินออมเข้ากองทุนรวมหรือสินทรัพย์เติบโต")

        if total_fixed > 0:
            strengths.append(f"มีสินทรัพย์ถาวร/อสังหาริมทรัพย์มูลค่า ฿{total_fixed:,.0f} เสริมความมั่งคั่งระยะยาว")

        # Action Recommendations
        if total_liabilities > 0 and dti_ratio > 30:
            recommendations.append("**เร่งปลดล็อกภาระหนี้:** ใช้หลัก Snowball หรือ Avalanche ลดหนี้เพื่อคืนกระแสเงินสดรายเดือน")
        if savings_rate > 0:
            recommendations.append("**กระจายความเสี่ยงพอร์ตลงทุน:** จัดสัดส่วนสินทรัพย์ (Asset Allocation) หุ้น/ตราสารหนี้/กองทุน ตามผลตอบแทนเป้าหมาย")
        recommendations.append(f"**มุ่งสู่ FIRE Number (฿{fire_target_today:,.0f}):** สะสมพอร์ตลงทุนต่อเนื่องเพื่อให้ผลตอบแทนครอบคลุมค่าใช้จ่าย ฿{fire_spend:,.0f}/ด. ในอนาคต")

        # Render Insights Cards
        st.markdown("""
        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 12px 16px; margin-bottom: 12px;">
            <div style="font-weight: 700; color: #166534; font-size: 0.9rem; margin-bottom: 6px;">🟢 จุดแข็งทางการเงินของคุณ (Strengths)</div>
        """, unsafe_allow_html=True)
        for s in strengths:
            st.markdown(f"<div style='font-size: 0.83rem; color: #14532D; margin-bottom: 4px;'>• {s}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if alerts:
            st.markdown("""
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="font-weight: 700; color: #92400E; font-size: 0.9rem; margin-bottom: 6px;">🟡 ข้อควรระวังและปรับปรุง (Areas of Concern)</div>
            """, unsafe_allow_html=True)
            for a in alerts:
                st.markdown(f"<div style='font-size: 0.83rem; color: #78350F; margin-bottom: 4px;'>• {a}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div style="background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 12px; padding: 12px 16px;">
            <div style="font-weight: 700; color: #3730A3; font-size: 0.9rem; margin-bottom: 6px;">🎯 แผนปฏิบัติการที่แนะนำ (Action Plan)</div>
        """, unsafe_allow_html=True)
        for idx, r in enumerate(recommendations, 1):
            st.markdown(f"<div style='font-size: 0.83rem; color: #312E81; margin-bottom: 4px;'><b>{idx}.</b> {r}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 5. QUICK NAVIGATION SHORTCUTS
    # -------------------------------------------------------------------------
    st.divider()
    qc1, qc2, qc3, qc4 = st.columns(4)
    with qc1:
        if st.button("📊 ประมาณการรายเดือน ➔", use_container_width=True, key="btn_nav_monthly"):
            st.session_state["nav_menu"] = "📊 ประมาณการรายเดือน (Monthly Planner)"
            st.rerun()

    with qc2:
        if st.button("📈 พอร์ตการลงทุน ➔", use_container_width=True, key="btn_nav_portfolio"):
            st.session_state["nav_menu"] = "📈 พอร์ตการลงทุน (Portfolio)"
            st.rerun()

    with qc3:
        if st.button("🏛️ ความมั่งคั่ง & FIRE ➔", use_container_width=True, key="btn_nav_fire"):
            st.session_state["nav_menu"] = "🏛️ ความมั่งคั่ง & อิสรภาพการเงิน (Net Worth & FIRE)"
            st.rerun()

    with qc4:
        if st.button("📜 ประวัติ & สำรองข้อมูล ➔", use_container_width=True, key="btn_nav_history"):
            st.session_state["nav_menu"] = "📜 ประวัติ & สำรองข้อมูล (History & Backup)"
            st.rerun()
