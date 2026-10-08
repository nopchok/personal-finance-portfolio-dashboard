"""
Net Worth, Liabilities & FIRE (Financial Independence) Calculator Module
Calculates total net worth, debt solvency, FIRE number (4% rule),
and Future Guaranteed Cash Flows (Endowment Insurance, Pension Annuity, Social Security, PVD/GPF).
"""

from datetime import datetime
import streamlit as st
import pandas as pd
from database import (
    get_all_assets, get_all_liabilities, add_liability,
    update_liability, delete_liability, save_liabilities_batch,
    get_all_future_cashflows, add_future_cashflow, update_future_cashflow,
    delete_future_cashflow, save_future_cashflows_batch,
    get_monthly_profile, update_monthly_profile,
    get_categories, safe_float, safe_str
)
from components.styles import render_metric_card
from components.charts import create_fire_projection_chart, create_future_cashflow_timeline_chart

FLOW_TYPES = [
    "เงินก้อนครั้งเดียว (Lump Sum)",
    "บำนาญรายปี (Annual Pension)"
]

def render_networth_fire():
    LIABILITY_CATEGORIES = get_categories("liability")
    FUTURE_CF_CATEGORIES = get_categories("future_cashflow")
    
    assets = get_all_assets()
    liabilities = get_all_liabilities()
    future_cfs = get_all_future_cashflows()
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

    st.markdown('<div class="section-header">🏛️ ความมั่งคั่งสุทธิ & วางแผนสู่อิสรภาพการเงิน (Net Worth & FIRE Plan)</div>', unsafe_allow_html=True)
    st.caption("งบดุลสินทรัพย์-หนี้สิน, แผนเงินคืน/บำนาญประกันในอนาคต และการคำนวณเป้าหมายสู่อิสรภาพทางการเงิน (FIRE)")

    # Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        nw_badge = "green" if net_worth >= 0 else "rose"
        render_metric_card(
            title="Net Worth (ความมั่งคั่งสุทธิ)",
            value=f"฿{net_worth:,.0f}",
            subtext="สินทรัพย์ - หนี้สิน",
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

    # =========================================================================
    # SECTION 1: FUTURE CASH FLOWS & INSURANCE ANNUITY (NEW FEATURE)
    # =========================================================================
    st.markdown("### 🛡️ แผนเงินคืน & บำนาญประกันในอนาคต (Guaranteed Future Cash Flows)")
    st.caption("วางแผนกระแสเงินสดที่การันตีในอนาคต เช่น ประกันสะสมทรัพย์ครบสัญญา, ประกันบำนาญ, บำนาญชราภาพประกันสังคม หรือเงินก้อน กบข./สำรองเลี้ยงชีพ")

    # Calculate Cash Flow Aggregates
    curr_y = datetime.now().year
    default_birth_year = int(profile.get("fire_birth_year", curr_y - int(profile.get("fire_current_age", 29))))
    current_age = max(1, curr_y - default_birth_year)
    target_retire_age = max(current_age + 1, int(profile.get("fire_target_age", 50)))
    target_monthly_spend = float(profile.get("fire_target_monthly_spend", 35000))

    total_lump_sums = sum(
        float(c.get("amount", 0)) for c in future_cfs
        if "เงินก้อน" in c.get("flow_type", "") or "Lump" in c.get("flow_type", "")
    )
    
    # Active Pension during retirement age
    active_pension_annual = sum(
        float(c.get("amount", 0)) for c in future_cfs
        if ("บำนาญ" in c.get("flow_type", "") or "Pension" in c.get("flow_type", "") or "Annuity" in c.get("flow_type", ""))
        and (int(c.get("start_age", 60)) <= target_retire_age <= int(c.get("end_age", 85)))
    )
    active_pension_monthly = active_pension_annual / 12

    # Metric Cards for Future Incomes
    ic1, ic2, ic3, ic4 = st.columns(4)
    with ic1:
        render_metric_card(
            title="เงินก้อนการันตีในอนาคต",
            value=f"฿{total_lump_sums:,.0f}",
            subtext="เงินคืนครบสัญญา/กบข./PVD",
            badge_text="Lump Sum",
            badge_type="emerald"
        )
    with ic2:
        render_metric_card(
            title="บำนาญการันตีช่วงเกษียณ",
            value=f"฿{active_pension_monthly:,.0f}/ด.",
            subtext=f"ปีละ ฿{active_pension_annual:,.0f} (อายุ {target_retire_age} ปี)",
            badge_text="Monthly Annuity",
            badge_type="indigo"
        )
    with ic3:
        # Relief to FIRE target (Annuity x 25 + Lump sums)
        fire_relief_val = (active_pension_annual * 25) + total_lump_sums
        render_metric_card(
            title="ลดเป้าหมายพอร์ตเกษียณลงได้",
            value=f"฿{fire_relief_val:,.0f}",
            subtext="ไม่ต้องเก็บเงินก้อนนี้เพิ่มเอง",
            badge_text="Target Relief",
            badge_type="green"
        )
    with ic4:
        render_metric_card(
            title="จำนวนสัญญา/แผนในอนาคต",
            value=f"{len(future_cfs)} แผน",
            subtext="กรมธรรม์และเงินรับการันตี",
            badge_text="Active Policies",
            badge_type="cyan"
        )

    # Future Inflow Timeline Chart
    st.plotly_chart(
        create_future_cashflow_timeline_chart(future_cfs, current_age=current_age, max_age=85),
        use_container_width=True
    )

    # Sub-tabs for Future Cash Flow Management
    tab_cf_view, tab_cf_editor, tab_cf_add = st.tabs([
        "📋 รายการแผนเงินคืน & บำนาญทั้งหมด",
        "📝 แก้ไขตารางด่วน (Table Editor)",
        "➕ เพิ่มรายการแผนเงินคืน/บำนาญใหม่ (Form)"
    ])

    with tab_cf_view:
        if not future_cfs:
            st.info("💡 ยังไม่มีรายการแผนเงินคืน/บำนาญในอนาคต กดแท็บ **'➕ เพิ่มรายการแผนเงินคืน/บำนาญใหม่'** หรือ **'📝 แก้ไขตารางด่วน'** เพื่อเริ่มวางแผนได้เลยครับ")
        else:
            cf_df = pd.DataFrame(future_cfs)
            formatted_cf_df = pd.DataFrame({
                "ชื่อแผน / กรมธรรม์": cf_df["name"],
                "หมวดหมู่": cf_df["category"],
                "รูปแบบ": cf_df["flow_type"],
                "จำนวนเงิน": cf_df.apply(lambda r: f"฿{r['amount']:,.0f}" + (" / ปี" if "บำนาญ" in r['flow_type'] else ""), axis=1),
                "ช่วงอายุที่ได้รับ": cf_df.apply(lambda r: f"อายุ {int(r['start_age'])} ปี" if "เงินก้อน" in r['flow_type'] else f"อายุ {int(r['start_age'])} - {int(r['end_age'])} ปี", axis=1),
                "หมายเหตุ": cf_df["notes"]
            })
            st.dataframe(formatted_cf_df, use_container_width=True, hide_index=True)

            with st.expander("🗑️ ลบรายการแผนเงินคืน/บำนาญ"):
                cf_opts = {f"{c['name']} (฿{c['amount']:,.0f})": c['id'] for c in future_cfs}
                del_cf_label = st.selectbox("เลือกรายการที่ต้องการลบ", list(cf_opts.keys()))
                if st.button("ลบรายการนี้", type="secondary", key="btn_del_future_cf"):
                    delete_future_cashflow(cf_opts[del_cf_label])
                    st.toast("ลบรายการแผนเงินคืนเรียบร้อย", icon="🗑️")
                    st.rerun()

    with tab_cf_editor:
        st.markdown("##### 📝 แก้ไข/เพิ่ม/ลบ แผนเงินคืนและบำนาญแบบตารางด่วน")
        st.caption("ดับเบิลคลิกแก้ไขตัวเลขในช่องตาราง, กดปุ่ม `+` ด้านล่างเพื่อเพิ่มแถวใหม่ หรือติ๊กแถวแล้วกด Delete เพื่อลบ")

        cf_edit_cols = ["id", "name", "category", "flow_type", "amount", "start_age", "end_age", "notes"]
        cf_df_edit = pd.DataFrame(future_cfs)[cf_edit_cols] if future_cfs else pd.DataFrame(columns=cf_edit_cols)

        cf_col_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "name": st.column_config.TextColumn("ชื่อแผน / กรมธรรม์", required=True),
            "category": st.column_config.SelectboxColumn("หมวดหมู่", options=FUTURE_CF_CATEGORIES, required=True),
            "flow_type": st.column_config.SelectboxColumn("รูปแบบการรับเงิน", options=FLOW_TYPES, required=True),
            "amount": st.column_config.NumberColumn("จำนวนเงิน (฿ หรือ ฿/ปี)", min_value=0, format="%.0f"),
            "start_age": st.column_config.NumberColumn("อายุที่เริ่มรับเงิน", min_value=1, max_value=100, format="%d"),
            "end_age": st.column_config.NumberColumn("อายุสิ้นสุดการรับเงิน", min_value=1, max_value=100, format="%d"),
            "notes": st.column_config.TextColumn("หมายเหตุ"),
        }

        edited_cfs = st.data_editor(
            cf_df_edit,
            column_config=cf_col_config,
            num_rows="dynamic",
            use_container_width=True,
            key="future_cfs_table_editor"
        )

        if st.button("💾 บันทึกการเปลี่ยนแปลงแผนเงินคืนทั้งหมด", type="primary", use_container_width=True, key="btn_save_batch_cf"):
            save_future_cashflows_batch(edited_cfs.to_dict("records"))
            st.toast("บันทึกข้อมูลแผนเงินคืน/บำนาญเรียบร้อยแล้ว!", icon="💾")
            st.rerun()

    with tab_cf_add:
        with st.form("add_future_cf_form", clear_on_submit=True):
            st.markdown("##### ➕ เพิ่มแผนเงินคืน & บำนาญในอนาคต")
            fcol1, fcol2 = st.columns(2)
            with fcol1:
                cf_name = st.text_input("ชื่อแผน / กรมธรรม์", placeholder="เช่น ประกันสะสมทรัพย์ AIA 15/25, ประกันบำนาญ เมืองไทย 85/60")
                cf_cat = st.selectbox("หมวดหมู่", FUTURE_CF_CATEGORIES)
                cf_type = st.selectbox("รูปแบบการรับเงิน", FLOW_TYPES)
                cf_amount = st.number_input("จำนวนเงิน (บาท ต่อครั้ง หรือต่อปี)", min_value=0.0, step=10000.0, format="%.0f")
            with fcol2:
                cf_start_age = st.number_input("อายุที่จะได้รับเงิน (หรือเริ่มรับบำนาญ)", min_value=1, max_value=100, value=max(current_age + 1, 55), step=1)
                cf_end_age = st.number_input("อายุสิ้นสุดการรับเงิน (กรณีบำนาญ เช่น 85 ปี, ถ้าเงินก้อนให้ใส่อายุเท่าเดิม)", min_value=1, max_value=100, value=max(current_age + 1, 85), step=1)
                cf_notes = st.text_input("บันทึกเพิ่มเติม", placeholder="เช่น เงินคืนครบสัญญา 20 ปี, จ่ายบำนาญปีละ 60,000 บ.")

            submitted_cf = st.form_submit_button("➕ บันทึกแผนเงินคืน/บำนาญ", use_container_width=True, type="primary")
            if submitted_cf:
                if not cf_name.strip():
                    st.error("กรุณาระบุชื่อแผนหรือกรมธรรม์")
                else:
                    if "เงินก้อน" in cf_type:
                        cf_end_age = cf_start_age
                    add_future_cashflow({
                        "name": cf_name.strip(),
                        "category": cf_cat,
                        "flow_type": cf_type,
                        "amount": cf_amount,
                        "start_age": cf_start_age,
                        "end_age": cf_end_age,
                        "notes": cf_notes.strip()
                    })
                    st.toast(f"บันทึกแผน '{cf_name}' สำเร็จ!", icon="✅")
                    st.rerun()

    st.markdown("---")

    # =========================================================================
    # SECTION 2: FIRE CALCULATOR WITH GUARANTEED INCOME
    # =========================================================================
    st.markdown("### 🎯 FIRE & Financial Freedom Calculator (กฎ 4% Rule แบบรวมประกัน)")

    with st.expander("⚙️ ปรับแต่งสมมติฐานการคำนวณ FIRE", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            birth_year = st.number_input(
                "ปี ค.ศ. เกิด (Birth Year)",
                min_value=1930,
                max_value=curr_y - 5,
                value=default_birth_year,
                step=1,
                help=f"เช่น {default_birth_year} (พ.ศ. {default_birth_year + 543}) ระบบจะคำนวณอายุให้อัตโนมัติทุกปี"
            )
            calc_age = max(1, curr_y - int(birth_year))
            st.caption(f"🎂 ปัจจุบันอายุ: **{calc_age} ปี** (เกิด พ.ศ. {int(birth_year) + 543})")
            target_retire_age_input = st.number_input(
                "อายุที่ต้องการเกษียณ/อิสรภาพการเงิน",
                min_value=calc_age + 1,
                max_value=100,
                value=max(calc_age + 1, int(profile.get("fire_target_age", 50))),
                step=1
            )
        with fc2:
            target_monthly_spend_input = st.number_input(
                "ค่าใช้จ่ายที่ต้องการใช้ต่อเดือนหลังเกษียณ (บาท)",
                min_value=5000.0,
                value=float(profile.get("fire_target_monthly_spend", 35000)),
                step=5000.0,
                format="%.0f"
            )
            years_to_retire = max(1, target_retire_age_input - calc_age)
            expected_roi = st.number_input("ผลตอบแทนพอร์ตคาดหวังเฉลี่ย (% ต่อปี)", min_value=1.0, max_value=25.0, value=float(profile.get("fire_expected_return", 7.0)), step=0.5)
        with fc3:
            inflation_rate = st.number_input("อัตราเงินเฟ้อคาดการณ์ (% ต่อปี)", min_value=0.0, max_value=15.0, value=float(profile.get("fire_inflation_rate", 2.5)), step=0.5)
            st.caption(f"⏱️ ระยะเวลาสะสมความมั่งคั่ง: **{years_to_retire} ปี**")

        if st.button("💾 อัปเดตสมมติฐาน FIRE ลงโปรไฟล์", type="secondary"):
            update_data = {
                "salary": profile.get("salary", 0),
                "bonus_or_other_income": profile.get("bonus_or_other_income", 0),
                "passive_income": profile.get("passive_income", 0),
                "fixed_expenses": profile.get("fixed_expenses", 0),
                "variable_expense_estimate": profile.get("variable_expense_estimate", 0),
                "emergency_fund_target_months": profile.get("emergency_fund_target_months", 6),
                "fire_target_monthly_spend": target_monthly_spend_input,
                "fire_expected_return": expected_roi,
                "fire_inflation_rate": inflation_rate,
                "fire_birth_year": birth_year,
                "fire_current_age": calc_age,
                "fire_target_age": target_retire_age_input,
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

    # Calculations for Standard FIRE vs Adjusted FIRE with Insurance
    annual_spend_today = target_monthly_spend_input * 12
    raw_fire_target_today = annual_spend_today * 25

    # Net spend required from portfolio after guaranteed annuity
    net_monthly_spend_needed = max(0.0, target_monthly_spend_input - active_pension_monthly)
    net_annual_spend_needed = net_monthly_spend_needed * 12
    
    # Adjusted target deducting retirement lump sums
    adjusted_fire_target_today = max(0.0, (net_annual_spend_needed * 25) - total_lump_sums)
    fire_target_future = adjusted_fire_target_today * ((1 + inflation_rate / 100) ** years_to_retire)

    # Current Portfolio FV projection at target age (with compounding + future cash flows)
    r_monthly = (expected_roi / 100) / 12
    n_months = years_to_retire * 12
    if r_monthly > 0:
        projected_portfolio = fire_base_amount * ((1 + r_monthly) ** n_months)
    else:
        projected_portfolio = fire_base_amount

    fire_progress_today = min(1.0, (fire_base_amount / adjusted_fire_target_today)) if adjusted_fire_target_today > 0 else 1.0
    progress_at_target_age = min(1.0, (projected_portfolio / fire_target_future)) if fire_target_future > 0 else 1.0

    # FIRE summary cards
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        render_metric_card(
            title="เป้าหมาย FIRE สุทธิ (หักลบประกันแล้ว)",
            value=f"฿{adjusted_fire_target_today:,.0f}",
            subtext=f"จากเดิม ฿{raw_fire_target_today:,.0f} (ประหยัด ฿{raw_fire_target_today - adjusted_fire_target_today:,.0f})",
            badge_text=f"บรรลุ {fire_progress_today*100:.1f}%",
            badge_type="indigo"
        )
    with fc2:
        render_metric_card(
            title=f"เป้าหมายเมื่ออายุ {target_retire_age_input} ปี (รวมเงินเฟ้อ)",
            value=f"฿{fire_target_future:,.0f}",
            subtext=f"เงินเฟ้อ {inflation_rate}% ต่อปี อีก {years_to_retire} ปี",
            badge_text="Inflation Adjusted",
            badge_type="amber"
        )
    with fc3:
        proj_badge = "green" if projected_portfolio >= fire_target_future else "cyan"
        render_metric_card(
            title=f"คาดการณ์พอร์ตเมื่ออายุ {target_retire_age_input} ปี",
            value=f"฿{projected_portfolio:,.0f}",
            subtext=f"เติบโตทบต้นเฉลี่ย {expected_roi}% ต่อปี",
            badge_text=f"คิดเป็น {progress_at_target_age*100:.0f}% ของเป้าหมาย",
            badge_type=proj_badge
        )

    # Progress bar
    st.markdown(f"**ความคืบหน้าสู่เป้าหมายเกษียณสุทธิ (พอร์ตมี ฿{fire_base_amount:,.0f} จากเป้าหมาย ฿{adjusted_fire_target_today:,.0f})**")
    st.progress(fire_progress_today)

    # Simulation Chart
    st.plotly_chart(
        create_fire_projection_chart(
            current_nw=fire_base_amount,
            monthly_invest=0,
            years=max(15, years_to_retire + 5),
            expected_return=expected_roi,
            fire_target=adjusted_fire_target_today,
            current_age=calc_age,
            future_cashflows=future_cfs
        ),
        use_container_width=True
    )

    # Educational Expander for Net Worth & FIRE
    with st.expander("📖 คู่มือทำความเข้าใจ: ความมั่งคั่งสุทธิ, แผนเงินคืนประกัน & กฎ 4% Rule", expanded=False):
        nwc1, nwc2 = st.columns(2)
        with nwc1:
            st.markdown("""
            ##### 🏛️ ความมั่งคั่ง & กระแสเงินสดการันตี (Guaranteed Inflows)
            * **Net Worth (ความมั่งคั่งสุทธิ):** คำนวณจาก `สินทรัพย์ทั้งหมด (ลงทุน + บ้าน/ที่ดิน) - หนี้สินทั้งหมด`
            * **ทำไมต้องใส่แผนเงินคืน/บำนาญประกัน?:** เพราะประกันสะสมทรัพย์, บำนาญ และเงินชราภาพประกันสังคม คือ **กระแสเงินสดที่การันตีแน่นอน** ในอนาคต
            * **ผลลัพธ์:** ทำให้คุณไม่ต้องแบกรับเป้าหมายการลงทุนในสินทรัพย์เสี่ยงสูงเกินไป ตัวเลข FIRE Number ที่ต้องเก็บจะ **ลดลงทันที**
            """)
        with nwc2:
            st.markdown("""
            ##### 🚀 กฎ 4% Rule & พลังดอกเบี้ยทบต้น (Compounding)
            * **สูตรคำนวณ Adjusted FIRE:** `[(ค่าใช้จ่ายหลังเกษียณ - บำนาญประกันต่อเดือน) x 12 เดือน x 25 เท่า] - เงินก้อนประกันที่ได้`
            * **ทำไมต้อง 25 เท่า (4% Rule)?:** เพราะถ้ามีเงิน 25 เท่า เมื่อถอนออกมาใช้ปีละ 4% เงินต้นจะถูกผลตอบแทนจากการลงทุนชดเชยและอยู่ได้ตลอดไป
            * **มูลค่าเมื่อถึงอายุเกษียณ (Inflation Adjusted):** คำนวณเงินเฟ้อสะสมเข้าไป เพื่อสะท้อนค่าครองชีพที่แท้จริงในอนาคต
            """)

    st.markdown("---")

    # =========================================================================
    # SECTION 3: MANAGE LIABILITIES
    # =========================================================================
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
