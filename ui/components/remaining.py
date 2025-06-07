# ui/components/test_history.py
import streamlit as st
from datetime import datetime
from api.client import get_user_test_history, get_test_details, explain_answer

def show_test_history_tab():
    """테스트 기록 탭 표시"""
    st.header("📊 내 테스트 기록")
    
    user_id = st.session_state.user.get("user_id")
    
    # 테스트 기록을 세션 상태에 보관
    if "test_history_data" not in st.session_state:
        st.session_state.test_history_data = None
    if "selected_test_details" not in st.session_state:
        st.session_state.selected_test_details = None
    
    # 테스트 세부사항이 선택되면 표시
    if st.session_state.selected_test_details:
        show_test_details_view()
        return
    
    # 테스트 기록 로드 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 테스트 기록 로드", key="load_history", use_container_width=True):
            with st.spinner("테스트 기록 로드 중..."):
                result = get_user_test_history(user_id)
                if result and result.get("status") == "success":
                    st.session_state.test_history_data = result
                    st.success(f"✅ {result.get('total_tests', 0)}개 테스트를 찾았습니다!")
                else:
                    st.error("테스트 기록 로드 중 오류가 발생했습니다.")
    
    # 테스트 기록 표시
    if st.session_state.test_history_data:
        test_history = st.session_state.test_history_data.get("test_history", [])
        
        if not test_history:
            st.info("👋 아직 테스트를 풀지 않았습니다. 레벨 테스트 탭에서 시작할 수 있습니다!")
            return
        
        st.markdown("---")
        st.subheader(f"📋 완료된 테스트 ({len(test_history)}개)")
        
        # 각 테스트에 대한 카드 표시
        for i, test in enumerate(test_history):
            _show_test_card(i, test, user_id)

def _show_test_card(i, test, user_id):
    """개별 테스트 카드 표시"""
    test_date = test.get("test_date")
    test_score = test.get("total_score", 0)
    test_level = test.get("level", "하")
    correct_count = test.get("correct_count", 0)
    total_questions = test.get("total_questions", 0)
    
    # 날짜 형식화
    if test_date:
        if isinstance(test_date, str):
            try:
                test_date = datetime.fromisoformat(test_date.replace('Z', '+00:00'))
            except:
                test_date = "알 수 없음"
        
        formatted_date = test_date.strftime("%Y.%m.%d %H:%M") if test_date != "알 수 없음" else "알 수 없음"
    else:
        formatted_date = "알 수 없음"
    
    # 테스트 카드
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown(f"**📅 테스트 #{i+1}**")
            st.markdown(f"🕒 {formatted_date}")
        
        with col2:
            st.metric("점수", f"{test_score}")
        
        with col3:
            level_colors = {"하": "🟢", "중": "🟡", "상": "🔴"}
            level_names = {"하": "쉬움", "중": "보통", "상": "어려움"}
            icon = level_colors.get(test_level, "⚪")
            name = level_names.get(test_level, "알 수 없음")
            st.markdown(f"**레벨**")
            st.markdown(f"{icon} {name}")
        
        with col4:
            accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
            st.metric("성공률", f"%{accuracy:.1f}")
        
        # 세부사항 버튼
        if st.button(f"📋 세부사항 보기", key=f"details_{i}"):
            load_test_details(user_id, i)
        
        st.markdown("---")

def load_test_details(user_id, test_index):
    """테스트 세부사항 로드"""
    with st.spinner("테스트 세부사항 로드 중..."):
        result = get_test_details(user_id, test_index)
        
        if result and result.get("status") == "success":
            st.session_state.selected_test_details = result.get("test_details")
            st.rerun()
        else:
            st.error("테스트 세부사항 로드 중 오류가 발생했습니다.")

