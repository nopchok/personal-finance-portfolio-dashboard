"""
Monthly Financial Status, Itemized Income & Expense Estimation Module
Provides high-level monthly budgeting with full table editing for both Income and Expense streams.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    get_monthly_profile, update_monthly_profile, 
    get_all_assets, get_all_liabilities, save_snapshot,
    get_all_income_items, add_income_item, update_income_item, delete_income_item, save_income_items_batch,
    get_all_expense_items, add_expense_item, update_expense_item, delete_expense_item, save_expense_items_batch,
    get_categories, safe_float, safe_str
)
from components.styles import render_metric_card
from components.charts import (
    create_cashflow_waterfall, create_budget_rule_gauge, 
    create_expense_donut, create_income_donut
)

INCOME_TYPES = [
    "ประจำ (Active / Fixed)",
    "ผันแปร/เสริม (Passive / Variable)"
]

EXPENSE_TYPES = [
    "คงที่ (Fixed)",
    "ผันแปร (Variable)"
]

def render_monthly_planner():
    profile = get_monthly_profile()
    if not profile:
        st.warning("ไม่พบข้อมูลโปรไฟล์รายเดือน")
        return

    INCOME_CATEGORIES = get_categories("income")
    EXPENSE_CATEGORIES = get_categories("expense")

    assets = get_all_assets()
    liabilities = get_all_liabilities()
    income_items = get_all_income_items()
    expense_items = get_all_expense_items()
    
    total_assets = sum(a["current_value"] for a in assets)
    total_liabilities = sum(l["total_balance"] for l in liabilities)
    net_worth = total_assets - total_liabilities
    
    # Calculate emergency cash currently held
    cash_assets = sum(a["current_value"] for a in assets if "เงินสด" in a["category"] or "ฉุกเฉิน" in a["category"] or "Cash" in a["category"])

    st.markdown('<div class="section-header">📊 ประมาณการสถานะการเงินรายเดือน (Monthly Cash Flow & Budget Overview)</div>', unsafe_allow_html=True)
    st.caption("วางแผนและประมาณการงบประมาณรายเดือนแบบตารางทั้งฝั่ง 'รายได้' และ 'รายจ่าย' (ไม่ต้องกรอกรายจ่ายยิบย่อยรายวัน)")

    # DataFrames for Income & Expenses
    inc_df = pd.DataFrame(income_items) if income_items else pd.DataFrame(columns=[
        "id", "name", "category", "income_type", "estimated_amount", "notes"
    ])
    exp_df = pd.DataFrame(expense_items) if expense_items else pd.DataFrame(columns=[
        "id", "name", "category", "expense_type", "estimated_amount", "notes"
    ])

    # Income calculations
    if not inc_df.empty:
        active_income = inc_df[inc_df["income_type"].str.contains("ประจำ|Active|Fixed", na=False)]["estimated_amount"].sum()
        passive_income = inc_df[inc_df["income_type"].str.contains("ผันแปร|เสริม|Passive|Variable", na=False)]["estimated_amount"].sum()
        total_income = active_income + passive_income
    else:
        active_income = float(profile.get("salary", 65000))
        passive_income = float(profile.get("bonus_or_other_income", 5000)) + float(profile.get("passive_income", 2000))
        total_income = active_income + passive_income

    # Expense calculations
    if not exp_df.empty:
        fixed_sum = exp_df[exp_df["expense_type"].str.contains("คงที่|Fixed", na=False)]["estimated_amount"].sum()
        variable_sum = exp_df[exp_df["expense_type"].str.contains("ผันแปร|Variable", na=False)]["estimated_amount"].sum()
        total_expenses = fixed_sum + variable_sum
    else:
        fixed_sum = float(profile.get("fixed_expenses", 18000))
        variable_sum = float(profile.get("variable_expense_estimate", 16000))
        total_expenses = fixed_sum + variable_sum

    monthly_surplus = total_income - total_expenses
    savings_rate = (monthly_surplus / total_income * 100) if total_income > 0 else 0
    emergency_target_months = int(profile.get("emergency_fund_target_months", 6))
    target_emergency_amount = total_expenses * emergency_target_months
    current_emergency_months = (cash_assets / total_expenses) if total_expenses > 0 else 0
    emergency_progress = min(1.0, (cash_assets / target_emergency_amount)) if target_emergency_amount > 0 else 1.0

    # Top KPI Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card(
            title="รายได้รวม / เดือน",
            value=f"฿{total_income:,.0f}",
            subtext=f"ประจำ ฿{active_income:,.0f} | เสริม ฿{passive_income:,.0f}",
            badge_text=f"{len(inc_df)} แหล่งรายได้",
            badge_type="green"
        )
    with m2:
        render_metric_card(
            title="รวมรายจ่ายประมาณการ",
            value=f"฿{total_expenses:,.0f}",
            subtext=f"คงที่ ฿{fixed_sum:,.0f} | ผันแปร ฿{variable_sum:,.0f}",
            badge_text=f"{(total_expenses/total_income*100):.0f}% ของรายได้" if total_income > 0 else "",
            badge_type="rose"
        )
    with m3:
        surplus_badge = "green" if savings_rate >= 20 else ("amber" if savings_rate > 0 else "rose")
        render_metric_card(
            title="เงินออม/ลงทุนคงเหลือ",
            value=f"฿{monthly_surplus:,.0f}",
            subtext=f"อัตราการออม {savings_rate:.1f}% ต่อเดือน",
            badge_text=f"Savings {savings_rate:.0f}%",
            badge_type=surplus_badge
        )
    with m4:
        ef_badge = "green" if current_emergency_months >= emergency_target_months else "amber"
        render_metric_card(
            title="เงินสำรองฉุกเฉิน",
            value=f"{current_emergency_months:.1f} เดือน",
            subtext=f"เป้าหมาย {emergency_target_months} เดือน (฿{target_emergency_amount:,.0f})",
            badge_text=f"ครอบคลุม {emergency_progress*100:.0f}%",
            badge_type=ef_badge
        )

    # Emergency Fund Progress
    st.markdown(f"**ความพร้อมของเงินสำรองฉุกเฉิน (มีเงินสด ฿{cash_assets:,.0f} จากเป้าหมาย ฿{target_emergency_amount:,.0f})**")
    st.progress(emergency_progress)

    st.markdown("---")

    # Visual Charts Row
    c_pie1, c_pie2 = st.columns(2)
    with c_pie1:
        if not inc_df.empty:
            st.plotly_chart(create_income_donut(inc_df, group_col="category", title="สัดส่วนประมาณการรายได้ตามหมวดหมู่"), use_container_width=True)
        else:
            st.info("ยังไม่มีข้อมูลรายการรายได้")
    with c_pie2:
        if not exp_df.empty:
            st.plotly_chart(create_expense_donut(exp_df, group_col="category", title="สัดส่วนประมาณการรายจ่ายตามหมวดหมู่"), use_container_width=True)
        else:
            st.info("ยังไม่มีข้อมูลรายการรายจ่าย")

    c_flow1, c_flow2 = st.columns(2)
    with c_flow1:
        st.plotly_chart(create_cashflow_waterfall(total_income, fixed_sum, variable_sum, monthly_surplus), use_container_width=True)
        st.caption("💧 **กราฟกระแสเงินสด (Waterfall):** แสดงทางเดินของเงิน เริ่มต้นจากรายได้รวม หักรายจ่ายคงที่และผันแปร จนเหลือเป็นเงินออมสุทธิ")
    with c_flow2:
        st.plotly_chart(create_budget_rule_gauge(total_income, fixed_sum, variable_sum, monthly_surplus), use_container_width=True)
        st.caption("📊 **เกณฑ์ 50/30/20:** เปรียบเทียบสัดส่วนจริงกับเกณฑ์มาตรฐาน (จำเป็น ≤ 50% | ตามใจ ≤ 30% | ออม ≥ 20%)")

    # Comprehensive Explanations Expander
    with st.expander("📖 คำอธิบายตัวชี้วัด & เกณฑ์การจัดสรรเงิน 50/30/20 (Click เพื่อดูรายละเอียด)", expanded=False):
        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown("""
            ##### 💡 ความหมายของตัวเลขสำคัญ (KPIs)
            * **รายได้รวม (Total Income):** ผลรวมของเงินเดือนประจำ (Active) และรายได้เสริม/ปันผล (Passive)
            * **รวมรายจ่ายประมาณการ (Total Expenses):** รวมรายจ่ายคงที่ (เช่น ค่าบ้าน ค่าเดินทาง) + รายจ่ายผันแปร (เช่น อาหาร ช้อปปิ้ง) ในระดับภาพรวม
            * **เงินออม/ลงทุนคงเหลือ (Monthly Surplus):** เงินสุทธิที่เหลือในแต่ละเดือนสำหรับนำไปลงทุนต่อ (รายได้ - รายจ่าย)
            * **เงินสำรองฉุกเฉิน (Emergency Fund):** เงินสดสภาพคล่องที่ควรเตรียมไว้ **3–6 เท่าของรายจ่ายรวม** เพื่อรองรับเหตุไม่คาดฝัน
            """)
        with ec2:
            st.markdown("""
            ##### 🎯 สูตรจัดสรรเงินตามเกณฑ์สากล (50/30/20 Rule)
            * 🔴 **จำเป็น (Needs - ไม่เกิน 50%):** ค่าใช้จ่ายพื้นฐานที่ขาดไม่ได้ (ที่อยู่อาศัย, อาหารหลัก, ค่าน้ำมัน, บิลสาธารณูปโภค, ประกัน)
            * 🟡 **ใช้จ่ายตามใจ (Wants - ไม่เกิน 30%):** ค่าใช้จ่ายเพื่อความสุข (กินเลี้ยง, ช้อปปิ้ง, ท่องเที่ยว, บันเทิง)
            * 🟢 **เงินออม & ลงทุน (Savings - อย่างน้อย 20%):** เงินที่นำไปสะสมเพื่อสร้างอิสรภาพทางการเงิน (DCA หุ้น/กองทุน, พอร์ตเกษียณ)
            """)

    st.markdown("---")

    # ==========================================
    # SECTION 1: ITEMIZE MONTHLY INCOME
    # ==========================================
    st.markdown('<div class="section-header">🟢 ส่วนที่ 1: รายละเอียดประมาณการรายได้ (Itemized Monthly Income)</div>', unsafe_allow_html=True)
    st.caption("บันทึกและจัดการแหล่งรายได้แต่ละรายการ เช่น เงินเดือนประจำ, ค่าฟรีแลนซ์, เงินปันผล, ค่าเช่า")

    tab_inc_view, tab_inc_editor, tab_inc_add, tab_inc_manage = st.tabs([
        "📋 รายการรายได้ทั้งหมด", 
        "📝 แก้ไขตารางด่วน (Table Editor)", 
        "➕ เพิ่มรายการรายได้ใหม่ (Form)", 
        "⚙️ แก้ไข / ลบรายตัว"
    ])

    # Income Tab 1: View
    with tab_inc_view:
        cat_inc_filter = st.selectbox("กรองตามหมวดหมู่รายได้", ["ทั้งหมด"] + INCOME_CATEGORIES, key="filter_inc_cat")
        filtered_inc = inc_df if cat_inc_filter == "ทั้งหมด" else inc_df[inc_df["category"] == cat_inc_filter]

        if not filtered_inc.empty:
            display_inc = filtered_inc.copy()
            display_inc["weight_pct"] = (display_inc["estimated_amount"] / total_income * 100) if total_income > 0 else 0

            formatted_inc = pd.DataFrame({
                "รายการรายได้": display_inc["name"],
                "หมวดหมู่": display_inc["category"],
                "ประเภทรายได้": display_inc["income_type"],
                "ประมาณการต่อเดือน": display_inc["estimated_amount"].apply(lambda x: f"฿{x:,.0f}"),
                "สัดส่วนของรายได้รวม": display_inc["weight_pct"].apply(lambda x: f"{x:.1f}%"),
                "หมายเหตุ": display_inc["notes"]
            })
            st.dataframe(formatted_inc, use_container_width=True, hide_index=True)

            # Mini category summary pills
            cat_inc_summary = inc_df.groupby("category")["estimated_amount"].sum().reset_index()
            st.markdown("##### 📌 สรุปยอดรวมแยกตามหมวดหมู่รายได้:")
            cols_inc_cat = st.columns(len(cat_inc_summary) if len(cat_inc_summary) <= 4 else 4)
            for idx, (_, row) in enumerate(cat_inc_summary.iterrows()):
                with cols_inc_cat[idx % len(cols_inc_cat)]:
                    st.markdown(f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 12px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                        <div style="font-size: 0.78rem; font-weight: 500; color: #64748B;">{row['category']}</div>
                        <div style="font-size: 1.15rem; font-weight: 800; color: #059669; margin-top: 2px;">฿{row['estimated_amount']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("ไม่มีรายการรายได้ในหมวดหมู่นี้")

    # Income Tab 2: Live Table Editor
    with tab_inc_editor:
        st.markdown("##### 📝 แก้ไข/เพิ่ม/ลบ รายได้แบบตารางด่วน (คล้าย Excel)")
        st.caption("ดับเบิลคลิกแก้ไขตัวเลขในช่องตาราง, กดปุ่ม `+` ด้านล่างเพื่อเพิ่มรายการใหม่, หรือติ๊กแถวแล้วกด Delete เพื่อลบ จากนั้นกดปุ่มบันทึกด้านล่าง")
        
        editable_inc_cols = ["id", "name", "category", "income_type", "estimated_amount", "notes"]
        inc_source = inc_df[editable_inc_cols].copy() if not inc_df.empty else pd.DataFrame(columns=editable_inc_cols)

        inc_col_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "name": st.column_config.TextColumn("ชื่อรายการรายได้", required=True),
            "category": st.column_config.SelectboxColumn("หมวดหมู่", options=INCOME_CATEGORIES, required=True),
            "income_type": st.column_config.SelectboxColumn("ประเภทรายได้", options=INCOME_TYPES, required=True),
            "estimated_amount": st.column_config.NumberColumn("ประมาณการต่อเดือน (฿)", min_value=0, format="%.0f", required=True),
            "notes": st.column_config.TextColumn("หมายเหตุ"),
        }

        edited_inc_data = st.data_editor(
            inc_source,
            column_config=inc_col_config,
            num_rows="dynamic",
            use_container_width=True,
            key="income_table_editor"
        )

        if st.button("💾 บันทึกการเปลี่ยนแปลงในตารางรายได้ทั้งหมด", type="primary", use_container_width=True):
            save_income_items_batch(edited_inc_data.to_dict("records"))
            st.toast("บันทึกรายการรายได้เรียบร้อยแล้ว!", icon="💾")
            st.rerun()

    # Income Tab 3: Add Form
    with tab_inc_add:
        with st.form("add_income_form", clear_on_submit=True):
            st.markdown("##### ➕ เพิ่มรายการประมาณการรายได้ใหม่")
            iac1, iac2 = st.columns(2)
            with iac1:
                inc_name = st.text_input("ชื่อรายการรายได้", placeholder="เช่น เงินเดือนประจำ, ค่าสอนพิเศษ, เงินปันผล")
                inc_category = st.selectbox("หมวดหมู่รายได้", INCOME_CATEGORIES)
            with iac2:
                inc_type = st.selectbox("ประเภทรายได้", INCOME_TYPES, help="ประจำ = ได้แน่นอนทุกเดือน, ผันแปร/เสริม = ขึ้นอยู่กับผลงาน/ปันผล")
                inc_amount = st.number_input("ประมาณการรายได้ต่อเดือน (บาท)", min_value=0.0, step=1000.0, format="%.0f")
            
            inc_notes = st.text_input("บันทึกเพิ่มเติม", placeholder="เช่น หักภาษี ณ ที่จ่ายแล้ว, รับทุกวันที่ 25")

            submitted_add_inc = st.form_submit_button("➕ บันทึกรายการรายได้", use_container_width=True, type="primary")
            if submitted_add_inc:
                if not inc_name.strip():
                    st.error("กรุณาระบุชื่อรายการรายได้")
                else:
                    add_income_item({
                        "name": inc_name.strip(),
                        "category": inc_category,
                        "income_type": inc_type,
                        "estimated_amount": inc_amount,
                        "notes": inc_notes.strip()
                    })
                    st.toast(f"เพิ่มรายการรายได้ '{inc_name}' สำเร็จ!", icon="🎉")
                    st.rerun()

    # Income Tab 4: Manage / Delete
    with tab_inc_manage:
        if inc_df.empty:
            st.info("ยังไม่มีรายการรายได้ให้แก้ไข")
        else:
            inc_options = {f"{row['name']} ({row['category']}) - ฿{row['estimated_amount']:,.0f}/ด.": row['id'] for _, row in inc_df.iterrows()}
            selected_inc_label = st.selectbox("เลือกรายการรายได้ที่ต้องการแก้ไขหรือลบ", list(inc_options.keys()))
            selected_inc_id = inc_options[selected_inc_label]
            selected_inc_item = next(i for i in income_items if i["id"] == selected_inc_id)

            with st.form("edit_income_form"):
                st.markdown(f"##### ✏️ แก้ไข: **{selected_inc_item['name']}**")
                iec1, iec2 = st.columns(2)
                with iec1:
                    edit_inc_name = st.text_input("ชื่อรายการรายได้", value=selected_inc_item["name"])
                    edit_inc_cat = st.selectbox("หมวดหมู่", INCOME_CATEGORIES, index=INCOME_CATEGORIES.index(selected_inc_item["category"]) if selected_inc_item["category"] in INCOME_CATEGORIES else 0)
                with iec2:
                    edit_inc_type = st.selectbox("ประเภทรายได้", INCOME_TYPES, index=INCOME_TYPES.index(selected_inc_item["income_type"]) if selected_inc_item["income_type"] in INCOME_TYPES else 0)
                    edit_inc_amount = st.number_input("ประมาณการต่อเดือน (บาท)", min_value=0.0, value=float(selected_inc_item["estimated_amount"]), step=1000.0, format="%.0f")
                
                edit_inc_notes = st.text_input("หมายเหตุ", value=selected_inc_item["notes"] or "")

                col_btn_i1, col_btn_i2 = st.columns(2)
                with col_btn_i1:
                    submitted_inc_edit = st.form_submit_button("💾 บันทึกการแก้ไข", use_container_width=True, type="primary")
                with col_btn_i2:
                    submitted_inc_del = st.form_submit_button("🗑️ ลบรายการนี้", use_container_width=True)

                if submitted_inc_edit:
                    update_income_item(selected_inc_id, {
                        "name": edit_inc_name.strip(),
                        "category": edit_inc_cat,
                        "income_type": edit_inc_type,
                        "estimated_amount": edit_inc_amount,
                        "notes": edit_inc_notes.strip()
                    })
                    st.toast("อัปเดตรายการรายได้สำเร็จ!", icon="✅")
                    st.rerun()

                if submitted_inc_del:
                    delete_income_item(selected_inc_id)
                    st.toast("ลบรายการรายได้เรียบร้อย", icon="🗑️")
                    st.rerun()

    st.markdown("---")

    # ==========================================
    # SECTION 2: ITEMIZE MONTHLY EXPENSES
    # ==========================================
    st.markdown('<div class="section-header">🔴 ส่วนที่ 2: รายละเอียดประมาณการรายจ่าย (Itemized Monthly Expenses)</div>', unsafe_allow_html=True)
    st.caption("แจกแจงค่าใช้จ่ายแต่ละรายการ แยกตามประเภท 'คงที่ (Fixed)' และ 'ผันแปร (Variable)' เพื่อการวางแผนที่แม่นยำ")

    tab_exp_view, tab_exp_editor, tab_exp_add, tab_exp_manage = st.tabs([
        "📋 รายการรายจ่ายทั้งหมด", 
        "📝 แก้ไขตารางด่วน (Table Editor)", 
        "➕ เพิ่มรายการรายจ่ายใหม่ (Form)", 
        "⚙️ แก้ไข / ลบรายตัว"
    ])

    # Expense Tab 1: View Table
    with tab_exp_view:
        cat_exp_filter = st.selectbox("กรองตามหมวดหมู่รายจ่าย", ["ทั้งหมด"] + EXPENSE_CATEGORIES, key="filter_exp_cat")
        filtered_exp = exp_df if cat_exp_filter == "ทั้งหมด" else exp_df[exp_df["category"] == cat_exp_filter]

        if not filtered_exp.empty:
            display_exp = filtered_exp.copy()
            display_exp["weight_pct"] = (display_exp["estimated_amount"] / total_expenses * 100) if total_expenses > 0 else 0

            formatted_exp = pd.DataFrame({
                "รายการรายจ่าย": display_exp["name"],
                "หมวดหมู่": display_exp["category"],
                "ประเภทรายจ่าย": display_exp["expense_type"],
                "ประมาณการต่อเดือน": display_exp["estimated_amount"].apply(lambda x: f"฿{x:,.0f}"),
                "สัดส่วนของรายจ่ายรวม": display_exp["weight_pct"].apply(lambda x: f"{x:.1f}%"),
                "หมายเหตุ": display_exp["notes"]
            })
            st.dataframe(formatted_exp, use_container_width=True, hide_index=True)

            # Mini category summary pills
            cat_summary = exp_df.groupby("category")["estimated_amount"].sum().reset_index()
            st.markdown("##### 📌 สรุปยอดรวมแยกตามหมวดหมู่รายจ่าย:")
            cols_cat = st.columns(len(cat_summary) if len(cat_summary) <= 4 else 4)
            for idx, (_, row) in enumerate(cat_summary.iterrows()):
                with cols_cat[idx % len(cols_cat)]:
                    st.markdown(f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 12px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                        <div style="font-size: 0.78rem; font-weight: 500; color: #64748B;">{row['category']}</div>
                        <div style="font-size: 1.15rem; font-weight: 800; color: #E11D48; margin-top: 2px;">฿{row['estimated_amount']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("ไม่มีรายการรายจ่ายในหมวดหมู่นี้")

    # Expense Tab 2: Live Table Editor
    with tab_exp_editor:
        st.markdown("##### 📝 แก้ไข/เพิ่ม/ลบ รายจ่ายแบบตารางด่วน (คล้าย Excel)")
        st.caption("ดับเบิลคลิกแก้ไขตัวเลขในช่องตาราง, กดปุ่ม `+` ด้านล่างเพื่อเพิ่มรายการใหม่, หรือติ๊กแถวแล้วกด Delete เพื่อลบ จากนั้นกดปุ่มบันทึกด้านล่าง")
        
        editable_exp_cols = ["id", "name", "category", "expense_type", "estimated_amount", "notes"]
        exp_source = exp_df[editable_exp_cols].copy() if not exp_df.empty else pd.DataFrame(columns=editable_exp_cols)

        exp_col_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "name": st.column_config.TextColumn("ชื่อรายการรายจ่าย", required=True),
            "category": st.column_config.SelectboxColumn("หมวดหมู่", options=EXPENSE_CATEGORIES, required=True),
            "expense_type": st.column_config.SelectboxColumn("ประเภทรายจ่าย", options=EXPENSE_TYPES, required=True),
            "estimated_amount": st.column_config.NumberColumn("ประมาณการต่อเดือน (฿)", min_value=0, format="%.0f", required=True),
            "notes": st.column_config.TextColumn("หมายเหตุ"),
        }

        edited_exp_data = st.data_editor(
            exp_source,
            column_config=exp_col_config,
            num_rows="dynamic",
            use_container_width=True,
            key="expense_table_editor"
        )

        if st.button("💾 บันทึกการเปลี่ยนแปลงในตารางรายจ่ายทั้งหมด", type="primary", use_container_width=True):
            save_expense_items_batch(edited_exp_data.to_dict("records"))
            st.toast("บันทึกรายการรายจ่ายเรียบร้อยแล้ว!", icon="💾")
            st.rerun()

    # Expense Tab 3: Add Form
    with tab_exp_add:
        with st.form("add_expense_form", clear_on_submit=True):
            st.markdown("##### ➕ เพิ่มรายการประมาณการรายจ่ายใหม่")
            eac1, eac2 = st.columns(2)
            with eac1:
                item_name = st.text_input("ชื่อรายการรายจ่าย (เช่น ค่าอาหาร, ค่าผ่อนรถ, ค่าเน็ต, ค่าน้ำไฟ)", placeholder="เช่น ค่ากาแฟ & เครื่องดื่ม")
                item_category = st.selectbox("หมวดหมู่รายจ่าย", EXPENSE_CATEGORIES)
            with eac2:
                item_type = st.selectbox("ประเภทรายจ่าย", EXPENSE_TYPES, help="คงที่ = ค่าใช้จ่ายที่ต้องจ่ายแน่นอนทุกเดือน, ผันแปร = ค่าใช้จ่ายกินอยู่ ยืดหยุ่นได้")
                item_amount = st.number_input("ประมาณการค่าใช้จ่ายต่อเดือน (บาท)", min_value=0.0, step=500.0, format="%.0f")
            
            item_notes = st.text_input("บันทึกเพิ่มเติม", placeholder="เช่น เฉลี่ยวันละ 100 บาท, ชำระผ่านบัตรเครดิต")

            submitted_add_exp = st.form_submit_button("➕ บันทึกรายการรายจ่าย", use_container_width=True, type="primary")
            if submitted_add_exp:
                if not item_name.strip():
                    st.error("กรุณาระบุชื่อรายการรายจ่าย")
                else:
                    add_expense_item({
                        "name": item_name.strip(),
                        "category": item_category,
                        "expense_type": item_type,
                        "estimated_amount": item_amount,
                        "notes": item_notes.strip()
                    })
                    st.toast(f"เพิ่มรายการ '{item_name}' สำเร็จ!", icon="🎉")
                    st.rerun()

    # Expense Tab 4: Manage / Delete
    with tab_exp_manage:
        if exp_df.empty:
            st.info("ยังไม่มีรายการรายจ่ายให้แก้ไข")
        else:
            exp_options = {f"{row['name']} ({row['category']}) - ฿{row['estimated_amount']:,.0f}/ด.": row['id'] for _, row in exp_df.iterrows()}
            selected_exp_label = st.selectbox("เลือกรายการที่ต้องการแก้ไขหรือลบ", list(exp_options.keys()))
            selected_exp_id = exp_options[selected_exp_label]
            selected_exp_item = next(e for e in expense_items if e["id"] == selected_exp_id)

            with st.form("edit_expense_form"):
                st.markdown(f"##### ✏️ แก้ไข: **{selected_exp_item['name']}**")
                eec1, eec2 = st.columns(2)
                with eec1:
                    edit_exp_name = st.text_input("ชื่อรายการรายจ่าย", value=selected_exp_item["name"])
                    edit_exp_cat = st.selectbox("หมวดหมู่", EXPENSE_CATEGORIES, index=EXPENSE_CATEGORIES.index(selected_exp_item["category"]) if selected_exp_item["category"] in EXPENSE_CATEGORIES else 0)
                with eec2:
                    edit_exp_type = st.selectbox("ประเภทรายจ่าย", EXPENSE_TYPES, index=EXPENSE_TYPES.index(selected_exp_item["expense_type"]) if selected_exp_item["expense_type"] in EXPENSE_TYPES else 0)
                    edit_exp_amount = st.number_input("ประมาณการต่อเดือน (บาท)", min_value=0.0, value=float(selected_exp_item["estimated_amount"]), step=500.0, format="%.0f")
                
                edit_exp_notes = st.text_input("หมายเหตุ", value=selected_exp_item["notes"] or "")

                col_btn_e1, col_btn_e2 = st.columns(2)
                with col_btn_e1:
                    submitted_exp_edit = st.form_submit_button("💾 บันทึกการแก้ไข", use_container_width=True, type="primary")
                with col_btn_e2:
                    submitted_exp_del = st.form_submit_button("🗑️ ลบรายการนี้", use_container_width=True)

                if submitted_exp_edit:
                    update_expense_item(selected_exp_id, {
                        "name": edit_exp_name.strip(),
                        "category": edit_exp_cat,
                        "expense_type": edit_exp_type,
                        "estimated_amount": edit_exp_amount,
                        "notes": edit_exp_notes.strip()
                    })
                    st.toast("อัปเดตรายการรายจ่ายสำเร็จ!", icon="✅")
                    st.rerun()

                if submitted_exp_del:
                    delete_expense_item(selected_exp_id)
                    st.toast("ลบรายการรายจ่ายเรียบร้อย", icon="🗑️")
                    st.rerun()

    # ==========================================
    # SECTION 3: EMERGENCY FUND & SNAPSHOT
    # ==========================================
    st.markdown("---")
    st.markdown('<div class="section-header">⚙️ ตั้งค่าเป้าหมาย & บันทึก Snapshot</div>', unsafe_allow_html=True)
    
    col_set1, col_set2 = st.columns([2, 2])
    with col_set1:
        new_ef_target = st.slider(
            "เป้าหมายเงินสำรองฉุกเฉิน (เดือน)",
            min_value=3,
            max_value=12,
            value=emergency_target_months,
            step=1
        )
        if new_ef_target != emergency_target_months:
            update_data = {
                "salary": total_income,
                "bonus_or_other_income": 0,
                "passive_income": 0,
                "fixed_expenses": fixed_sum,
                "variable_expense_estimate": variable_sum,
                "emergency_fund_target_months": new_ef_target,
                "fire_target_monthly_spend": profile.get("fire_target_monthly_spend", 35000),
                "fire_expected_return": profile.get("fire_expected_return", 7.0),
                "fire_inflation_rate": profile.get("fire_inflation_rate", 2.5),
                "fire_current_age": profile.get("fire_current_age", 29),
                "fire_target_age": profile.get("fire_target_age", 50)
            }
            update_monthly_profile(update_data)
            st.rerun()

    with col_set2:
        current_ym = datetime.now().strftime("%Y-%m")
        st.markdown(f"**📸 บันทึก Snapshot ข้อมูลประจำเดือน ({current_ym})**")
        st.caption("บันทึกยอดรายได้, รายจ่าย, สินทรัพย์ และหนี้สินปัจจุบันลงในสถิติย้อนหลัง")
        if st.button("📸 บันทึก Snapshot ประจำเดือนนี้", use_container_width=True, type="primary"):
            save_snapshot({
                "snapshot_month": current_ym,
                "income": total_income,
                "expenses": total_expenses,
                "savings_invested": monthly_surplus,
                "total_assets": total_assets,
                "total_debts": total_liabilities,
                "net_worth": net_worth,
                "notes": f"รายได้ ฿{total_income:,.0f} | รายจ่าย ฿{total_expenses:,.0f} | ออม {savings_rate:.1f}%"
            })
            st.toast(f"บันทึก Snapshot เดือน {current_ym} สำเร็จ!", icon="✨")
            st.rerun()
