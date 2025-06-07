import streamlit as st
import pandas as pd
from api.client import (
    upload_questions_pdf, upload_answers_pdf, merge_and_save,
    get_collections, get_questions
)
from ui.components.admin_components import (
    show_questions_json_preview, show_answers_json_preview
)

def show_admin_dashboard():
    """관리자 대시보드 표시"""
    st.title("관리자 패널")
    
    tabs = st.tabs(["PDF 업로드", "문제 관리", "사용자 관리"])
    
    with tabs[0]:  # PDF 업로드
        show_pdf_upload_tab()
    
    with tabs[1]:  # 문제 관리
        show_question_management_tab()
    
    with tabs[2]:  # 사용자 관리
        show_user_management_tab()
    # 로그아웃 버튼
    if st.sidebar.button("🚪 로그아웃", key="admin_logout"):
        _admin_logout()

def show_pdf_upload_tab():
    """PDF 업로드 탭"""
    st.header("PDF 파일 업로드")
    
    # 문제 PDF
    st.subheader("1️⃣ 문제 PDF")
    questions_file = st.file_uploader("문제 PDF 선택", type="pdf", key="questions_pdf")
    
    if questions_file:
        if st.button("📤 문제 업로드", key="upload_questions_button"):
            with st.spinner("📋 문제 파싱 중..."):
                result = upload_questions_pdf(questions_file)
                
                if result and result.get("status") == "success":
                    st.success("✅ 문제가 성공적으로 업로드되었습니다!")
                    
                    # 세션 상태에 저장
                    st.session_state.questions = result.get("questions", [])
                    st.session_state.questions_api_result = result
                    
                    st.write(f"📊 {len(st.session_state.questions)}개 문제가 감지되었습니다.")
                else:
                    st.error("❌ 문제 업로드 중 오류가 발생했습니다.")
                    if result:
                        st.json(result)
    
    # 문제 JSON 미리보기
    if st.session_state.get("questions_api_result"):
        show_questions_json_preview(st.session_state.questions_api_result)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ 문제 지우기", key="clear_questions"):
                if "questions" in st.session_state:
                    del st.session_state.questions
                if "questions_api_result" in st.session_state:
                    del st.session_state.questions_api_result
                st.rerun()
    
    st.markdown("---")
    
    # 답안 PDF
    st.subheader("2️⃣ 답안 키 PDF")
    answers_file = st.file_uploader("답안 키 PDF 선택", type="pdf", key="answers_pdf")
    
    if answers_file:
        if st.button("🔑 답안 키 업로드", key="upload_answers_button"):
            with st.spinner("🔍 답안 키 파싱 중..."):
                result = upload_answers_pdf(answers_file)
                
                if result and result.get("status") == "success":
                    st.success("✅ 답안 키가 성공적으로 업로드되었습니다!")
                    
                    # 세션 상태에 저장
                    st.session_state.answers = result.get("answers", [])
                    st.session_state.answers_api_result = result
                    
                    st.write(f"📊 {len(st.session_state.answers)}개 답안이 감지되었습니다.")
                else:
                    st.error("❌ 답안 키 업로드 중 오류가 발생했습니다.")
                    if result:
                        st.json(result)
    
    # 답안 JSON 미리보기
    if st.session_state.get("answers_api_result"):
        show_answers_json_preview(st.session_state.answers_api_result)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ 답안 지우기", key="clear_answers"):
                if "answers" in st.session_state:
                    del st.session_state.answers
                if "answers_api_result" in st.session_state:
                    del st.session_state.answers_api_result
                st.rerun()
    
    # 세션 선택
    if st.session_state.get("answers"):
        _show_session_selection()
    
    # 데이터 저장
    _show_data_save_section()

def _show_session_selection():
    """세션 선택 섹션"""
    st.markdown("---")
    st.subheader("3️⃣ 세션 선택")
    
    answers = st.session_state.answers
    available_sessions = list(set([
        ans.get('session', '') for ans in answers 
        if ans.get('session', '').strip()
    ]))
    available_sessions = [s for s in available_sessions if s]
    
    if available_sessions:
        selected_session = st.selectbox(
            "📚 어떤 세션을 저장하시겠습니까?",
            ["전체"] + sorted(available_sessions),
            index=0
        )
        
        if selected_session == "전체":
            st.session_state.selected_session = None
            st.info("💡 모든 세션이 저장됩니다")
        else:
            st.session_state.selected_session = selected_session
            st.success(f"✅ 선택된 세션: {selected_session}")
    else:
        st.info("📝 답안 키에서 세션 정보를 찾을 수 없습니다")

