import streamlit as st
from config.session_state import clear_test_session
from ui.components.level_test import show_level_test_tab
from ui.components.practice_test import show_practice_test_tab
from ui.components.remaining import show_test_history_tab
from ui.components.remaining import show_questions_tab
from ui.components.remaining import show_profile_tab
from ui.components.bkt_dashboard import show_bkt_dashboard_tab
from ui.components.adaptive_test_component import show_adaptive_test_component

def show_student_dashboard():
    """학생 대시보드 표시"""
    user = st.session_state.user
    
    st.title(f"안녕하세요, {user.get('name', '학생')}님!")
    
    # 상단 정보 카드
    _show_user_info_cards(user)
    
    # 메인 탭들 - 적응형 테스트 탭 추가
    tabs = st.tabs([
        "레벨 테스트", 
        "테스트 기록", 
        "🧠 학습 분석",
        "🎯 맞춤형 테스트",  # 새로운 적응형 테스트 탭
        "연습 테스트",
        "문제", 
        "프로필"
    ])
    
    with tabs[0]:  # 레벨 테스트
        show_level_test_tab()
    
    with tabs[1]:  # 연습 테스트
        show_test_history_tab()
    
    with tabs[2]:  # 새로운 적응형 테스트
        show_bkt_dashboard_tab()
        
    with tabs[3]:  # BKT 학습 분석
        show_adaptive_test_component()
    
    with tabs[4]:  # 테스트 기록
        show_practice_test_tab()
        
    with tabs[5]:  # 문제
        show_questions_tab()
    
    with tabs[6]:  # 프로필
        show_profile_tab()
    
    # 로그아웃 버튼
    if st.sidebar.button("로그아웃"):
        _logout()
        
def _show_user_info_cards(user):
    """사용자 정보 카드 표시"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**학과:** {user.get('department', '미지정')}")
    
    with col2:
        st.info(f"**학년:** {user.get('grade', '미지정')}")
    
    with col3:
        level = user.get('level', None)
        level_text = "아직 테스트되지 않음" if level is None else level
        level_color = "warning" if level is None else "success"
        getattr(st, level_color)(f"**레벨:** {level_text}")

def _logout():
    """로그아웃 처리"""
    # 세션 상태 초기화
    session_vars_to_clear = [
        "user", "current_test", "current_answers", "test_submitted", 
        "test_results", "selected_session", "questions_api_result",
        "answers_api_result", "current_practice_question", 
        "practice_answer_submitted", "practice_explanation",
        "test_history_data", "selected_test_details",
        # 적응형 테스트 관련 세션 변수들도 추가
        "adaptive_test", "adaptive_answers", "adaptive_submitted",
        "adaptive_results", "adaptive_question_index", "adaptive_start_time",
        # ⭐ NEW: Adaptive navigation state variables
        "adaptive_nav_button_clicked", "adaptive_prev_selectbox_index"
    ]
    
    for var in session_vars_to_clear:
        if var in st.session_state:
            st.session_state[var] = None if var != "current_answers" and var != "adaptive_answers" else {}
    
    st.rerun()