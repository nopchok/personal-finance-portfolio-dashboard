"""
History Snapshots, Data Backup & System Settings Module
Allows viewing timeline history, managing custom categories, exporting/importing JSON backups, and resetting data.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    get_all_snapshots, delete_snapshot, save_snapshot,
    export_all_data, import_all_data, seed_sample_data_if_empty, reset_all_data,
    get_categories, add_category, delete_category, reset_default_categories
)
from components.charts import create_historical_trend_chart

CAT_TYPE_MAP = {
    "รายได้ (Income)": "income",
    "รายจ่าย (Expense)": "expense",
    "พอร์ตการลงทุนสภาพคล่อง (Liquid Investment Asset)": "asset",
    "สินทรัพย์ถาวร & อสังหาริมทรัพย์ (Real Estate & Fixed Asset)": "fixed_asset",
    "หนี้สิน (Liability)": "liability"
}

def render_settings_data():
    st.markdown('<div class="section-header">📜 ประวัติรายเดือน, จัดการหมวดหมู่ & สำรองข้อมูล (History & Backup)</div>', unsafe_allow_html=True)
    st.caption("ติดตามพัฒนาการความมั่งคั่งย้อนหลัง, ปรับแต่งหมวดหมู่ตามใจชอบ, และสำรองข้อมูล JSON")

    tab_hist, tab_cats, tab_backup, tab_danger = st.tabs([
        "📊 ประวัติย้อนหลัง (History)", 
        "🏷️ จัดการหมวดหมู่ (Category Manager)",
        "💾 สำรอง & กู้คืนข้อมูล (Export / Import)", 
        "⚠️ จัดการฐานข้อมูล"
    ])

    # Tab 1: History
    with tab_hist:
        snapshots = get_all_snapshots()
        st.plotly_chart(create_historical_trend_chart(snapshots), use_container_width=True)

        if snapshots:
            sdf = pd.DataFrame(snapshots)
            formatted_sdf = pd.DataFrame({
                "เดือน (Month)": sdf["snapshot_month"],
                "รายได้รวม": sdf["income"].apply(lambda x: f"฿{x:,.0f}"),
                "รายจ่ายรวม": sdf["expenses"].apply(lambda x: f"฿{x:,.0f}"),
                "เงินออม/ลงทุน": sdf["savings_invested"].apply(lambda x: f"฿{x:,.0f}"),
                "สินทรัพย์รวม": sdf["total_assets"].apply(lambda x: f"฿{x:,.0f}"),
                "หนี้สินรวม": sdf["total_debts"].apply(lambda x: f"฿{x:,.0f}"),
                "Net Worth": sdf["net_worth"].apply(lambda x: f"฿{x:,.0f}"),
                "หมายเหตุ": sdf["notes"]
            })
            st.dataframe(formatted_sdf, use_container_width=True, hide_index=True)

            with st.expander("🗑️ ลบประวัติบางเดือน"):
                month_to_del = st.selectbox("เลือกเดือนที่ต้องการลบ", [s["snapshot_month"] for s in snapshots])
                if st.button("ยืนยันการลบประวัติเดือนนี้", type="secondary"):
                    delete_snapshot(month_to_del)
                    st.toast(f"ลบประวัติเดือน {month_to_del} เรียบร้อย", icon="🗑️")
                    st.rerun()
        else:
            st.info("ยังไม่มีข้อมูลบันทึกประวัติรายเดือน คุณสามารถกด 'บันทึก Snapshot' ได้ที่หน้าประมาณการรายเดือน")

        with st.expander("📖 คำอธิบาย: การบันทึก Snapshot ประจำเดือนมีประโยชน์อย่างไร?", expanded=False):
            st.markdown("""
            * 📸 **Snapshot คืออะไร?:** คือการ "ถ่ายภาพบันทึกสถานะการเงิน" ณ สิ้นเดือนนั้นๆ (เช่น รายได้, รายจ่าย, พอร์ตลงทุน, หนี้สิน, และ Net Worth)
            * 📈 **ประโยชน์:** เมื่อคุณบันทึกเป็นประจำทุกเดือน กราฟด้านบนจะวาดเส้นแนวโน้มให้เห็นว่า **ความมั่งคั่งสุทธิ (Net Worth) ของคุณกำลังเติบโตขึ้นเร็วแค่ไหน**
            * 🗓️ **ควรกดบันทึกเมื่อไหร่?:** แนะนำให้กดปุ่ม **"📸 บันทึก Snapshot รอบเดือนนี้"** ในหน้าแรก ทุกๆ สิ้นเดือน หรือวันเงินเดือนออกครับ
            """)

    # Tab 2: Category Manager
    with tab_cats:
        st.markdown("##### 🏷️ เพิ่ม / ลด / ปรับแต่งหมวดหมู่ตามการใช้งานของคุณ")
        st.caption("คุณสามารถเพิ่มหมวดหมู่ใหม่ หรือลบหมวดหมู่ที่ไม่ได้ใช้ออก โดยรายการที่เพิ่มจะไปแสดงใน Dropdown และตารางทันที")

        selected_cat_type_label = st.selectbox("เลือกประเภทหมวดหมู่ที่ต้องการจัดการ", list(CAT_TYPE_MAP.keys()))
        selected_cat_type = CAT_TYPE_MAP[selected_cat_type_label]
        
        current_cats = get_categories(selected_cat_type)

        col_cat_view, col_cat_add = st.columns([3, 2])

        with col_cat_view:
            st.markdown(f"**รายการหมวดหมู่ {selected_cat_type_label} ปัจจุบัน ({len(current_cats)} หมวด):**")
            
            for cat_name in current_cats:
                c_pill1, c_pill2 = st.columns([4, 1])
                with c_pill1:
                    st.markdown(f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 7px 12px; border-radius: 8px; margin-bottom: 6px; font-weight: 600; color: #0F172A; font-size: 0.9rem;">
                        {cat_name}
                    </div>
                    """, unsafe_allow_html=True)
                with c_pill2:
                    if st.button("🗑️ ลบ", key=f"del_cat_{selected_cat_type}_{cat_name}", help=f"ลบหมวดหมู่ {cat_name}"):
                        delete_category(selected_cat_type, cat_name)
                        st.toast(f"ลบหมวดหมู่ '{cat_name}' แล้ว", icon="🗑️")
                        st.rerun()

        with col_cat_add:
            st.markdown(f"**➕ เพิ่มหมวดหมู่ใหม่สำหรับ {selected_cat_type_label}:**")
            new_cat_name = st.text_input("ชื่อหมวดหมู่ใหม่", placeholder="เช่น 🐱 สัตว์เลี้ยง & อุปกรณ์, 🎮 เกม & ของสะสม", key=f"new_cat_input_{selected_cat_type}")
            if st.button("➕ เพิ่มหมวดหมู่นี้", type="primary", use_container_width=True, key=f"btn_add_cat_{selected_cat_type}"):
                if not new_cat_name.strip():
                    st.error("กรุณาระบุชื่อหมวดหมู่")
                else:
                    success = add_category(selected_cat_type, new_cat_name.strip())
                    if success:
                        st.toast(f"เพิ่มหมวดหมู่ '{new_cat_name.strip()}' สำเร็จ!", icon="🎉")
                        st.rerun()
                    else:
                        st.warning("หมวดหมู่นี้มีอยู่แล้ว")

            st.markdown("---")
            if st.button(f"🔄 คืนค่าเริ่มต้นเฉพาะ {selected_cat_type_label}", type="secondary", use_container_width=True):
                reset_default_categories(selected_cat_type)
                st.toast(f"คืนค่าเริ่มต้นหมวดหมู่ {selected_cat_type_label} เรียบร้อยแล้ว", icon="🔄")
                st.rerun()

    # Tab 3: Export / Import
    with tab_backup:
        col_exp, col_imp = st.columns(2)
        with col_exp:
            st.markdown("##### 📤 ดาวน์โหลดไฟล์สำรองข้อมูล (Export JSON)")
            st.caption("บันทึกข้อมูลพอร์ต, การประมาณการ, หมวดหมู่ที่สร้างขึ้น และประวัติทั้งหมดเก็บไว้ในเครื่อง")
            json_data = export_all_data()
            today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ myfinance_backup.json",
                data=json_data,
                file_name=f"myfinance_backup_{today_str}.json",
                mime="application/json",
                type="primary",
                use_container_width=True
            )

        with col_imp:
            st.markdown("##### 📥 กู้คืนข้อมูลจากไฟล์ (Import JSON)")
            st.caption("อัปโหลดไฟล์ JSON ที่เคยดาวน์โหลดไว้เพื่อเรียกคืนข้อมูล")
            uploaded_file = st.file_uploader("เลือกไฟล์ myfinance_backup.json", type=["json"])
            if uploaded_file is not None:
                if st.button("ยืนยันการนำเข้าข้อมูล", type="secondary", use_container_width=True):
                    content = uploaded_file.getvalue().decode("utf-8")
                    success = import_all_data(content)
                    if success:
                        st.success("🎉 นำเข้าข้อมูลและกู้คืนสำเร็จ!")
                        st.rerun()
                    else:
                        st.error("เกิดข้อผิดพลาด รูปแบบไฟล์ JSON ไม่ถูกต้อง")

    # Tab 4: Danger Zone / Reset
    with tab_danger:
        st.markdown("##### ⚙️ รีเซ็ตและคืนค่าเริ่มต้น")
        st.caption("หากต้องการเริ่มต้นใหม่ หรือโหลดตัวอย่างข้อมูลจำลอง")
        
        c_reset1, c_reset2 = st.columns(2)
        with c_reset1:
            if st.button("🔄 โหลดข้อมูลตัวอย่างใหม่ (Seed Sample Data)", use_container_width=True):
                reset_all_data()
                reset_default_categories()
                seed_sample_data_if_empty()
                st.toast("โหลดข้อมูลตัวอย่างสำเร็จ!", icon="🌱")
                st.rerun()

        with c_reset2:
            if st.button("🗑️ ล้างข้อมูลทั้งหมด (Clear All Data)", use_container_width=True):
                reset_all_data()
                reset_default_categories()
                st.toast("ล้างข้อมูลทั้งหมดเรียบร้อยแล้ว", icon="🧹")
                st.rerun()
