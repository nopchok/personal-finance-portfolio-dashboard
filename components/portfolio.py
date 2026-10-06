"""
Investment Portfolio & Fixed Assets Module
Handles two distinct asset classes:
1. Liquid Investments (Mutual Funds, Stocks, Crypto, Cash, Gold/Commodities) with Target Allocation, Rebalancing, and DCA.
2. Real Estate & Fixed Assets (Houses, Condos, Land, Vehicles, Buildings) for Net Worth tracking.
"""

import streamlit as st
import pandas as pd
from database import (
    get_all_assets, add_asset, update_asset, delete_asset, get_categories,
    get_connection, safe_float, safe_str
)
from components.styles import render_metric_card
from components.charts import create_allocation_donut, create_target_vs_actual_chart

def render_portfolio():
    INVESTMENT_CATS = get_categories("asset")
    FIXED_ASSET_CATS = get_categories("fixed_asset")
    
    all_assets = get_all_assets()
    
    # Helper to determine asset type
    def is_fixed(a):
        if a.get("asset_type") == "fixed_asset":
            return True
        cat = str(a.get("category", ""))
        name = str(a.get("name", ""))
        return any(k in cat for k in ["บ้าน", "คอนโด", "ที่ดิน", "อสังหา", "สิ่งปลูกสร้าง", "Real Estate", "รถยนต์", "Vehicle"]) or \
               any(k in name for k in ["บ้าน", "คอนโด", "ที่ดิน"])

    liquid_assets = [a for a in all_assets if not is_fixed(a)]
    fixed_assets = [a for a in all_assets if is_fixed(a)]

    liquid_df = pd.DataFrame(liquid_assets) if liquid_assets else pd.DataFrame(columns=[
        "id", "name", "category", "current_value", "cost_basis",
        "target_allocation", "monthly_dca", "expected_roi", "platform_or_broker", "notes", "asset_type"
    ])

    fixed_df = pd.DataFrame(fixed_assets) if fixed_assets else pd.DataFrame(columns=[
        "id", "name", "category", "current_value", "cost_basis",
        "target_allocation", "monthly_dca", "expected_roi", "platform_or_broker", "notes", "asset_type"
    ])

    st.markdown('<div class="section-header">📈 พอร์ตสินทรัพย์ & การลงทุน (Portfolio & Assets)</div>', unsafe_allow_html=True)
    st.caption("บริหารจัดการและติดตามสินทรัพย์แยกเป็น 2 ส่วน: พอร์ตลงทุนสภาพคล่อง (หุ้น/กองทุน/คริปโต) และ สินทรัพย์ถาวร (บ้าน/ที่ดิน/รถยนต์)")

    # Top Level Tabs
    tab_liquid, tab_fixed = st.tabs([
        "💼 1. พอร์ตการลงทุนสภาพคล่อง (Liquid Investments)",
        "🏠 2. สินทรัพย์ถาวร & อสังหาริมทรัพย์ (Real Estate & Fixed Assets)"
    ])

    # =========================================================================
    # SECTION 1: LIQUID INVESTMENTS
    # =========================================================================
    with tab_liquid:
        st.markdown("#### 💼 พอร์ตการลงทุนสภาพคล่อง & การจัดสรรสินทรัพย์ (Asset Allocation)")
        st.caption("สินทรัพย์ที่สร้างผลตอบแทน สภาพคล่องสูง และนำไปใช้คำนวณเป้าหมายเกษียณ (FIRE Number)")

        total_liq_val = liquid_df["current_value"].sum() if not liquid_df.empty else 0
        total_liq_cost = liquid_df["cost_basis"].sum() if not liquid_df.empty else 0
        total_liq_pnl = total_liq_val - total_liq_cost
        liq_pnl_pct = (total_liq_pnl / total_liq_cost * 100) if total_liq_cost > 0 else 0
        total_liq_dca = liquid_df["monthly_dca"].sum() if not liquid_df.empty else 0

        # KPI Row
        lcol1, lcol2, lcol3, lcol4 = st.columns(4)
        with lcol1:
            render_metric_card(
                title="มูลค่าพอร์ตลงทุนรวม",
                value=f"฿{total_liq_val:,.0f}",
                subtext=f"จำนวน {len(liquid_df)} รายการลงทุน",
                badge_text="Liquid Assets",
                badge_type="indigo"
            )
        with lcol2:
            render_metric_card(
                title="เงินต้นทุนรวม (Cost Basis)",
                value=f"฿{total_liq_cost:,.0f}",
                subtext="เงินลงทุนสะสมทั้งหมด",
                badge_text="Invested",
                badge_type="cyan"
            )
        with lcol3:
            pnl_badge = "green" if total_liq_pnl >= 0 else "rose"
            pnl_sign = "+" if total_liq_pnl >= 0 else ""
            render_metric_card(
                title="กำไร/ขาดทุนรวม (P&L)",
                value=f"{pnl_sign}฿{total_liq_pnl:,.0f}",
                subtext=f"{pnl_sign}{liq_pnl_pct:.2f}% จากต้นทุน",
                badge_text=f"{pnl_sign}{liq_pnl_pct:.1f}%",
                badge_type=pnl_badge
            )
        with lcol4:
            render_metric_card(
                title="แผน DCA รายเดือน",
                value=f"฿{total_liq_dca:,.0f}",
                subtext="เงินลงทุนเพิ่มต่อเดือน",
                badge_text="Monthly DCA",
                badge_type="amber"
            )

        # Charts Row
        st.markdown("---")
        lc1, lc2 = st.columns(2)
        with lc1:
            if not liquid_df.empty and total_liq_val > 0:
                st.plotly_chart(create_allocation_donut(liquid_df, group_col="category", title="สัดส่วนตามประเภทสินทรัพย์ลงทุน"), use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลสินทรัพย์ลงทุนสภาพคล่อง")
        with lc2:
            if not liquid_df.empty and total_liq_val > 0:
                cat_summary = liquid_df.groupby("category").agg({
                    "current_value": "sum",
                    "target_allocation": "sum"
                }).reset_index()
                cat_summary["actual_pct"] = (cat_summary["current_value"] / total_liq_val) * 100
                cat_summary["target_pct"] = cat_summary["target_allocation"]
                cat_summary["diff_pct"] = cat_summary["actual_pct"] - cat_summary["target_pct"]
                st.plotly_chart(create_target_vs_actual_chart(cat_summary), use_container_width=True)
            else:
                st.info("เพิ่มรายการสินทรัพย์เพื่อแสดงกราฟเปรียบเทียบสัดส่วนเป้าหมาย")

        # Rebalancing Suggestions
        if not liquid_df.empty and total_liq_val > 0:
            with st.expander("⚖️ ข้อเสนอแนะการปรับสมดุลพอร์ตลงทุน (Portfolio Rebalancing Suggestions)", expanded=False):
                cat_df = liquid_df.groupby("category").agg({
                    "current_value": "sum",
                    "target_allocation": "sum"
                }).reset_index()
                cat_df["actual_pct"] = (cat_df["current_value"] / total_liq_val) * 100
                cat_df["target_pct"] = cat_df["target_allocation"]
                cat_df["target_value"] = total_liq_val * (cat_df["target_pct"] / 100.0)
                cat_df["rebalance_needed"] = cat_df["target_value"] - cat_df["current_value"]
                
                rebal_cols = st.columns(max(1, len(cat_df)))
                for i, (_, row) in enumerate(cat_df.iterrows()):
                    with rebal_cols[i % len(rebal_cols)]:
                        diff = row["rebalance_needed"]
                        status = "🎯 พอดีเป้าหมาย"
                        status_color = "#10B981"
                        if diff > 1000:
                            status = f"➕ ควรเติมเงิน ฿{abs(diff):,.0f}"
                            status_color = "#38BDF8"
                        elif diff < -1000:
                            status = f"➖ เกินเป้าหมาย ฿{abs(diff):,.0f}"
                            status_color = "#F59E0B"
                        
                        st.markdown(f"""
                        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 10px; border-left: 4px solid {status_color}; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">
                            <div style="font-weight: 700; font-size: 0.85rem; color: #0F172A;">{row['category']}</div>
                            <div style="font-size: 0.78rem; color: #64748B;">ปัจจุบัน {row['actual_pct']:.1f}% | เป้าหมาย {row['target_pct']:.1f}%</div>
                            <div style="font-size: 0.82rem; font-weight: 700; color: {status_color}; margin-top: 4px;">{status}</div>
                        </div>
                        """, unsafe_allow_html=True)

        # Educational Expander for Portfolio
        with st.expander("📖 คำอธิบาย: สัดส่วนเป้าหมาย (Target %) & การปรับสมดุลพอร์ต (Rebalancing)", expanded=False):
            st.markdown("""
            * 🎯 **สัดส่วนเป้าหมาย (Target Allocation %):** คือ สัดส่วนในอุดมคติที่เราต้องการถือครองเพื่อควบคุมความเสี่ยง (เช่น หุ้น 50%, คริปโต 20%, กองทุน 20%, เงินสด 10%)
            * 📊 **สัดส่วนจริง (Actual %):** คือ เปอร์เซ็นต์มูลค่าเงินจริง ณ วันนี้ ซึ่งจะขยับขึ้นลงตามราคาตลาด
            * ⚖️ **การปรับสมดุลพอร์ต (Rebalancing):** เมื่อสินทรัพย์ใดราคาขึ้นเยอะจนสัดส่วน **เกินเป้า (Overweight)** ระบบจะแนะนำให้ชะลอการซื้อหรือขายทำกำไร และนำเงินไปซื้อสินทรัพย์ที่ **ต่ำกว่าเป้า (Underweight)** เพื่อรักษาวินัยการลงทุน
            * 💵 **DCA (Dollar-Cost Averaging):** ยอดเงินที่ตั้งใจจะทยอยซื้อสะสมในแต่ละเดือนอย่างสม่ำเสมอ
            """)

        st.markdown("---")

        # Inner Sub-tabs for Liquid Assets
        t_liq_view, t_liq_edit, t_liq_add, t_liq_manage = st.tabs([
            "📋 รายการสินทรัพย์ลงทุน", 
            "📝 แก้ไขตารางด่วน (Table Editor)",
            "➕ เพิ่มสินทรัพย์ลงทุน (Form)", 
            "⚙️ แก้ไข / ลบรายตัว"
        ])

        with t_liq_view:
            liq_cat_filter = st.selectbox("กรองตามหมวดหมู่ลงทุน", ["ทั้งหมด"] + INVESTMENT_CATS, key="filter_liq_cat")
            filtered_liq = liquid_df if liq_cat_filter == "ทั้งหมด" else liquid_df[liquid_df["category"] == liq_cat_filter]

            if not filtered_liq.empty:
                disp_liq = filtered_liq.copy()
                disp_liq["pnl"] = disp_liq["current_value"] - disp_liq["cost_basis"]
                disp_liq["pnl_pct"] = (disp_liq["pnl"] / disp_liq["cost_basis"] * 100).fillna(0)
                disp_liq["weight_pct"] = (disp_liq["current_value"] / total_liq_val * 100) if total_liq_val > 0 else 0

                formatted_liq = pd.DataFrame({
                    "ชื่อสินทรัพย์": disp_liq["name"],
                    "หมวดหมู่": disp_liq["category"],
                    "โบรกเกอร์/แพลตฟอร์ม": disp_liq["platform_or_broker"],
                    "มูลค่าปัจจุบัน": disp_liq["current_value"].apply(lambda x: f"฿{x:,.0f}"),
                    "เงินต้นทุน": disp_liq["cost_basis"].apply(lambda x: f"฿{x:,.0f}"),
                    "กำไร/ขาดทุน": disp_liq["pnl"].apply(lambda x: f"{'+' if x>=0 else ''}฿{x:,.0f}"),
                    "กำไร/ขาดทุน (%)": disp_liq["pnl_pct"].apply(lambda x: f"{'+' if x>=0 else ''}{x:.2f}%"),
                    "สัดส่วนในพอร์ต": disp_liq["weight_pct"].apply(lambda x: f"{x:.1f}%"),
                    "เป้าหมาย (%)": disp_liq["target_allocation"].apply(lambda x: f"{x:.1f}%"),
                    "DCA/เดือน": disp_liq["monthly_dca"].apply(lambda x: f"฿{x:,.0f}" if x>0 else "-"),
                    "หมายเหตุ": disp_liq["notes"]
                })
                st.dataframe(formatted_liq, use_container_width=True, hide_index=True)
            else:
                st.info("ไม่มีรายการสินทรัพย์ในหมวดหมู่นี้")

        with t_liq_edit:
            st.markdown("##### 📝 แก้ไข/เพิ่ม/ลบ สินทรัพย์ลงทุนแบบตารางด่วน")
            st.caption("ดับเบิลคลิกแก้ไขตัวเลขในช่องตาราง, กดปุ่ม `+` เพื่อเพิ่มแถวใหม่ หรือติ๊กแถวแล้วกด Delete เพื่อลบ")
            
            editable_cols = ["id", "name", "category", "current_value", "cost_basis", "target_allocation", "monthly_dca", "expected_roi", "platform_or_broker", "notes"]
            edit_liq_df = liquid_df[editable_cols].copy() if not liquid_df.empty else pd.DataFrame(columns=editable_cols)
            
            column_config = {
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "name": st.column_config.TextColumn("ชื่อสินทรัพย์", required=True),
                "category": st.column_config.SelectboxColumn("หมวดหมู่", options=INVESTMENT_CATS, required=True),
                "current_value": st.column_config.NumberColumn("มูลค่าปัจจุบัน (฿)", min_value=0, format="%.0f"),
                "cost_basis": st.column_config.NumberColumn("เงินต้นทุน (฿)", min_value=0, format="%.0f"),
                "target_allocation": st.column_config.NumberColumn("เป้าหมาย (%)", min_value=0, max_value=100, format="%.1f%%"),
                "monthly_dca": st.column_config.NumberColumn("DCA/เดือน (฿)", min_value=0, format="%.0f"),
                "expected_roi": st.column_config.NumberColumn("ผลตอบแทน (%/ปี)", format="%.1f%%"),
                "platform_or_broker": st.column_config.TextColumn("โบรกเกอร์/แพลตฟอร์ม"),
                "notes": st.column_config.TextColumn("หมายเหตุ"),
            }

            edited_liq = st.data_editor(
                edit_liq_df,
                column_config=column_config,
                num_rows="dynamic",
                use_container_width=True,
                key="liq_table_editor"
            )

            if st.button("💾 บันทึกการเปลี่ยนแปลงพอร์ตลงทุนทั้งหมด", type="primary", use_container_width=True):
                conn = get_connection()
                c = conn.cursor()
                
                saved_liq_ids = []
                for _, r in edited_liq.iterrows():
                    asset_name = safe_str(r.get("name"))
                    if not asset_name:
                        continue
                    row_id = safe_float(r.get("id"), 0)
                    if row_id > 0:
                        c.execute("""
                        INSERT OR REPLACE INTO assets (id, name, category, current_value, cost_basis, target_allocation, monthly_dca, expected_roi, platform_or_broker, notes, asset_type, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'investment', CURRENT_TIMESTAMP)
                        """, (
                            int(row_id),
                            asset_name,
                            safe_str(r.get("category"), INVESTMENT_CATS[0] if INVESTMENT_CATS else "กองทุนรวม (Mutual Funds)"),
                            safe_float(r.get("current_value"), 0.0),
                            safe_float(r.get("cost_basis"), 0.0),
                            safe_float(r.get("target_allocation"), 0.0),
                            safe_float(r.get("monthly_dca"), 0.0),
                            safe_float(r.get("expected_roi"), 7.0),
                            safe_str(r.get("platform_or_broker"), ""),
                            safe_str(r.get("notes"), "")
                        ))
                        saved_liq_ids.append(int(row_id))
                    else:
                        c.execute("""
                        INSERT INTO assets (name, category, current_value, cost_basis, target_allocation, monthly_dca, expected_roi, platform_or_broker, notes, asset_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'investment')
                        """, (
                            asset_name,
                            safe_str(r.get("category"), INVESTMENT_CATS[0] if INVESTMENT_CATS else "กองทุนรวม (Mutual Funds)"),
                            safe_float(r.get("current_value"), 0.0),
                            safe_float(r.get("cost_basis"), 0.0),
                            safe_float(r.get("target_allocation"), 0.0),
                            safe_float(r.get("monthly_dca"), 0.0),
                            safe_float(r.get("expected_roi"), 7.0),
                            safe_str(r.get("platform_or_broker"), ""),
                            safe_str(r.get("notes"), "")
                        ))
                        saved_liq_ids.append(c.lastrowid)
                
                # Delete removed liquid assets only
                current_liq_ids = [a["id"] for a in liquid_assets]
                to_delete = [lid for lid in current_liq_ids if lid not in saved_liq_ids]
                if to_delete:
                    del_ph = ','.join(['?'] * len(to_delete))
                    c.execute(f"DELETE FROM assets WHERE id IN ({del_ph})", to_delete)

                conn.commit()
                conn.close()
                st.toast("บันทึกข้อมูลพอร์ตลงทุนเรียบร้อยแล้ว!", icon="💾")
                st.rerun()

        with t_liq_add:
            with st.form("add_liq_asset_form", clear_on_submit=True):
                st.markdown("##### ➕ เพิ่มรายการสินทรัพย์ลงทุนใหม่")
                ac1, ac2 = st.columns(2)
                with ac1:
                    name = st.text_input("ชื่อสินทรัพย์ (เช่น SCBWORLD, BTC, PTT, กองทุน RMF, เงินฝาก Dime)", placeholder="เช่น US Tech ETF (QQQ)")
                    category = st.selectbox("หมวดหมู่การลงทุน", INVESTMENT_CATS)
                    current_value = st.number_input("มูลค่าปัจจุบัน (บาท)", min_value=0.0, step=1000.0, format="%.0f")
                    cost_basis = st.number_input("ต้นทุนรวมที่ซื้อ (บาท)", min_value=0.0, step=1000.0, format="%.0f")
                with ac2:
                    target_allocation = st.number_input("สัดส่วนเป้าหมายในพอร์ต (%)", min_value=0.0, max_value=100.0, step=1.0, value=10.0)
                    monthly_dca = st.number_input("แผนซื้อ DCA รายเดือน (บาท)", min_value=0.0, step=500.0, format="%.0f", value=0.0)
                    expected_roi = st.number_input("ผลตอบแทนคาดหวังต่อปี (% ต่อปี)", min_value=-50.0, max_value=200.0, step=0.5, value=7.0)
                    platform = st.text_input("แพลตฟอร์ม / โบรกเกอร์", placeholder="เช่น InnovestX, Dime, Streaming, Bitkub")
                    notes = st.text_input("บันทึกเพิ่มเติม / กลยุทธ์", placeholder="เช่น ถือยาวรับปันผล, DCA ทุกวันที่ 25")

                submitted_liq_add = st.form_submit_button("➕ บันทึกสินทรัพย์ลงทุน", use_container_width=True, type="primary")
                if submitted_liq_add:
                    if not name.strip():
                        st.error("กรุณาระบุชื่อสินทรัพย์")
                    else:
                        add_asset({
                            "name": name.strip(),
                            "category": category,
                            "current_value": current_value,
                            "cost_basis": cost_basis,
                            "target_allocation": target_allocation,
                            "monthly_dca": monthly_dca,
                            "expected_roi": expected_roi,
                            "platform_or_broker": platform.strip(),
                            "notes": notes.strip(),
                            "asset_type": "investment"
                        })
                        st.toast(f"เพิ่ม '{name}' ลงในพอร์ตลงทุนเรียบร้อยแล้ว!", icon="🎉")
                        st.rerun()

        with t_liq_manage:
            if liquid_df.empty:
                st.info("ยังไม่มีสินทรัพย์ลงทุนให้แก้ไข")
            else:
                asset_options = {f"{row['name']} ({row['category']}) - ฿{row['current_value']:,.0f}": row['id'] for _, row in liquid_df.iterrows()}
                selected_label = st.selectbox("เลือกรายการที่ต้องการแก้ไขหรือลบ", list(asset_options.keys()), key="sel_liq_edit")
                selected_id = asset_options[selected_label]
                selected_asset = next(a for a in liquid_assets if a["id"] == selected_id)

                with st.form("edit_liq_asset_form"):
                    st.markdown(f"##### ✏️ แก้ไข: **{selected_asset['name']}**")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        edit_name = st.text_input("ชื่อสินทรัพย์", value=selected_asset["name"])
                        edit_category = st.selectbox("หมวดหมู่", INVESTMENT_CATS, index=INVESTMENT_CATS.index(selected_asset["category"]) if selected_asset["category"] in INVESTMENT_CATS else 0)
                        edit_current_val = st.number_input("มูลค่าปัจจุบัน (บาท)", min_value=0.0, value=float(selected_asset["current_value"]), step=1000.0, format="%.0f")
                        edit_cost = st.number_input("ต้นทุนรวม (บาท)", min_value=0.0, value=float(selected_asset["cost_basis"]), step=1000.0, format="%.0f")
                    with ec2:
                        edit_target = st.number_input("สัดส่วนเป้าหมาย (%)", min_value=0.0, max_value=100.0, value=float(selected_asset["target_allocation"]), step=1.0)
                        edit_dca = st.number_input("แผน DCA รายเดือน (บาท)", min_value=0.0, value=float(selected_asset["monthly_dca"]), step=500.0, format="%.0f")
                        edit_roi = st.number_input("ผลตอบแทนคาดหวัง (%/ปี)", min_value=-50.0, max_value=200.0, value=float(selected_asset["expected_roi"]), step=0.5)
                        edit_platform = st.text_input("แพลตฟอร์ม/โบรกเกอร์", value=selected_asset["platform_or_broker"] or "")
                        edit_notes = st.text_input("บันทึกเพิ่มเติม", value=selected_asset["notes"] or "")

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        submitted_edit = st.form_submit_button("💾 บันทึกการแก้ไข", use_container_width=True, type="primary")
                    with col_btn2:
                        submitted_delete = st.form_submit_button("🗑️ ลบสินทรัพย์นี้", use_container_width=True)

                    if submitted_edit:
                        update_asset(selected_id, {
                            "name": edit_name.strip(),
                            "category": edit_category,
                            "current_value": edit_current_val,
                            "cost_basis": edit_cost,
                            "target_allocation": edit_target,
                            "monthly_dca": edit_dca,
                            "expected_roi": edit_roi,
                            "platform_or_broker": edit_platform.strip(),
                            "notes": edit_notes.strip(),
                            "asset_type": "investment"
                        })
                        st.toast("อัปเดตข้อมูลสินทรัพย์สำเร็จ!", icon="✅")
                        st.rerun()

                    if submitted_delete:
                        delete_asset(selected_id)
                        st.toast("ลบรายการสินทรัพย์เรียบร้อยแล้ว", icon="🗑️")
                        st.rerun()

    # =========================================================================
    # SECTION 2: FIXED ASSETS & REAL ESTATE
    # =========================================================================
    with tab_fixed:
        st.markdown("#### 🏠 สินทรัพย์ถาวร & อสังหาริมทรัพย์ (Real Estate & Fixed Assets)")
        st.caption("บันทึกบ้าน, คอนโด, ที่ดิน, สิ่งปลูกสร้าง, ยานพาหนะ หรือของสะสมมีค่าเพื่อนับรวมในงบดุลความมั่งคั่งสุทธิ (Net Worth)")

        total_fix_val = fixed_df["current_value"].sum() if not fixed_df.empty else 0
        total_fix_cost = fixed_df["cost_basis"].sum() if not fixed_df.empty else 0
        total_fix_gain = total_fix_val - total_fix_cost
        fix_gain_pct = (total_fix_gain / total_fix_cost * 100) if total_fix_cost > 0 else 0

        # KPI Cards for Fixed Assets
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            render_metric_card(
                title="มูลค่าประเมินรวม",
                value=f"฿{total_fix_val:,.0f}",
                subtext=f"จำนวน {len(fixed_df)} รายการ",
                badge_text="Real Estate",
                badge_type="indigo"
            )
        with fcol2:
            render_metric_card(
                title="ราคาซื้อ / ต้นทุนเดิม",
                value=f"฿{total_fix_cost:,.0f}",
                subtext="เงินต้นทุนที่ซื้อมา",
                badge_text="Cost Basis",
                badge_type="cyan"
            )
        with fcol3:
            gain_badge = "green" if total_fix_gain >= 0 else "rose"
            gain_sign = "+" if total_fix_gain >= 0 else ""
            render_metric_card(
                title="มูลค่าเพิ่มขึ้น (Capital Gain)",
                value=f"{gain_sign}฿{total_fix_gain:,.0f}",
                subtext=f"{gain_sign}{fix_gain_pct:.1f}% จากราคาซื้อ",
                badge_text=f"{gain_sign}{fix_gain_pct:.1f}%",
                badge_type=gain_badge
            )
        with fcol4:
            render_metric_card(
                title="ผลต่อ Net Worth รวม",
                value=f"฿{total_fix_val:,.0f}",
                subtext="รวมในความมั่งคั่งสุทธิ",
                badge_text="Balance Sheet",
                badge_type="green"
            )

        st.info("💡 **คำแนะนำ:** หากบ้านหรือคอนโดยังมีภาระผ่อน ให้กรอก **'มูลค่าบ้านเต็ม'** ในส่วนนี้ และกรอก **'ยอดหนี้ค้างชำระ'** ในหน้าหนี้สิน (Liabilities) ระบบจะคำนวณ Net Worth สุทธิให้อย่างถูกต้องครับ")

        st.markdown("---")

        # Inner Sub-tabs for Fixed Assets
        t_fix_view, t_fix_edit, t_fix_add, t_fix_manage = st.tabs([
            "📋 รายการอสังหาฯ & สินทรัพย์ถาวร", 
            "📝 แก้ไขตารางด่วน (Table Editor)",
            "➕ เพิ่มบ้าน / ที่ดิน / สิ่งปลูกสร้าง (Form)", 
            "⚙️ แก้ไข / ลบรายตัว"
        ])

        with t_fix_view:
            if not fixed_df.empty:
                disp_fix = fixed_df.copy()
                disp_fix["gain"] = disp_fix["current_value"] - disp_fix["cost_basis"]
                disp_fix["gain_pct"] = (disp_fix["gain"] / disp_fix["cost_basis"] * 100).fillna(0)

                formatted_fix = pd.DataFrame({
                    "ชื่อทรัพย์สิน": disp_fix["name"],
                    "ประเภททรัพย์สิน": disp_fix["category"],
                    "สถานที่ / โครงการ / ทะเบียน": disp_fix["platform_or_broker"],
                    "มูลค่าประเมินปัจจุบัน": disp_fix["current_value"].apply(lambda x: f"฿{x:,.0f}"),
                    "ราคาซื้อ / ต้นทุน": disp_fix["cost_basis"].apply(lambda x: f"฿{x:,.0f}"),
                    "มูลค่าส่วนต่าง": disp_fix["gain"].apply(lambda x: f"{'+' if x>=0 else ''}฿{x:,.0f}"),
                    "ผลตอบแทนส่วนต่าง (%)": disp_fix["gain_pct"].apply(lambda x: f"{'+' if x>=0 else ''}{x:.2f}%"),
                    "หมายเหตุ": disp_fix["notes"]
                })
                st.dataframe(formatted_fix, use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่มีรายการอสังหาริมทรัพย์หรือสินทรัพย์ถาวร (สามารถกดเพิ่มได้ที่แท็บด้านบน)")

        with t_fix_edit:
            st.markdown("##### 📝 แก้ไข/เพิ่ม/ลบ อสังหาริมทรัพย์ & สินทรัพย์ถาวรแบบตารางด่วน")
            st.caption("ดับเบิลคลิกแก้ไขตัวเลขในช่องตาราง, กดปุ่ม `+` เพื่อเพิ่มแถวใหม่ หรือติ๊กแถวแล้วกด Delete เพื่อลบ")
            
            fix_editable_cols = ["id", "name", "category", "current_value", "cost_basis", "platform_or_broker", "notes"]
            edit_fix_df = fixed_df[fix_editable_cols].copy() if not fixed_df.empty else pd.DataFrame(columns=fix_editable_cols)
            
            fix_column_config = {
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "name": st.column_config.TextColumn("ชื่อทรัพย์สิน (เช่น บ้านเดี่ยว, คอนโด, รถ)", required=True),
                "category": st.column_config.SelectboxColumn("ประเภท", options=FIXED_ASSET_CATS, required=True),
                "current_value": st.column_config.NumberColumn("มูลค่าประเมินปัจจุบัน (฿)", min_value=0, format="%.0f"),
                "cost_basis": st.column_config.NumberColumn("ราคาซื้อ / ต้นทุน (฿)", min_value=0, format="%.0f"),
                "platform_or_broker": st.column_config.TextColumn("สถานที่ / โครงการ / ทะเบียน"),
                "notes": st.column_config.TextColumn("หมายเหตุ"),
            }

            edited_fix = st.data_editor(
                edit_fix_df,
                column_config=fix_column_config,
                num_rows="dynamic",
                use_container_width=True,
                key="fix_table_editor"
            )

            if st.button("💾 บันทึกการเปลี่ยนแปลงสินทรัพย์ถาวรทั้งหมด", type="primary", use_container_width=True):
                conn = get_connection()
                c = conn.cursor()
                
                saved_fix_ids = []
                for _, r in edited_fix.iterrows():
                    asset_name = safe_str(r.get("name"))
                    if not asset_name:
                        continue
                    row_id = safe_float(r.get("id"), 0)
                    if row_id > 0:
                        c.execute("""
                        INSERT OR REPLACE INTO assets (id, name, category, current_value, cost_basis, target_allocation, monthly_dca, expected_roi, platform_or_broker, notes, asset_type, updated_at)
                        VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?, ?, 'fixed_asset', CURRENT_TIMESTAMP)
                        """, (
                            int(row_id),
                            asset_name,
                            safe_str(r.get("category"), FIXED_ASSET_CATS[0] if FIXED_ASSET_CATS else "🏠 บ้านเดี่ยว / ทาวน์โฮม (House)"),
                            safe_float(r.get("current_value"), 0.0),
                            safe_float(r.get("cost_basis"), 0.0),
                            safe_str(r.get("platform_or_broker"), ""),
                            safe_str(r.get("notes"), "")
                        ))
                        saved_fix_ids.append(int(row_id))
                    else:
                        c.execute("""
                        INSERT INTO assets (name, category, current_value, cost_basis, target_allocation, monthly_dca, expected_roi, platform_or_broker, notes, asset_type)
                        VALUES (?, ?, ?, ?, 0, 0, 0, ?, ?, 'fixed_asset')
                        """, (
                            asset_name,
                            safe_str(r.get("category"), FIXED_ASSET_CATS[0] if FIXED_ASSET_CATS else "🏠 บ้านเดี่ยว / ทาวน์โฮม (House)"),
                            safe_float(r.get("current_value"), 0.0),
                            safe_float(r.get("cost_basis"), 0.0),
                            safe_str(r.get("platform_or_broker"), ""),
                            safe_str(r.get("notes"), "")
                        ))
                        saved_fix_ids.append(c.lastrowid)
                
                # Delete removed fixed assets only
                current_fix_ids = [a["id"] for a in fixed_assets]
                to_delete = [fid for fid in current_fix_ids if fid not in saved_fix_ids]
                if to_delete:
                    del_ph = ','.join(['?'] * len(to_delete))
                    c.execute(f"DELETE FROM assets WHERE id IN ({del_ph})", to_delete)

                conn.commit()
                conn.close()
                st.toast("บันทึกข้อมูลสินทรัพย์ถาวรเรียบร้อยแล้ว!", icon="💾")
                st.rerun()

        with t_fix_add:
            with st.form("add_fix_asset_form", clear_on_submit=True):
                st.markdown("##### ➕ เพิ่มรายการบ้าน / คอนโด / ที่ดิน / สิ่งปลูกสร้างใหม่")
                fac1, fac2 = st.columns(2)
                with fac1:
                    fname = st.text_input("ชื่อทรัพย์สิน (เช่น บ้านเดี่ยว ราชพฤกษ์, คอนโด อโศก, ที่ดิน เขาใหญ่, รถยนต์ CR-V)", placeholder="เช่น บ้านเดี่ยว 2 ชั้น")
                    fcategory = st.selectbox("ประเภททรัพย์สิน", FIXED_ASSET_CATS)
                    fcurrent_val = st.number_input("ราคาประเมินตลาดปัจจุบัน (บาท)", min_value=0.0, step=50000.0, format="%.0f")
                with fac2:
                    fcost = st.number_input("ราคาซื้อ / เงินต้นทุนรวม (บาท)", min_value=0.0, step=50000.0, format="%.0f")
                    flocation = st.text_input("สถานที่ตั้ง / โครงการ / เลขทะเบียน", placeholder="เช่น ซอยสุขุมวิท 39, ทะเบียน กข-1234")
                    fnotes = st.text_input("หมายเหตุเพิ่มเติม", placeholder="เช่น ผ่อนกับ SCB เหลือหนี้ 1.5 ล้าน, ปล่อยเช่า")

                submitted_fix_add = st.form_submit_button("➕ บันทึกสินทรัพย์ถาวร", use_container_width=True, type="primary")
                if submitted_fix_add:
                    if not fname.strip():
                        st.error("กรุณาระบุชื่อทรัพย์สิน")
                    else:
                        add_asset({
                            "name": fname.strip(),
                            "category": fcategory,
                            "current_value": fcurrent_val,
                            "cost_basis": fcost,
                            "target_allocation": 0,
                            "monthly_dca": 0,
                            "expected_roi": 0,
                            "platform_or_broker": flocation.strip(),
                            "notes": fnotes.strip(),
                            "asset_type": "fixed_asset"
                        })
                        st.toast(f"บันทึก '{fname}' เรียบร้อยแล้ว!", icon="🎉")
                        st.rerun()

        with t_fix_manage:
            if fixed_df.empty:
                st.info("ยังไม่มีรายการสินทรัพย์ถาวรให้แก้ไข")
            else:
                fix_options = {f"{row['name']} ({row['category']}) - ฿{row['current_value']:,.0f}": row['id'] for _, row in fixed_df.iterrows()}
                selected_fix_label = st.selectbox("เลือกรายการที่ต้องการแก้ไขหรือลบ", list(fix_options.keys()), key="sel_fix_edit")
                selected_fix_id = fix_options[selected_fix_label]
                selected_fix_asset = next(a for a in fixed_assets if a["id"] == selected_fix_id)

                with st.form("edit_fix_asset_form"):
                    st.markdown(f"##### ✏️ แก้ไข: **{selected_fix_asset['name']}**")
                    fec1, fec2 = st.columns(2)
                    with fec1:
                        edit_fname = st.text_input("ชื่อทรัพย์สิน", value=selected_fix_asset["name"])
                        edit_fcategory = st.selectbox("ประเภททรัพย์สิน", FIXED_ASSET_CATS, index=FIXED_ASSET_CATS.index(selected_fix_asset["category"]) if selected_fix_asset["category"] in FIXED_ASSET_CATS else 0)
                        edit_fcurrent_val = st.number_input("มูลค่าประเมินปัจจุบัน (บาท)", min_value=0.0, value=float(selected_fix_asset["current_value"]), step=50000.0, format="%.0f")
                    with fec2:
                        edit_fcost = st.number_input("ราคาซื้อ / ต้นทุน (บาท)", min_value=0.0, value=float(selected_fix_asset["cost_basis"]), step=50000.0, format="%.0f")
                        edit_flocation = st.text_input("สถานที่ตั้ง / โครงการ / เลขทะเบียน", value=selected_fix_asset["platform_or_broker"] or "")
                        edit_fnotes = st.text_input("หมายเหตุเพิ่มเติม", value=selected_fix_asset["notes"] or "")

                    col_fbtn1, col_fbtn2 = st.columns(2)
                    with col_fbtn1:
                        submitted_fedit = st.form_submit_button("💾 บันทึกการแก้ไข", use_container_width=True, type="primary")
                    with col_fbtn2:
                        submitted_fdelete = st.form_submit_button("🗑️ ลบทรัพย์สินนี้", use_container_width=True)

                    if submitted_fedit:
                        update_asset(selected_fix_id, {
                            "name": edit_fname.strip(),
                            "category": edit_fcategory,
                            "current_value": edit_fcurrent_val,
                            "cost_basis": edit_fcost,
                            "target_allocation": 0,
                            "monthly_dca": 0,
                            "expected_roi": 0,
                            "platform_or_broker": edit_flocation.strip(),
                            "notes": edit_fnotes.strip(),
                            "asset_type": "fixed_asset"
                        })
                        st.toast("อัปเดตข้อมูลสินทรัพย์ถาวรสำเร็จ!", icon="✅")
                        st.rerun()

                    if submitted_fdelete:
                        delete_asset(selected_fix_id)
                        st.toast("ลบรายการสินทรัพย์ถาวรเรียบร้อยแล้ว", icon="🗑️")
                        st.rerun()
