import streamlit as st
from config.settings import configure_page
from config.session_state import initialize_session_state
from ui.auth import show_login_page
from ui.student import show_student_dashboard
from ui.admin import show_admin_dashboard

def main():
    configure_page()
    
    initialize_session_state()
    
    # Sidebar
    st.sidebar.title("📚 시험 플랫폼")
    
    # User authentication check
    if st.session_state.user:
        # Kullanıcı bilgilerini sidebar'da göster
        user_name = st.session_state.user.get('name', '사용자')
        user_role = st.session_state.user.get('role', 'student')
        
        st.sidebar.success(f"✅ 로그인됨: {user_name}")
        st.sidebar.info(f"🎭 역할: {user_role}")
        
        # ROle
        if user_role and user_role.lower() == "admin":
            st.sidebar.success("🔧 관리자 패널 활성")
            show_admin_dashboard()
        else:
            st.sidebar.info("👨‍🎓 학생 패널 활성")
            show_student_dashboard()
        
        # Sidebar information
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 빠른 정보")
        
        if user_role and user_role.lower() == "admin":
            st.sidebar.info("🔧 관리자로 로그인했습니다")
            st.sidebar.markdown("- PDF 업로드")
            st.sidebar.markdown("- 문제 관리") 
            st.sidebar.markdown("- 사용자 추적")
        else:
            level = st.session_state.user.get('level', '아직 테스트되지 않음')
            st.sidebar.info(f"📊 귀하의 레벨: {level}")
    else:
        show_login_page()

if __name__ == "__main__":
    main()