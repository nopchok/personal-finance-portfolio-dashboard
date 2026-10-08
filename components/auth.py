"""
Authentication & User Management Component for Minimal Personal Finance
Provides modern, clean login and registration UI for multi-user data isolation.
"""

import streamlit as st
from database import login_user, register_user, get_all_users

def render_auth_page():
    """Renders the standalone login and registration portal."""
    
    st.markdown("""<div style="max-width: 480px; margin: 2rem auto 1rem auto; text-align: center;">
<div style="display: inline-flex; background: #EEF2FF; width: 64px; height: 64px; border-radius: 18px; border: 1px solid #C7D2FE; align-items: center; justify-content: center; font-size: 2rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);">
💼
</div>
<h1 style="font-size: 1.85rem; font-weight: 800; color: #0F172A; margin: 0 0 0.4rem 0; letter-spacing: -0.03em;">
MINIMAL FINANCE
</h1>
<p style="color: #64748B; font-size: 0.95rem; margin: 0 0 1.5rem 0;">
ระบบบริหารการเงิน & พอร์ตการลงทุนส่วนบุคคล (Multi-User Dashboard)
</p>
</div>""", unsafe_allow_html=True)

    col_center = st.columns([1, 2.2, 1])[1]
    
    with col_center:
        st.markdown('<div class="tailwind-card" style="padding: 1.75rem 2rem;">', unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔑 เข้าสู่ระบบ (Sign In)", "✨ สร้างบัญชีใหม่ (Sign Up)"])
        
        # -------------------------------------------------------------
        # TAB 1: LOGIN
        # -------------------------------------------------------------
        with tab_login:
            st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)
            with st.form("form_login"):
                login_username = st.text_input(
                    "ชื่อผู้ใช้ / Username / PIN", 
                    placeholder="เช่น user1, nnn",
                    key="login_user_input"
                ).strip()
                
                login_password = st.text_input(
                    "รหัสผ่าน / Password", 
                    type="password", 
                    placeholder="ระบุรหัสผ่าน",
                    key="login_pass_input"
                )
                
                st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
                btn_login = st.form_submit_button(
                    "🚀 เข้าสู่ระบบ (Sign In)", 
                    type="primary", 
                    use_container_width=True
                )
                
                if btn_login:
                    if not login_username or not login_password:
                        st.error("กรุณาระบุชื่อผู้ใช้และรหัสผ่านให้ครบถ้วน")
                    else:
                        success, msg, user_data = login_user(login_username, login_password)
                        if success and user_data:
                            st.session_state["current_user"] = user_data
                            st.toast(f"ยินดีต้อนรับคุณ {user_data.get('display_name')}!", icon="👋")
                            st.rerun()
                        else:
                            st.error(msg)
                            
            # Quick Demo / Existing User Helper
            existing_users = get_all_users()
            if not existing_users:
                st.info("💡 ยังไม่มีบัญชีผู้ใช้ในระบบ คุณสามารถคลิกแท็บ **'สร้างบัญชีใหม่'** ด้านบนเพื่อเริ่มต้นใช้งานได้ทันที")
        
        # -------------------------------------------------------------
        # TAB 2: REGISTER
        # -------------------------------------------------------------
        with tab_register:
            st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)
            with st.form("form_register"):
                reg_username = st.text_input(
                    "ตั้งชื่อผู้ใช้ (Username)", 
                    placeholder="เช่น nnn (ตัวอักษรภาษาอังกฤษหรือตัวเลข)",
                    key="reg_user_input"
                ).strip().lower()
                
                reg_display_name = st.text_input(
                    "ชื่อที่ต้องการแสดง (Display Name)", 
                    placeholder="เช่น My Wealth",
                    key="reg_name_input"
                ).strip()
                
                reg_password = st.text_input(
                    "ตั้งรหัสผ่าน (Password)", 
                    type="password", 
                    placeholder="อย่างน้อย 4 ตัวอักษร",
                    key="reg_pass_input"
                )
                
                reg_confirm = st.text_input(
                    "ยืนยันรหัสผ่าน (Confirm Password)", 
                    type="password", 
                    placeholder="พิมพ์รหัสผ่านอีกครั้ง",
                    key="reg_confirm_input"
                )
                
                seed_sample = st.checkbox(
                    "🌱 โหลดชุดข้อมูลตัวอย่างเริ่มต้น (Sample Investments, Income & Expenses)",
                    value=False,
                    help="โหลดพอร์ตการลงทุนจำลองเพื่อให้เห็นกราฟและฟังก์ชันทั้งหมดพร้อมใช้งานทันที"
                )
                
                st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
                btn_reg = st.form_submit_button(
                    "✨ สร้างบัญชีผู้ใช้และเริ่มต้นใช้งาน", 
                    type="primary", 
                    use_container_width=True
                )
                
                if btn_reg:
                    if not reg_username:
                        st.error("กรุณาระบุ Username")
                    elif len(reg_username) < 3:
                        st.error("Username ต้องมีความยาวอย่างน้อย 3 ตัวอักษร")
                    elif not reg_password:
                        st.error("กรุณาระบุรหัสผ่าน")
                    elif len(reg_password) < 4:
                        st.error("รหัสผ่านต้องมีความยาวอย่างน้อย 4 ตัวอักษร")
                    elif reg_password != reg_confirm:
                        st.error("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
                    else:
                        display = reg_display_name if reg_display_name else reg_username
                        success, msg, user_data = register_user(
                            username=reg_username,
                            password=reg_password,
                            display_name=display,
                            seed_sample=seed_sample
                        )
                        if success and user_data:
                            st.session_state["current_user"] = user_data
                            st.toast(f"🎉 สร้างบัญชีสำเร็จ! ยินดีต้อนรับคุณ {display}", icon="🎉")
                            st.rerun()
                        else:
                            st.error(msg)
                            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Privacy & Security Assurance Note
        st.markdown("""<div style="text-align: center; color: #94A3B8; font-size: 0.78rem; margin-top: 1.5rem; line-height: 1.5;">
🔒 <b>ข้อมูลแยกส่วนบุคคล 100%:</b> บัญชีแต่ละคนจะเห็นเฉพาะสินทรัพย์ หนี้สิน รายได้ และประมาณการของตนเองเท่านั้น
</div>""", unsafe_allow_html=True)

def render_sidebar_user_profile():
    """Renders the user profile card and logout button in the sidebar."""
    current_user = st.session_state.get("current_user")
    if not current_user:
        return
        
    display_name = current_user.get("display_name", "ผู้ใช้งาน")
    username = current_user.get("username", "user")
    initial = (display_name[0] if display_name else username[0]).upper()
    
    st.markdown(f"""<div style="background: linear-gradient(135deg, #F8FAFC 0%, #EEF2FF 100%); border: 1px solid #C7D2FE; border-radius: 12px; padding: 10px 14px; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
<div style="display: flex; align-items: center; gap: 0.75rem;">
<div style="background: #4F46E5; color: #FFFFFF; font-weight: 700; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1rem; box-shadow: 0 2px 4px rgba(79, 70, 229, 0.25);">
{initial}
</div>
<div>
<div style="font-weight: 700; font-size: 0.92rem; color: #0F172A; line-height: 1.2;">{display_name}</div>
<div style="font-size: 0.75rem; color: #6366F1; font-weight: 500;">@{username}</div>
</div>
</div>
<div style="background: #ECFDF5; color: #059669; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; border: 1px solid #A7F3D0;">
Online
</div>
</div>""", unsafe_allow_html=True)
    
    if st.button("🚪 ออกจากระบบ (Sign Out)", use_container_width=True, key="btn_logout_sidebar"):
        st.session_state.pop("current_user", None)
        st.session_state.pop("nav_menu", None)
        try:
            st.cache_data.clear()
        except Exception:
            pass
        st.toast("ออกจากระบบเรียบร้อยแล้ว", icon="👋")
        st.rerun()
