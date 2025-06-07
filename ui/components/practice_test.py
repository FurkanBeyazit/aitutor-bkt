import streamlit as st
from api.client import get_practice_question, submit_practice_answer, explain_answer
from config.settings import DIFFICULTY_NAMES, DIFFICULTY_COLORS

def show_practice_test_tab():
    """연습 테스트 탭 표시"""
    st.header("🎯 연습 테스트")
    
    # 연습 테스트 세션 상태 초기화
    if "current_practice_question" not in st.session_state:
        st.session_state.current_practice_question = None
    if "practice_answer_submitted" not in st.session_state:
        st.session_state.practice_answer_submitted = False
    if "practice_explanation" not in st.session_state:
        st.session_state.practice_explanation = None
    
    # 문제가 풀렸고 설명이 있으면 결과 표시
    if st.session_state.practice_explanation:
        show_practice_results()
        return
    
    # 문제가 로드되었고 답변이 제출되지 않았으면 문제 표시
    if st.session_state.current_practice_question and not st.session_state.practice_answer_submitted:
        show_practice_question()
        return
    
    # 메인 연습 테스트 페이지
    _show_practice_main_page()

def _show_practice_main_page():
    """연습 테스트 메인 페이지"""
    st.write("다양한 난이도의 문제를 풀어보며 자신을 발전시킬 수 있습니다.")
    
    # 난이도 선택
    st.subheader("난이도 선택")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📗 쉬운 문제", key="easy_practice", use_container_width=True):
            load_practice_question("하")
    
    with col2:
        if st.button("📙 보통 문제", key="medium_practice", use_container_width=True):
            load_practice_question("중")
    
    with col3:
        if st.button("📕 어려운 문제", key="hard_practice", use_container_width=True):
            load_practice_question("상")
    
    # 정보 카드
    st.markdown("---")
    st.subheader("📊 레벨 설명")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **📗 쉬운 레벨**
        - 기본 개념
        - 간단한 문제
        - 일상 연습에 이상적
        """)
    
    with col2:
        st.warning("""
        **📙 보통 레벨**
        - 응용 문제
        - 분석이 필요한 문제
        - 지식 강화
        """)
    
    with col3:
        st.error("""
        **📕 어려운 레벨**
        - 복잡한 시나리오
        - 심층 분석
        - 전문가 수준
        """)

def load_practice_question(difficulty):
    """지정된 난이도의 연습 문제 로드"""
    with st.spinner(f"문제 준비 중..."):
        result = get_practice_question(difficulty)
        
        if result and result.get("status") == "success":
            st.session_state.current_practice_question = result.get("question")
            st.session_state.practice_answer_submitted = False
            st.session_state.practice_explanation = None
            st.rerun()
        else:
            st.error("문제 로드 중 오류가 발생했습니다.")

def show_practice_question():
    """연습 문제 표시"""
    question = st.session_state.current_practice_question
    
    if not question:
        st.error("문제 정보를 찾을 수 없습니다.")
        return
    
    # 문제 정보 가져오기
    question_id = question.get("_id")
    problem_text = question.get("Problem", question.get("problem", ""))
    choices = question.get("Choices", question.get("choices", []))
    difficulty = question.get("difficulty", "알 수 없음")
    
    # 난이도 표시
    color = DIFFICULTY_COLORS.get(difficulty, "info")
    name = DIFFICULTY_NAMES.get(difficulty, "알 수 없음")
    
    getattr(st, color)(f"**난이도:** {name}")
    
    # 문제 텍스트
    st.markdown(f"### 문제")
    st.markdown(f"**{problem_text}**")
    
    # 선택지
    if choices:
        st.markdown("### 선택지")
        
        # 라디오 버튼으로 선택지 제공
        selected_option = st.radio(
            "답을 선택하세요:",
            range(1, len(choices) + 1),
            format_func=lambda x: f"{x}. {choices[x-1]}",
            key="practice_answer",
            index=None
        )
        
        # 답변 제출 버튼
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("답변 제출", key="submit_practice", use_container_width=True, disabled=selected_option is None):
                if selected_option:
                    submit_practice_answer_func(question_id, selected_option)
    else:
        st.error("문제 선택지를 찾을 수 없습니다.")
    
    # 새 문제 가져오기 버튼
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 새 문제 가져오기", key="new_practice_question", use_container_width=True):
            st.session_state.current_practice_question = None
            st.session_state.practice_answer_submitted = False
            st.session_state.practice_explanation = None
            st.rerun()

def submit_practice_answer_func(question_id, student_answer):
    """연습 테스트 답변 제출 및 설명 가져오기"""
    with st.spinner("답변을 평가 중..."):
        # 먼저 답변 확인
        answer_result = submit_practice_answer(question_id, student_answer)
        
        if answer_result and answer_result.get("status") == "success":
            # 그 다음 설명 가져오기
            explanation_result = explain_answer(question_id, student_answer)
            
            if explanation_result and explanation_result.get("status") == "success":
                # 결과 합치기
                combined_result = {
                    **answer_result,
                    **explanation_result
                }
                
                st.session_state.practice_explanation = combined_result
                st.session_state.practice_answer_submitted = True
                st.rerun()
            else:
                st.error("설명을 가져오는 중 오류가 발생했습니다.")
        else:
            st.error("답변 평가 중 오류가 발생했습니다.")

def show_practice_results():
    """연습 테스트 결과 표시"""
    result = st.session_state.practice_explanation
    question = st.session_state.current_practice_question
    
    if not result or not question:
        st.error("결과 정보를 찾을 수 없습니다.")
        return
    
    # 문제 정보
    problem_text = question.get("Problem", question.get("problem", ""))
    choices = question.get("Choices", question.get("choices", []))
    difficulty = question.get("difficulty", "알 수 없음")
    
    # 결과 정보
    is_correct = result.get("is_correct", False)
    correct_answer = result.get("correct_answer", 1)
    student_answer = result.get("student_answer", 1)
    explanation = result.get("explanation", "설명을 찾을 수 없습니다.")
    
    # 난이도
    difficulty_name = DIFFICULTY_NAMES.get(difficulty, "알 수 없음")
    
    # 문제 다시 표시
    st.markdown(f"### 문제 ({difficulty_name} 레벨)")
    st.markdown(f"**{problem_text}**")
    
    # 선택지 표시
    st.markdown("### 선택지")
    for i, choice in enumerate(choices, 1):
        if i == correct_answer and i == student_answer:
            # 정답이면서 학생의 답변
            st.success(f"✅ {i}. {choice} ← **정답 (귀하의 답변)**")
        elif i == correct_answer:
            # 정답만
            st.success(f"✅ {i}. {choice} ← **정답**")
        elif i == student_answer:
            # 학생의 틀린 답변만
            st.error(f"❌ {i}. {choice} ← **귀하의 답변**")
        else:
            # 다른 선택지들
            st.write(f"   {i}. {choice}")
    
    # 결과
    st.markdown("---")
    if is_correct:
        st.success("🎉 **축하합니다! 정답입니다.**")
    else:
        st.error("❌ **틀렸습니다. 정답은 위에 표시되어 있습니다.**")
    
    # 설명
    st.markdown("### 💡 설명")
    st.info(explanation)
    
    # 버튼들
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 같은 레벨의 새 문제", key="same_level_new", use_container_width=True):
            difficulty_map = {"쉬움": "하", "보통": "중", "어려움": "상"}
            current_difficulty = difficulty_map.get(difficulty_name, "하")
            load_practice_question(current_difficulty)
    
    with col2:
        if st.button("🏠 메인 페이지로 돌아가기", key="back_to_main", use_container_width=True):
            st.session_state.current_practice_question = None
            st.session_state.practice_answer_submitted = False
            st.session_state.practice_explanation = None
            st.rerun()