def _show_data_save_section():
    """데이터 저장 섹션"""
    st.subheader("데이터 저장")
    
    has_questions = "questions" in st.session_state and st.session_state.questions
    has_answers = "answers" in st.session_state and st.session_state.answers
    
    if has_questions or has_answers:
        collection_name = st.text_input("컬렉션 이름", value="exam_questions")
        
        if st.button("저장", key="save_button"):
            with st.spinner("데이터 저장 중..."):
                questions = st.session_state.questions if has_questions else []
                answers = st.session_state.answers if has_answers else None
                selected_session = st.session_state.get("selected_session")
                
                result = merge_and_save(questions, answers, collection_name, selected_session)
                
                if result and result.get("status") == "success":
                    st.success(result.get("message", "데이터가 성공적으로 저장되었습니다!"))
                    
                    # 세션 상태 정리
                    if "questions" in st.session_state:
                        del st.session_state.questions
                    if "answers" in st.session_state:
                        del st.session_state.answers
                    if "selected_session" in st.session_state:
                        del st.session_state.selected_session
                else:
                    st.error("데이터 저장 중 오류가 발생했습니다.")
    else:
        st.warning("저장할 문제나 답안이 없습니다. 먼저 PDF 파일을 업로드해주세요.")

def show_question_management_tab():
    """문제 관리 탭"""
    st.header("문제 관리")
    
    collections_result = get_collections()
    
    if collections_result and collections_result.get("status") == "success":
        collections = collections_result.get("collections", [])
        
        if collections:
            selected_collection = st.selectbox(
                "컬렉션 선택",
                collections,
                key="admin_collection_select"
            )
            
            limit = st.slider("페이지당 문제 수", 5, 50, 10, key="admin_limit_slider")
            page = st.number_input("페이지", min_value=1, value=1, key="admin_page_number")
            skip = (page - 1) * limit
            
            questions_result = get_questions(selected_collection, limit, skip)
            
            if questions_result and questions_result.get("status") == "success":
                questions = questions_result.get("questions", [])
                
                if questions:
                    # 문제를 DataFrame으로 표시
                    questions_df = []
                    for q in questions:
                        questions_df.append({
                            "문제 ID": q.get("problem_id", ""),
                            "문제": q.get("problem", "")[:50] + "..." if len(q.get("problem", "")) > 50 else q.get("problem", ""),
                            "답안": q.get("answer_key", ""),
                            "난이도": q.get("difficulty", "미지정"),
                            "선택지": str(q.get("choices", [])),
                            "생성일": q.get("created_at", ""),
                            "세션": q.get("session", "N/A"),
                            "과목": q.get("subject", "N/A"),
                        })
                    
                    st.dataframe(pd.DataFrame(questions_df), use_container_width=True)
                    
                    # 페이지네이션 컨트롤
                    total = questions_result.get("total", 0)
                    col1, col2 = st.columns(2)
                    with col1:
                        if page > 1:
                            if st.button("이전 페이지", key="admin_prev_page"):
                                st.experimental_set_query_params(admin_page=page-1)
                    with col2:
                        if page < (total // limit) + 1:
                            if st.button("다음 페이지", key="admin_next_page"):
                                st.experimental_set_query_params(admin_page=page+1)
                else:
                    st.warning("이 컬렉션에서 문제를 찾을 수 없습니다.")
            else:
                st.error("문제 로드 중 오류가 발생했습니다.")
        else:
            st.warning("아직 컬렉션이 없습니다.")
    else:
        st.error("컬렉션 로드 중 오류가 발생했습니다.")

def show_user_management_tab():
    """사용자 관리 탭"""
    st.header("사용자 관리")
    
    st.info("이 섹션은 사용자 관리 기능을 위해 예약되어 있으며 곧 사용할 수 있게 됩니다.")
    
    # 시연용 예시 내용
    st.subheader("예시 사용자 목록")
    
    sample_users = [
        {"id": "1", "name": "김철수", "email": "kim@example.com", "department": "물리치료", "level": "상"},
        {"id": "2", "name": "이영희", "email": "lee@example.com", "department": "물리치료", "level": "중"},
        {"id": "3", "name": "박민수", "email": "park@example.com", "department": "물리치료", "level": "하"}
    ]
    
    users_df = pd.DataFrame(sample_users)
    users_df.columns = ["ID", "이름", "이메일", "학과", "레벨"]
    st.dataframe(users_df, use_container_width=True)
def _admin_logout():
    """관리자 로그아웃 처리"""
    # 세션 상태 초기화
    session_vars_to_clear = [
        "user", "current_test", "current_answers", "test_submitted", 
        "test_results", "selected_session", "questions_api_result",
        "answers_api_result", "current_practice_question", 
        "practice_answer_submitted", "practice_explanation",
        "test_history_data", "selected_test_details"
    ]
    
    for var in session_vars_to_clear:
        if var in st.session_state:
            st.session_state[var] = None if var != "current_answers" else {}
    
    # 관리자 관련 세션 변수들도 정리
    admin_vars = ["questions", "answers", "questions_api_result", "answers_api_result", "selected_session"]
    for var in admin_vars:
        if var in st.session_state:
            st.session_state[var] = None
    
    st.success("로그아웃되었습니다!")
    st.rerun()    