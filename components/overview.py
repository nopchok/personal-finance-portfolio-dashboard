"""
Overview & Financial Health Executive Summary Module.
Provides an all-in-one financial health checkup, diagnostic score, balance sheet snapshot,
cash flow assessment, detailed retirement & FIRE projections, and personalized actionable guidance.
"""

from datetime import datetime
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

    curr_y = datetime.now().year

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
    emergency_cash = sum(
        a["current_value"] for a in liquid_assets 
        if any(c.lower() in str(a.get("category", "")).lower() or c.lower() in str(a.get("name", "")).lower() for c in ["เงินสด", "ออมทรัพย์", "cash", "emergency", "ฝาก"])
    )
    emergency_cash = max(emergency_cash, 0)
    emergency_months = (emergency_cash / total_expenses) if total_expenses > 0 else 0
    target_emergency_months = profile.get("emergency_fund_target_months", 6)

    # Debt-to-Income (DTI) ratio
    dti_ratio = (total_monthly_debt / total_income * 100) if total_income > 0 else 0

    # Solvency Ratio (Assets / Liabilities)
    solvency_ratio = (total_assets / total_liabilities * 100) if total_liabilities > 0 else 999.0

    # -------------------------------------------------------------------------
    # RETIREMENT & FIRE PARAMETERS & PROJECTIONS
    # -------------------------------------------------------------------------
    default_birth_year = int(profile.get("fire_birth_year", curr_y - int(profile.get("fire_current_age", 29))))
    current_age = max(1, curr_y - default_birth_year)
    target_retire_age = max(current_age + 1, int(profile.get("fire_target_age", 50)))
    years_to_retire = max(1, target_retire_age - current_age)

    fire_spend_today = profile.get("fire_target_monthly_spend", total_expenses if total_expenses > 0 else 35000)
    expected_roi = float(profile.get("fire_expected_return", 7.0))
    inflation_rate = float(profile.get("fire_inflation_rate", 2.5))

    # 4% Rule calculations
    fire_target_today = fire_spend_today * 12 * 25
    inflation_factor = ((1 + inflation_rate / 100) ** years_to_retire)
    fire_target_future = fire_target_today * inflation_factor
    future_monthly_spend = fire_spend_today * inflation_factor

    # Compound growth simulation to retirement age
    r_monthly = (expected_roi / 100) / 12
    n_months = years_to_retire * 12
    monthly_investment = max(0.0, monthly_surplus)

    # Future value of current capital
    fv_capital_only = total_liquid * ((1 + r_monthly) ** n_months) if r_monthly > 0 else total_liquid
    # Future value of monthly contributions
    if r_monthly > 0:
        fv_contributions = monthly_investment * (((1 + r_monthly) ** n_months - 1) / r_monthly)
    else:
        fv_contributions = monthly_investment * n_months

    projected_portfolio_total = fv_capital_only + fv_contributions

    # Progress & Readiness
    fire_progress_today = min(1.0, (total_liquid / fire_target_today)) if fire_target_today > 0 else 0
    readiness_future_pct = (projected_portfolio_total / fire_target_future * 100) if fire_target_future > 0 else 0

    # Required Monthly Investment to hit 100% of future target
    funding_gap = max(0.0, fire_target_future - fv_capital_only)
    if r_monthly > 0 and funding_gap > 0:
        required_monthly_dca = funding_gap * r_monthly / (((1 + r_monthly) ** n_months) - 1)
    elif funding_gap > 0:
        required_monthly_dca = funding_gap / n_months
    else:
        required_monthly_dca = 0.0

    # Estimated FIRE Age simulation (year-by-year)
    estimated_fire_age = None
    max_sim_years = max(40, years_to_retire + 15)
    for y in range(1, max_sim_years + 1):
        m = y * 12
        if r_monthly > 0:
            val_y = total_liquid * ((1 + r_monthly) ** m) + monthly_investment * (((1 + r_monthly) ** m - 1) / r_monthly)
        else:
            val_y = total_liquid + (monthly_investment * m)
        target_y = fire_target_today * ((1 + inflation_rate / 100) ** y)
        if val_y >= target_y:
            estimated_fire_age = current_age + y
            break

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
        grade_desc = "สุขภาพการเงินแข็งแกร่งมาก มีการออมสม่ำเสมอ หนี้สินต่ำ และมีสภาพคล่องพร้อมเติบโตสู่อิสรภาพการเงิน"
    elif score >= 70:
        grade = "B (ดี / มีเสถียรภาพ)"
        grade_desc = "สถานะการเงินอยู่ในเกณฑ์ดี มีเงินเหลือออม ควบคุมหนี้สินได้ดี ควรเน้นขยายพอร์ตลงทุนเพิ่ม"
    elif score >= 50:
        grade = "C (ปานกลาง / เฝ้าระวัง)"
        grade_desc = "สถานะการเงินพอใช้ ควรเพิ่มสัดส่วนเงินออมฉุกเฉินและลดรายจ่ายฟุ่มเฟือยเพื่อเสริมสภาพคล่อง"
    else:
        grade = "D (ต้องปรับปรุงเร่งด่วน)"
        grade_desc = "มีความเสี่ยงด้านสภาพคล่องหรือภาระหนี้สูง ควรจัดทำงบประมาณฉุกเฉินและลดภาระหนี้เป็นอันดับแรก"

    # -------------------------------------------------------------------------
    # 3. RENDER UI
    # -------------------------------------------------------------------------
    st.markdown('<div class="section-header">🧭 หน้าแรก: สรุปภาพรวม & ตรวจสุขภาพการเงิน (Financial Health Summary)</div>', unsafe_allow_html=True)
    st.caption("แดชบอร์ดสรุปสถานะการเงินทุกมิติแบบองค์รวม ประเมินคะแนนสุขภาพ วิเคราะห์จุดแข็ง และแนวทางบริหารจัดการ")

    # Top Health Score Banner
    st.markdown(f"""<div style="background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%); border-radius: 16px; padding: 1.5rem 1.75rem; color: #FFFFFF; margin-bottom: 1.5rem; box-shadow: 0 10px 25px -5px rgba(67, 56, 202, 0.25);">
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
</div>""", unsafe_allow_html=True)

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
            badge_text=f"บรรลุ {fire_progress_today*100:.1f}%",
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
        st.markdown(f"""<div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:2px;">
<span>💰 <b>อัตราการออม (Savings Rate)</b></span>
<span><b>{savings_rate:.1f}%</b> (เกณฑ์แนะนำ: > 20%)</span>
</div>""", unsafe_allow_html=True)
        st.progress(min(1.0, max(0.0, savings_rate / 40.0)))

        # 2. Emergency Buffer
        st.markdown(f"""<div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-top:8px; margin-bottom:2px;">
<span>🛡️ <b>เงินสำรองฉุกเฉิน (Emergency Buffer)</b></span>
<span><b>{emergency_months:.1f} เดือน</b> (เป้าหมาย: {target_emergency_months} เดือน)</span>
</div>""", unsafe_allow_html=True)
        st.progress(min(1.0, max(0.0, emergency_months / max(1, target_emergency_months))))

        # 3. Debt-to-Income
        dti_health = max(0.0, 1.0 - (dti_ratio / 50.0))
        st.markdown(f"""<div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-top:8px; margin-bottom:2px;">
<span>💳 <b>ความปลอดภัยด้านหนี้สิน (DTI Safety)</b></span>
<span>ภาระผ่อน <b>{dti_ratio:.1f}%</b> ของรายได้ (เกณฑ์ปลอดภัย: < 30%)</span>
</div>""", unsafe_allow_html=True)
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
        recommendations.append(f"**มุ่งสู่ FIRE Number (฿{fire_target_today:,.0f}):** สะสมพอร์ตลงทุนต่อเนื่องเพื่อให้ผลตอบแทนครอบคลุมค่าใช้จ่าย ฿{fire_spend_today:,.0f}/ด. ในอนาคต")

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
    # 5. DETAILED RETIREMENT & FIRE PROJECTIONS (การประมาณการ การเกษียณ)
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    st.markdown("### 🎯 รายละเอียดการประมาณการเกษียณอายุ (Retirement & FIRE Projections)")
    st.caption(f"แบบจำลองการสะสมความมั่งคั่งและพลังดอกเบี้ยทบต้น (Compounding Interest) อ้างอิงกฎ 4% Rule สำหรับเป้าหมายเกษียณอายุ {target_retire_age} ปี")

    # Milestone Banner Card with Timeline Insights
    if estimated_fire_age:
        if estimated_fire_age <= target_retire_age:
            pace_text = f"🚀 ด้วยอัตราการออมและพอร์ตปัจจุบัน คาดว่าจะบรรลุเป้าหมายอิสรภาพการเงินที่อายุ <b>{estimated_fire_age} ปี</b> (เร็วกว่าเป้าหมาย {target_retire_age - estimated_fire_age} ปี)"
            pace_bg = "background: #F0FDF4; color: #14532D; border: 1px solid #86EFAC; border-left: 5px solid #16A34A;"
            badge_bg = "background: #DCFCE7; color: #166534; border: 1px solid #BBF7D0;"
        else:
            pace_text = f"⏳ ด้วยอัตราการออมปัจจุบัน คาดว่าจะบรรลุเป้าหมายอิสรภาพการเงินที่อายุ <b>{estimated_fire_age} ปี</b> (ช้ากว่าเป้าหมาย {estimated_fire_age - target_retire_age} ปี แนะนำเพิ่มเงินลงทุน ฿{required_monthly_dca:,.0f}/ด.)"
            pace_bg = "background: #FFFBEB; color: #78350F; border: 1px solid #FDE68A; border-left: 5px solid #D97706;"
            badge_bg = "background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A;"
    else:
        pace_text = f"💡 แนะนำเริ่มจัดสรรเงินออมลงทุนเดือนละ ฿{required_monthly_dca:,.0f} เพื่อให้พอร์ตเติบโตทันเป้าหมายเกษียณอายุ {target_retire_age} ปี"
        pace_bg = "background: #EEF2FF; color: #312E81; border: 1px solid #C7D2FE; border-left: 5px solid #4F46E5;"
        badge_bg = "background: #E0E7FF; color: #3730A3; border: 1px solid #C7D2FE;"

    st.markdown(f"""
    <div style="{pace_bg} border-radius: 12px; padding: 1rem 1.35rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem;">
            <div style="font-size: 0.92rem; line-height: 1.55; flex: 1; min-width: 280px;">
                {pace_text}
            </div>
            <div style="{badge_bg} font-size: 0.8rem; font-weight: 700; padding: 5px 12px; border-radius: 8px; white-space: nowrap;">
                🎂 อายุปัจจุบัน {current_age} ปี ➔ เกษียณ {target_retire_age} ปี ({years_to_retire} ปีข้างหน้า)
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Detailed Retirement Metrics Cards
    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1:
        render_metric_card(
            title="เป้าหมาย ณ วันเกษียณ (รวมเงินเฟ้อ)",
            value=f"฿{fire_target_future:,.0f}",
            subtext=f"มูลค่าวันนี้ ฿{fire_target_today:,.0f} (เงินเฟ้อ {inflation_rate}%/ปี)",
            badge_text="Future Target",
            badge_type="indigo"
        )
    with rc2:
        render_metric_card(
            title=f"คาดการณ์พอร์ตเมื่ออายุ {target_retire_age} ปี",
            value=f"฿{projected_portfolio_total:,.0f}",
            subtext=f"เงินต้นเดิม + ออม ฿{monthly_investment:,.0f}/ด. (ผลตอบแทน {expected_roi}%/ปี)",
            badge_text=f"ครอบคลุม {readiness_future_pct:.0f}%",
            badge_type="green" if readiness_future_pct >= 100 else ("amber" if readiness_future_pct >= 60 else "rose")
        )
    with rc3:
        render_metric_card(
            title="ค่าใช้จ่าย ณ วันเกษียณ (ปรับเงินเฟ้อ)",
            value=f"฿{future_monthly_spend:,.0f}/ด.",
            subtext=f"เทียบเท่า ฿{fire_spend_today:,.0f}/ด. ในปัจจุบัน",
            badge_text=f"ปีละ ฿{future_monthly_spend*12:,.0f}",
            badge_type="cyan"
        )
    with rc4:
        diff_dca = required_monthly_dca - monthly_investment
        if diff_dca <= 0:
            dca_sub = f"ยอดเยี่ยม! ออมเกินเป้า ฿{abs(diff_dca):,.0f}/ด."
            dca_badge = "green"
            dca_badge_txt = "อยู่ในแผน 100%"
        else:
            dca_sub = f"ขาดอีก ฿{diff_dca:,.0f}/ด. เพื่อให้ถึงเป้าหมาย"
            dca_badge = "amber"
            dca_badge_txt = "แนะนำเพิ่มเงินออม"
        render_metric_card(
            title="เงินลงทุนรายเดือนที่แนะนำ (DCA Target)",
            value=f"฿{required_monthly_dca:,.0f}/ด.",
            subtext=dca_sub,
            badge_text=dca_badge_txt,
            badge_type=dca_badge
        )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Two column: Compounding Chart & Milestone Timeline Table
    col_ret_chart, col_ret_table = st.columns([1.15, 0.85])

    with col_ret_chart:
        st.markdown("##### 📈 เส้นทางเติบโตของพอร์ต & เป้าหมายเกษียณ (Growth Simulation)")
        
        sim_years_range = max(years_to_retire + 5, 25)
        sim_months = sim_years_range * 12
        x_years = [i / 12 for i in range(sim_months + 1)]
        x_ages = [current_age + (i / 12) for i in range(sim_months + 1)]

        val_total_proj = []
        val_capital_only = []
        val_target_inflation = []

        for m in range(sim_months + 1):
            if r_monthly > 0:
                fv_cap = total_liquid * ((1 + r_monthly) ** m)
                fv_dca = monthly_investment * (((1 + r_monthly) ** m - 1) / r_monthly)
            else:
                fv_cap = total_liquid
                fv_dca = monthly_investment * m
            val_total_proj.append(fv_cap + fv_dca)
            val_capital_only.append(fv_cap)
            
            y_curr = m / 12
            val_target_inflation.append(fire_target_today * ((1 + inflation_rate / 100) ** y_curr))

        fig_proj = go.Figure()

        # Target Line (Inflation Adjusted)
        fig_proj.add_trace(go.Scatter(
            x=x_ages,
            y=val_target_inflation,
            mode="lines",
            name="เป้าหมาย FIRE ปรับเงินเฟ้อ",
            line=dict(color="#E11D48", width=2, dash="dash"),
            hovertemplate="อายุ %{x:.0f} ปี: เป้าหมาย ฿%{y:,.0f}<extra></extra>"
        ))

        # Capital Only Growth
        fig_proj.add_trace(go.Scatter(
            x=x_ages,
            y=val_capital_only,
            mode="lines",
            name=f"พอร์ตเติบโตจากเงินต้นเดิม ({expected_roi}%)",
            line=dict(color="#94A3B8", width=1.5, dash="dot"),
            hovertemplate="อายุ %{x:.0f} ปี: พอร์ตเดิม ฿%{y:,.0f}<extra></extra>"
        ))

        # Total Projected Portfolio (Capital + DCA)
        fig_proj.add_trace(go.Scatter(
            x=x_ages,
            y=val_total_proj,
            mode="lines",
            name=f"พอร์ตสะสมรวมเงินออม (+฿{monthly_investment:,.0f}/ด.)",
            line=dict(color="#4F46E5", width=3),
            fill="tozeroy",
            fillcolor="rgba(79, 70, 229, 0.08)",
            hovertemplate="อายุ %{x:.0f} ปี: พอร์ตรวม ฿%{y:,.0f}<extra></extra>"
        ))

        # Retirement Age marker line
        fig_proj.add_vline(
            x=target_retire_age,
            line_dash="dot",
            line_color="#10B981",
            annotation_text=f"อายุเกษียณเป้าหมาย ({target_retire_age} ปี)",
            annotation_position="top right",
            annotation_font=dict(color="#10B981", size=11)
        )

        fig_proj.update_layout(
            **CHART_LAYOUT_BASE,
            xaxis=dict(
                title="อายุ (ปี)",
                showgrid=True,
                gridcolor="#F1F5F9",
                color="#64748B"
            ),
            yaxis=dict(
                title="มูลค่าพอร์ตสะสม (บาท)",
                showgrid=True,
                gridcolor="#F1F5F9",
                tickprefix="฿",
                tickformat=",.0f",
                color="#64748B"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.28,
                xanchor="center",
                x=0.5,
                font=dict(size=11, color="#64748B")
            ),
            height=340
        )
        st.plotly_chart(fig_proj, use_container_width=True)

    with col_ret_table:
        st.markdown("##### 🗓️ ไทม์ไลน์เปรียบเทียบตามช่วงอายุ (Milestones)")

        # Create 5-year step milestone dataframe
        milestones = []
        milestone_ages = list(range(current_age, target_retire_age + 11, 5))
        if target_retire_age not in milestone_ages:
            milestone_ages.append(target_retire_age)
        milestone_ages = sorted(list(set(milestone_ages)))

        for age in milestone_ages:
            y_diff = age - current_age
            m_diff = y_diff * 12
            if y_diff == 0:
                port_val = total_liquid
                target_val = fire_target_today
            else:
                if r_monthly > 0:
                    port_val = total_liquid * ((1 + r_monthly) ** m_diff) + monthly_investment * (((1 + r_monthly) ** m_diff - 1) / r_monthly)
                else:
                    port_val = total_liquid + (monthly_investment * m_diff)
                target_val = fire_target_today * ((1 + inflation_rate / 100) ** y_diff)
            
            prog = (port_val / target_val * 100) if target_val > 0 else 0
            label = f"อายุ {age} ปี"
            if age == current_age:
                label += " (ปัจจุบัน)"
            elif age == target_retire_age:
                label += " 🎯 (เกษียณ)"

            milestones.append({
                "ช่วงอายุ": label,
                "ระยะเวลา": f"อีก {y_diff} ปี" if y_diff > 0 else "ปีปัจจุบัน",
                "พอร์ตคาดการณ์": f"฿{port_val:,.0f}",
                "เป้าหมาย FIRE": f"฿{target_val:,.0f}",
                "ความพร้อม": f"{prog:.0f}%"
            })

        df_milestones = pd.DataFrame(milestones)
        st.dataframe(
            df_milestones,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ช่วงอายุ": st.column_config.TextColumn("ช่วงอายุ", width="medium"),
                "ระยะเวลา": st.column_config.TextColumn("ระยะเวลา", width="small"),
                "พอร์ตคาดการณ์": st.column_config.TextColumn("พอร์ตคาดการณ์", width="medium"),
                "เป้าหมาย FIRE": st.column_config.TextColumn("เป้าหมาย FIRE", width="medium"),
                "ความพร้อม": st.column_config.TextColumn("ความพร้อม", width="small"),
            }
        )

        st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 14px; font-size: 0.8rem; color: #475569; margin-top: 6px;">
            <b>💡 สมมติฐานที่ใช้ในการคำนวณ:</b><br>
            • ผลตอบแทนพอร์ตคาดหวังเฉลี่ย: <b>{expected_roi:.1f}% ต่อปี</b><br>
            • อัตราเงินเฟ้อเฉลี่ย: <b>{inflation_rate:.1f}% ต่อปี</b><br>
            • ค่าใช้จ่ายหลังเกษียณ: <b>฿{fire_spend_today:,.0f}/เดือน</b> (กฎ 4% Rule หรือ 25 เท่าของรายจ่ายทั้งปี)
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 6. QUICK NAVIGATION SHORTCUTS
    # -------------------------------------------------------------------------
    st.divider()
    qc1, qc2, qc3, qc4 = st.columns(4)
    with qc1:
        if st.button("📊 ประมาณการรายเดือน ➔", use_container_width=True, key="btn_nav_monthly"):
            st.session_state["redirect_nav"] = "📊 ประมาณการรายเดือน (Monthly Planner)"
            st.rerun()

    with qc2:
        if st.button("📈 พอร์ตการลงทุน ➔", use_container_width=True, key="btn_nav_portfolio"):
            st.session_state["redirect_nav"] = "📈 พอร์ตการลงทุน (Portfolio)"
            st.rerun()

    with qc3:
        if st.button("🏛️ ความมั่งคั่ง & FIRE ➔", use_container_width=True, key="btn_nav_fire"):
            st.session_state["redirect_nav"] = "🏛️ ความมั่งคั่ง & อิสรภาพการเงิน (Net Worth & FIRE)"
            st.rerun()

    with qc4:
        if st.button("📜 ประวัติ & สำรองข้อมูล ➔", use_container_width=True, key="btn_nav_history"):
            st.session_state["redirect_nav"] = "📜 ประวัติ & สำรองข้อมูล (History & Backup)"
            st.rerun()
