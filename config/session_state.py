import streamlit as st

def initialize_session_state():
    """세션 상태 초기화"""
    session_vars = {
        # 사용자 관련
        "user": None,
        
        # 레벨 테스트 관련
        "current_test": None,
        "current_answers": {},
        "test_submitted": False,
        "test_results": None,
        
        # 타이머 및 네비게이션 관련 (새로 추가)
        "test_start_time": None,
        "test_duration_minutes": 30,
        "current_question_index": 0,
        "auto_submitted": False,
        "show_submit_confirmation": False,  # 새로 추가
        
        # 관리자 기능 관련
        "selected_session": None,
        "questions_api_result": None,
        "answers_api_result": None,
        
        # 연습 테스트 관련
        "current_practice_question": None,
        "practice_answer_submitted": False,
        "practice_explanation": None,
        
        # 기타
        "test_history_data": None,
        "selected_test_details": None
    }
    
    for var, default_value in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default_value

def clear_test_session():
    """테스트 세션 정리"""
    test_vars = [
        "current_test", "current_answers", "test_submitted", "test_results",
        "test_start_time", "test_duration_minutes", "current_question_index", 
        "auto_submitted", "show_submit_confirmation"
    ]
    
    for var in test_vars:
        if var in st.session_state:
            if var == "current_answers":
                st.session_state[var] = {}
            else:
                st.session_state[var] = None

def clear_practice_session():
    """연습 세션 정리"""
    practice_vars = [
        "current_practice_question", "practice_answer_submitted", "practice_explanation"
    ]
    
    for var in practice_vars:
        if var in st.session_state:
            st.session_state[var] = None

def clear_admin_session():
    """관리자 세션 정리"""
    admin_vars = [
        "questions", "answers", "questions_api_result", "answers_api_result", "selected_session"
    ]
    
    for var in admin_vars:
        if var in st.session_state:
            del st.session_state[var]

def reset_timer():
    """타이머 리셋"""
    from datetime import datetime
    st.session_state.test_start_time = datetime.now()
    st.session_state.current_question_index = 0
    st.session_state.auto_submitted = False

def get_time_remaining():
    """남은 시간 계산"""
    from datetime import datetime, timedelta
    
    if not st.session_state.test_start_time:
        return None
    
    start_time = st.session_state.test_start_time
    duration_minutes = st.session_state.test_duration_minutes
    current_time = datetime.now()
    elapsed_time = current_time - start_time
    remaining_time = timedelta(minutes=duration_minutes) - elapsed_time
    
    return remaining_time

def is_time_expired():
    """시간이 만료되었는지 확인"""
    remaining = get_time_remaining()
    if remaining is None:
        return False
    return remaining.total_seconds() <= 0

def get_progress_stats():
    """진행 상황 통계"""
    if not st.session_state.current_test:
        return {"total": 0, "answered": 0, "current": 0, "progress": 0}
    
    total_questions = len(st.session_state.current_test)
    answered_questions = len(st.session_state.current_answers)
    current_question = st.session_state.current_question_index + 1
    progress_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
    
    return {
        "total": total_questions,
        "answered": answered_questions,
        "current": current_question,
        "progress": progress_percentage
    }