def show_test_details_view():
    """테스트 세부사항 뷰 표시"""
    test_details = st.session_state.selected_test_details
    
    # 뒤로 가기 버튼
    if st.button("🔙 테스트 기록으로 돌아가기", key="back_to_history"):
        st.session_state.selected_test_details = None
        st.rerun()
    
    st.markdown("## 🔍 테스트 세부사항")
    
    # 테스트 요약
    st.markdown("### 📊 테스트 요약")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총점", test_details.get("total_score", 0))
    with col2:
        st.metric("정답 수", test_details.get("correct_count", 0))
    with col3:
        total_q = test_details.get("total_questions", 0)
        st.metric("총 문제", total_q)
    with col4:
        accuracy = (test_details.get("correct_count", 0) / total_q * 100) if total_q > 0 else 0
        st.metric("성공률", f"%{accuracy:.1f}")
    
    # 상세 문제들
    st.markdown("### 📝 문제 세부사항")
    
    detailed_results = test_details.get("detailed_results", [])
    
    for i, question_result in enumerate(detailed_results):
        _show_question_detail(i, question_result)

def _show_question_detail(i, question_result):
    """개별 문제 세부사항 표시"""
    question_text = question_result.get("question_text", "")
    choices = question_result.get("choices", [])
    correct_answer = question_result.get("correct_answer", 1)
    student_answer = question_result.get("student_answer", 1)
    is_correct = question_result.get("is_correct", False)
    difficulty = question_result.get("difficulty", "하")
    question_id = question_result.get("question_id", "")
    
    # 난이도 색상
    difficulty_names = {"하": "쉬움", "중": "보통", "상": "어려움"}
    
    # 문제 카드
    with st.expander(f"{'✅' if is_correct else '❌'} 문제 {i+1} - {difficulty_names.get(difficulty, '알 수 없음')}", expanded=False):
        # 문제 텍스트
        st.markdown(f"**문제:** {question_text}")
        
        # 선택지 표시
        st.markdown("**선택지:**")
        for j, choice in enumerate(choices, 1):
            if j == correct_answer and j == student_answer:
                # 정답이면서 학생의 답변
                st.success(f"✅ {j}. {choice} ← **정답 (귀하의 답변)**")
            elif j == correct_answer:
                # 정답만
                st.success(f"✅ {j}. {choice} ← **정답**")
            elif j == student_answer:
                # 학생의 틀린 답변만
                st.error(f"❌ {j}. {choice} ← **귀하의 답변**")
            else:
                # 다른 선택지들
                st.write(f"   {j}. {choice}")
        
        # 설명 버튼
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"💡 이 문제 설명", key=f"explain_history_{i}", use_container_width=True):
                show_question_explanation_popup(question_id, student_answer, i)

def show_question_explanation_popup(question_id, student_answer, question_index):
    """문제 설명을 팝업으로 표시"""
    with st.spinner("설명 준비 중..."):
        result = explain_answer(question_id, student_answer)
        
        if result and result.get("status") == "success":
            explanation = result.get("explanation", "")
            is_correct = result.get("is_correct", False)
            cached = result.get("cached", False)
            
            # 설명 모달 스타일 표시
            st.markdown("---")
            st.markdown(f"### 💡 문제 {question_index + 1} 설명")
            
            if cached:
                st.info("📚 이 설명은 이전에 생성되었습니다 (빠른 로딩)")
            
            if is_correct:
                st.success("🎉 이 문제를 정답으로 답했습니다!")
            else:
                st.warning("📖 이 문제에서 틀린 답을 했습니다. 설명은 다음과 같습니다:")
            
            # 설명 박스
            with st.container():
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff6b6b;">
                {explanation}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
        else:
            st.error("설명을 가져오는 중 오류가 발생했습니다.")

