import streamlit as st
from api.client import login, register, google_login

def show_login_page():
    """로그인 페이지 표시"""
    st.title("시험 플랫폼 - 로그인")
    
    tabs = st.tabs(["로그인", "회원가입", "Google 로그인"])
    
    with tabs[0]:  # 로그인
        _show_login_tab()
    
    with tabs[1]:  # 회원가입
        _show_register_tab()
    
    with tabs[2]:  # Google 로그인
        _show_google_login_tab()

def _show_login_tab():
    """로그인 탭"""
    email = st.text_input("이메일", key="login_email")
    password = st.text_input("비밀번호", type="password", key="login_password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("로그인", key="login_button"):
            if not email or not password:
                st.error("이메일과 비밀번호가 필요합니다")
            else:
                result = login(email, password)
                if result and result.get("status") == "success":
                    st.session_state.user = result.get("user")
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("로그인 실패. 정보를 확인해주세요.")

def _show_register_tab():
    """회원가입 탭"""
    reg_email = st.text_input("이메일", key="reg_email")
    reg_password = st.text_input("비밀번호", type="password", key="reg_password")
    reg_name = st.text_input("이름", key="reg_name")
    reg_grade = st.number_input("학년", min_value=1, max_value=12, value=1, key="reg_grade")
    reg_dept = st.text_input("학과", key="reg_dept")
    
    if st.button("회원가입", key="register_button"):
        if not reg_email or not reg_password or not reg_name:
            st.error("이메일, 비밀번호, 이름은 필수입니다")
        else:
            result = register(reg_email, reg_password, reg_name, reg_grade, reg_dept)
            if result and result.get("status") == "success":
                st.success("회원가입 성공! 로그인할 수 있습니다.")
            else:
                st.error("회원가입 실패. 정보를 확인해주세요.")

def _show_google_login_tab():
    """Google 로그인 탭"""
    google_email = st.text_input("Google 이메일", key="google_email")
    google_name = st.text_input("이름", key="google_name")
    
    if st.button("Google 로그인", key="google_login_button"):
        if not google_email or not google_name:
            st.error("이메일과 이름이 필요합니다")
        else:
            result = google_login(google_email, google_name)
            if result and result.get("status") == "success":
                st.session_state.user = result.get("user")
                st.success("Google 로그인 성공!")
                st.rerun()
            else:
                st.error("Google 로그인 실패. 정보를 확인해주세요.")