"""
Net Worth, Liabilities & FIRE (Financial Independence) Calculator Module
Calculates total net worth, debt solvency, FIRE number (4% rule), and compounding multi-year simulations.
"""

import streamlit as st
import pandas as pd
from database import (
    get_all_assets, get_all_liabilities, add_liability,
    update_liability, delete_liability, save_liabilities_batch, get_monthly_profile, update_monthly_profile,
    get_categories, safe_float, safe_str
)
from components.styles import render_metric_card
from components.charts import create_fire_projection_chart

def render_networth_fire():
    LIABILITY_CATEGORIES = get_categories("liability")
    assets = get_all_assets()
    liabilities = get_all_liabilities()
    profile = get_monthly_profile()

    def is_fixed(a):
        if a.get("asset_type") == "fixed_asset":
            return True
        cat = str(a.get("category", ""))
        name = str(a.get("name", ""))
        return any(k in cat for k in ["บ้าน", "คอนโด", "ที่ดิน", "อสังหา", "สิ่งปลูกสร้าง", "Real Estate", "รถยนต์", "Vehicle"]) or \
               any(k in name for k in ["บ้าน", "คอนโด", "ที่ดิน"])

    liquid_assets = [a for a in assets if not is_fixed(a)]
    fixed_assets = [a for a in assets if is_fixed(a)]

    total_liquid = sum(a["current_value"] for a in liquid_assets)
    total_fixed = sum(a["current_value"] for a in fixed_assets)
    total_assets = total_liquid + total_fixed
    total_liabilities = sum(l["total_balance"] for l in liabilities)
    net_worth = total_assets - total_liabilities
    monthly_debt_payments = sum(l["monthly_payment"] for l in liabilities)
    total_monthly_dca = sum(a["monthly_dca"] for a in liquid_assets)

    st.markdown('<div class="section-header">🏛️ ความมั่งคั่งสุทธิ & วางแผนสู่อิสรภาพการเงิน (Net Worth & FIRE Plan)</div>', unsafe_allow_html=True)
    st.caption("งบดุลสินทรัพย์-หนี้สิน, การจำลองการเติบโตแบบทบต้น (Compounding) และคำนวณเป้าหมายสู่อิสรภาพทางการเงิน (FIRE)")

    # Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        nw_badge = "green" if net_worth >= 0 else "rose"
        render_metric_card(
            title="Net Worth (ความมั่งคั่งสุทธิ)",
            value=f"฿{net_worth:,.0f}",
            subtext=f"สินทรัพย์ - หนี้สิน",
            badge_text="Net Worth",
            badge_type=nw_badge
        )
    with c2:
        render_metric_card(
            title="สินทรัพย์รวม (Total Assets)",
            value=f"฿{total_assets:,.0f}",
            subtext=f"ลงทุน ฿{total_liquid:,.0f} | บ้าน/ถาวร ฿{total_fixed:,.0f}",
            badge_text=f"{len(assets)} รายการ",
            badge_type="indigo"
        )
    with c3:
        debt_badge = "rose" if total_liabilities > 0 else "green"
        render_metric_card(
            title="หนี้สินรวม (Liabilities)",
            value=f"฿{total_liabilities:,.0f}",
            subtext=f"ภาระผ่อน ฿{monthly_debt_payments:,.0f}/ด.",
            badge_text=f"{len(liabilities)} รายการหนี้",
            badge_type=debt_badge
        )
    with c4:
        solvency_ratio = (total_assets / total_liabilities * 100) if total_liabilities > 0 else 999
        solv_badge = "green" if solvency_ratio >= 150 else ("amber" if solvency_ratio >= 100 else "rose")
        render_metric_card(
            title="อัตราส่วนความมั่งคั่ง (Solvency)",
            value=f"{solvency_ratio:.0f}%" if solvency_ratio < 999 else "100% ปลอดหนี้",
            subtext="สินทรัพย์ต่อหนี้สิน",
            badge_text="Financial Health",
            badge_type=solv_badge
        )

    st.markdown("---")

    # Section 1: FIRE Calculator
    st.markdown("### 🎯 FIRE & Financial Freedom Calculator (กฎ 4% Rule)")

    with st.expander("⚙️ ปรับแต่งสมมติฐานการคำนวณ FIRE", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            current_age = st.number_input("อายุปัจจุบัน", min_value=15, max_value=80, value=int(profile.get("fire_current_age", 29)), step=1)
            target_retire_age = st.number_input("อายุที่ต้องการเกษียณ/อิสรภาพการเงิน", min_value=current_age + 1, max_value=90, value=int(profile.get("fire_target_age", 50)), step=1)
        with fc2:
            target_monthly_spend = st.number_input(
                "ค่าใช้จ่ายที่ต้องการใช้ต่อเดือนหลังเกษียณ (บาท)",
                min_value=5000.0,
                value=float(profile.get("fire_target_monthly_spend", 35000)),
                step=5000.0,
                format="%.0f"
            )
            years_to_retire = max(1, target_retire_age - current_age)
            expected_roi = st.number_input("ผลตอบแทนพอร์ตคาดหวังเฉลี่ย (% ต่อปี)", min_value=1.0, max_value=25.0, value=float(profile.get("fire_expected_return", 7.0)), step=0.5)
        with fc3:
            inflation_rate = st.number_input("อัตราเงินเฟ้อคาดการณ์ (% ต่อปี)", min_value=0.0, max_value=15.0, value=float(profile.get("fire_inflation_rate", 2.5)), step=0.5)
            st.caption(f"⏱️ ระยะเวลาสะสมความมั่งคั่ง: **{years_to_retire} ปี**")

        if st.button("💾 อัปเดตสมมติฐาน FIRE ลงโปรไฟล์", type="secondary"):
            update_data = {
                "salary": profile.get("salary", 50000),
                "bonus_or_other_income": profile.get("bonus_or_other_income", 0),
                "passive_income": profile.get("passive_income", 0),
                "fixed_expenses": profile.get("fixed_expenses", 15000),
                "variable_expense_estimate": profile.get("variable_expense_estimate", 15000),
                "emergency_fund_target_months": profile.get("emergency_fund_target_months", 6),
                "fire_target_monthly_spend": target_monthly_spend,
                "fire_expected_return": expected_roi,
                "fire_inflation_rate": inflation_rate,
                "fire_current_age": current_age,
                "fire_target_age": target_retire_age,
                "fire_monthly_dca": 0
            }
            update_monthly_profile(update_data)
            st.toast("บันทึกสมมติฐาน FIRE เรียบร้อยแล้ว", icon="🎯")
            st.rerun()

    # Option to select asset base for FIRE
    fire_base_choice = st.radio(
        "💼 พอร์ตสินทรัพย์ตั้งต้นสำหรับการคำนวณ FIRE:",
        [
            f"พอร์ตลงทุนสภาพคล่องเท่านั้น (฿{total_liquid:,.0f}) [แนะนำ: หุ้น/กองทุน/คริปโต/เงินสด]",
            f"รวมสินทรัพย์ทั้งหมด (฿{total_assets:,.0f}) [รวมบ้าน/ที่ดิน/สิ่งปลูกสร้าง]"
        ],
        index=0,
        horizontal=True
    )
    fire_base_amount = total_liquid if "สภาพคล่องเท่านั้น" in fire_base_choice else total_assets

    # Calculations for FIRE
    # Annual spend in future value adjusted for inflation
    annual_spend_today = target_monthly_spend * 12
    # 4% rule -> 25x annual expenses
    fire_target_today = annual_spend_today * 25
    fire_target_future = fire_target_today * ((1 + inflation_rate / 100) ** years_to_retire)

    # Current Portfolio FV projection at target age
    r_monthly = (expected_roi / 100) / 12
    n_months = years_to_retire * 12
    if r_monthly > 0:
        projected_portfolio = fire_base_amount * ((1 + r_monthly) ** n_months)
    else:
        projected_portfolio = fire_base_amount

    fire_progress_today = min(1.0, (fire_base_amount / fire_target_today)) if fire_target_today > 0 else 0
    progress_at_target_age = min(1.0, (projected_portfolio / fire_target_future)) if fire_target_future > 0 else 0

    # FIRE summary cards
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        render_metric_card(
            title="เป้าหมาย FIRE Number (มูลค่าปัจจุบัน)",
            value=f"฿{fire_target_today:,.0f}",
            subtext=f"รายจ่าย ฿{target_monthly_spend:,.0f}/ด. x 25 เท่า (4% Rule)",
            badge_text=f"บรรลุ {fire_progress_today*100:.1f}%",
            badge_type="indigo"
        )
    with fc2:
        render_metric_card(
            title=f"เป้าหมายเมื่ออายุ {target_retire_age} ปี (รวมเงินเฟ้อ)",
            value=f"฿{fire_target_future:,.0f}",
            subtext=f"เงินเฟ้อ {inflation_rate}% ต่อปี อีก {years_to_retire} ปี",
            badge_text="Inflation Adjusted",
            badge_type="amber"
        )
    with fc3:
        proj_badge = "green" if projected_portfolio >= fire_target_future else "cyan"
        render_metric_card(
            title=f"คาดการณ์พอร์ตเมื่ออายุ {target_retire_age} ปี",
            value=f"฿{projected_portfolio:,.0f}",
            subtext=f"เติบโตทบต้นเฉลี่ย {expected_roi}% ต่อปี",
            badge_text=f"คิดเป็น {progress_at_target_age*100:.0f}% ของเป้าหมาย",
            badge_type=proj_badge
        )

    # Progress bar
    st.markdown(f"**ความคืบหน้าสู่เป้าหมาย ณ มูลค่าปัจจุบัน (พอร์ตมี ฿{fire_base_amount:,.0f} จากเป้าหมาย ฿{fire_target_today:,.0f})**")
    st.progress(fire_progress_today)

    # Simulation Chart
    st.plotly_chart(
        create_fire_projection_chart(
            current_nw=fire_base_amount,
            monthly_invest=0,
            years=max(15, years_to_retire + 5),
            expected_return=expected_roi,
            fire_target=fire_target_today
        ),
        use_container_width=True
    )

    # Educational Expander for Net Worth & FIRE
    with st.expander("📖 คู่มือทำความเข้าใจ: ความมั่งคั่งสุทธิ (Net Worth) & สูตรคำนวณเกษียณเร็ว (FIRE 4% Rule)", expanded=False):
        nwc1, nwc2 = st.columns(2)
        with nwc1:
            st.markdown("""
            ##### 🏛️ ความมั่งคั่ง & งบดุล (Balance Sheet)
            * **Net Worth (ความมั่งคั่งสุทธิ):** คำนวณจาก `สินทรัพย์ทั้งหมด (ลงทุน + บ้าน/ที่ดิน) - หนี้สินทั้งหมด` แสดงมูลค่าความมั่งคั่งที่แท้จริงที่คุณเป็นเจ้าของ
            * **อัตราส่วนความมั่งคั่ง (Solvency Ratio):** สัดส่วน `สินทรัพย์รวม / หนี้สินรวม` หากเกิน **150%** ถือว่ามีความมั่นคงทางการเงินสูงมาก
            * **การแยกบ้านออกจากพอร์ต FIRE:** บ้านใช้นับใน Net Worth ได้ แต่ไม่ควรนำมารวมในพอร์ตเกษียณ 4% เพราะไม่ได้ผลิตกระแสเงินสดมาเป็นค่าข้าวในแต่ละวัน
            """)
        with nwc2:
            st.markdown("""
            ##### 🚀 กฎ 4% Rule & พลังดอกเบี้ยทบต้น (Compounding)
            * **FIRE Number (เป้าหมาย ณ มูลค่าปัจจุบัน):** คิดจาก `(ค่าใช้จ่ายต่อเดือนหลังเกษียณ x 12 เดือน) x 25 เท่า`
            * **ทำไมต้อง 25 เท่า (4% Rule)?:** เพราะถ้ามีเงิน 25 เท่า เมื่อถอนออกมาใช้ปีละ 4% เงินต้นจะถูกผลตอบแทนจากการลงทุนชดเชยและอยู่ได้ตลอดไปโดยเงินไม่หมด
            * **มูลค่าเมื่อถึงอายุเกษียณ (Inflation Adjusted):** คำนวณเงินเฟ้อสะสมเข้าไป เพื่อให้ทราบว่าเงิน 35,000 บาทในวันนี้ จะเทียบเท่ากับกี่บาทในอีกหลายสิบปีข้างหน้า
            * **คาดการณ์พอร์ต (Future Value):** คำนวณพลังดอกเบี้ยทบต้นจาก `พอร์ตปัจจุบัน + เงินออม DCA ทุกเดือน x ผลตอบแทนเฉลี่ยต่อปี`
            """)

    st.markdown("---")

    # Section 2: Manage Liabilities (หนี้สินและภาระผูกพัน)
    st.markdown("### 💳 จัดการรายการหนี้สิน & ภาระผูกพัน (Liabilities)")
    
    tab_debts_view, tab_debts_editor, tab_debts_add = st.tabs([
        "📋 รายการหนี้สินทั้งหมด", 
        "📝 แก้ไขตารางด่วน (Table Editor)",
        "➕ เพิ่มรายการหนี้สิน (Form)"
    ])

    with tab_debts_view:
        if not liabilities:
            st.success("🎉 ยินดีด้วย! คุณไม่มีรายการหนี้สินที่บันทึกไว้ (ปลอดหนี้ 100%)")
        else:
            ldf = pd.DataFrame(liabilities)
            formatted_ldf = pd.DataFrame({
                "รายการหนี้สิน": ldf["name"],
                "หมวดหมู่": ldf["category"],
                "ยอดหนี้คงเหลือ": ldf["total_balance"].apply(lambda x: f"฿{x:,.0f}"),
                "ค่างวดรายเดือน": ldf["monthly_payment"].apply(lambda x: f"฿{x:,.0f}"),
                "อัตราดอกเบี้ย": ldf["interest_rate"].apply(lambda x: f"{x:.2f}%"),
                "หมายเหตุ": ldf["notes"]
            })
            st.dataframe(formatted_ldf, use_container_width=True, hide_index=True)

            with st.expander("🗑️ ลบรายการหนี้สิน"):
                debt_opts = {f"{l['name']} (คงเหลือ ฿{l['total_balance']:,.0f})": l['id'] for l in liabilities}
                del_debt_label = st.selectbox("เลือกหนี้สินที่ต้องการลบ", list(debt_opts.keys()))
                if st.button("ลบรายการนี้", type="secondary"):
                    delete_liability(debt_opts[del_debt_label])
                    st.toast("ลบรายการหนี้สินเรียบร้อย", icon="🗑️")
                    st.rerun()

    with tab_debts_editor:
        st.markdown("##### 📝 แก้ไข/เพิ่ม/ลบ หนี้สินแบบตารางด่วน")
        st.caption("ดับเบิลคลิกแก้ไขตัวเลขในช่องตาราง, กดปุ่ม `+` ด้านล่างเพื่อเพิ่มหนี้สินใหม่, หรือติ๊กแถวแล้วกด Delete เพื่อลบ")
        
        debts_edit_cols = ["id", "name", "category", "total_balance", "monthly_payment", "interest_rate", "notes"]
        ldf_edit = pd.DataFrame(liabilities)[debts_edit_cols] if liabilities else pd.DataFrame(columns=debts_edit_cols)

        debts_col_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "name": st.column_config.TextColumn("ชื่อภาระหนี้", required=True),
            "category": st.column_config.SelectboxColumn("หมวดหมู่", options=LIABILITY_CATEGORIES, required=True),
            "total_balance": st.column_config.NumberColumn("ยอดหนี้คงเหลือ (฿)", min_value=0, format="%.0f"),
            "monthly_payment": st.column_config.NumberColumn("ค่างวด/เดือน (฿)", min_value=0, format="%.0f"),
            "interest_rate": st.column_config.NumberColumn("ดอกเบี้ย (%/ปี)", format="%.2f%%"),
            "notes": st.column_config.TextColumn("หมายเหตุ"),
        }

        edited_debts = st.data_editor(
            ldf_edit,
            column_config=debts_col_config,
            num_rows="dynamic",
            use_container_width=True,
            key="debts_table_editor"
        )

        if st.button("💾 บันทึกการเปลี่ยนแปลงหนี้สินทั้งหมด", type="primary", use_container_width=True):
            save_liabilities_batch(edited_debts.to_dict("records"))
            st.toast("บันทึกข้อมูลหนี้สินเรียบร้อยแล้ว!", icon="💾")
            st.rerun()

    with tab_debts_add:
        with st.form("add_liability_form", clear_on_submit=True):
            st.markdown("##### ➕ เพิ่มรายการหนี้สินใหม่")
            lc1, lc2 = st.columns(2)
            with lc1:
                debt_name = st.text_input("ชื่อภาระหนี้ (เช่น ผ่อนบ้าน, ผ่อนรถยนต์, บัตรเครดิต KTC)", placeholder="เช่น ค่างวดคอนโด")
                debt_category = st.selectbox("หมวดหมู่หนี้สิน", LIABILITY_CATEGORIES)
                debt_balance = st.number_input("ยอดหนี้คงเหลือทั้งหมด (บาท)", min_value=0.0, step=10000.0, format="%.0f")
            with lc2:
                debt_payment = st.number_input("ค่างวดผ่อนชำระต่อเดือน (บาท)", min_value=0.0, step=500.0, format="%.0f")
                debt_interest = st.number_input("อัตราดอกเบี้ยต่อปี (% ต่อปี)", min_value=0.0, max_value=40.0, step=0.1, value=3.5)
                debt_notes = st.text_input("บันทึกเพิ่มเติม", placeholder="เช่น หักบัญชีทุกวันที่ 1, ผ่อน 30 ปี")

            submitted_debt = st.form_submit_button("➕ บันทึกหนี้สิน", use_container_width=True, type="primary")
            if submitted_debt:
                if not debt_name.strip():
                    st.error("กรุณาระบุชื่อภาระหนี้")
                else:
                    add_liability({
                        "name": debt_name.strip(),
                        "category": debt_category,
                        "total_balance": debt_balance,
                        "monthly_payment": debt_payment,
                        "interest_rate": debt_interest,
                        "notes": debt_notes.strip()
                    })
                    st.toast(f"บันทึกหนี้สิน '{debt_name}' สำเร็จ!", icon="✅")
                    st.rerun()