# ui/components/questions.py
def show_questions_tab():
    """모든 문제 탭"""
    from api.client import get_collections, get_questions, explain_answer
    
    st.header("모든 문제")
    
    # 컬렉션 가져오기
    collections_result = get_collections()
    
    if collections_result and collections_result.get("status") == "success":
        collections = collections_result.get("collections", [])
        
        if not collections:
            st.warning("아직 문제 컬렉션이 없습니다.")
            return
        
        # 컬렉션 선택
        selected_collection = st.selectbox(
            "컬렉션 선택",
            collections
        )
        
        # 페이지네이션 매개변수
        limit = st.slider("페이지당 문제 수", 5, 50, 10)
        page = st.number_input("페이지", min_value=1, value=1)
        skip = (page - 1) * limit
        
        # 문제 가져오기
        questions_result = get_questions(selected_collection, limit, skip)
        
        if questions_result and questions_result.get("status") == "success":
            questions = questions_result.get("questions", [])
            total = questions_result.get("total", 0)
            
            st.write(f"총 {total}개 문제를 찾았습니다. 페이지 {page}/{(total // limit) + 1}")
            
            # 문제 표시
            for i, question in enumerate(questions):
                _show_individual_question(i, question)
            
            # 페이지네이션 컨트롤
            col1, col2 = st.columns(2)
            with col1:
                if page > 1:
                    if st.button("이전 페이지"):
                        st.experimental_set_query_params(page=page-1)
            with col2:
                if page < (total // limit) + 1:
                    if st.button("다음 페이지"):
                        st.experimental_set_query_params(page=page+1)
        else:
            st.error("문제 로드 중 오류가 발생했습니다.")
    else:
        st.error("컬렉션 로드 중 오류가 발생했습니다.")

def _show_individual_question(i, question):
    """개별 문제 표시"""
    from api.client import explain_answer
    
    question_id = question.get("_id")
    problem_id = question.get("problem_id", "")
    problem = question.get("problem", "")
    choices = question.get("choices", [])
    answer_key = question.get("answer_key")
    difficulty = question.get("difficulty", "")
    
    with st.expander(f"문제 {i+1}: {problem_id}", expanded=False):
        st.markdown(f"{problem}")
        
        for j, choice in enumerate(choices):
            is_correct = j == answer_key
            choice_text = f"{'✓ ' if is_correct else ''}{choice}"
            st.markdown(f"{j}. {choice_text}")
        
        st.markdown(f"난이도: {difficulty}")
        
        # 설명 버튼
        if st.button("설명 요청", key=f"explain_{question_id}"):
            with st.spinner("설명 준비 중..."):
                explanation_result = explain_answer(question_id, answer_key)
                
                if explanation_result and explanation_result.get("status") == "success":
                    explanation = explanation_result.get("explanation", "")
                    st.info(explanation)
                else:
                    st.error("설명 준비 중 오류가 발생했습니다.")

# ui/components/profile.py
def show_profile_tab():
    """프로필 탭"""
    from api.client import update_profile
    
    user = st.session_state.user
    
    st.header("프로필 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 개인 정보")
        st.markdown(f"**이름:** {user.get('name', '미지정')}")
        st.markdown(f"**이메일:** {user.get('email', '미지정')}")
        st.markdown(f"**학과:** {user.get('department', '미지정')}")
        st.markdown(f"**학년:** {user.get('grade', '미지정')}")
    
    with col2:
        st.markdown("#### 테스트 정보")
        test_score = user.get('test_score', 0)
        level = user.get('level', '아직 테스트되지 않음')
        
        st.markdown(f"**총점:** {test_score}")
        st.markdown(f"**레벨:** {level}")
        
        # 레벨 설명
        from config.settings import LEVEL_DESCRIPTIONS
        if level in LEVEL_DESCRIPTIONS:
            st.info(LEVEL_DESCRIPTIONS[level])
    
    st.markdown("---")
    
    # 프로필 업데이트 폼
    st.subheader("프로필 정보 업데이트")
    
    update_dept = st.text_input("학과", value=user.get('department', ''))
    update_grade = st.number_input("학년", min_value=1, max_value=12, value=user.get('grade', 1))
    
    if st.button("정보 업데이트"):
        with st.spinner("정보 업데이트 중..."):
            result = update_profile(user.get('email'), update_dept, update_grade)
            
            if result and result.get("status") == "success":
                st.session_state.user = result.get("user")
                st.success("프로필 정보가 성공적으로 업데이트되었습니다!")
                #st.rerun()
            else:
                st.error("프로필 업데이트 중 오류가 발생했습니다.")