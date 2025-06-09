# ui/components/adaptive_test_component.py
import streamlit as st
from datetime import datetime, timedelta
from api.client import api_request, submit_test

def show_adaptive_test_component():
    """적응형 테스트 전용 컴포넌트"""
    st.header("🎯 유형별 맞춤형 학습 테스트")
    
    # 세션 상태 초기화
    if "adaptive_test" not in st.session_state:
        st.session_state.adaptive_test = None
    if "adaptive_answers" not in st.session_state:
        st.session_state.adaptive_answers = {}
    if "adaptive_submitted" not in st.session_state:
        st.session_state.adaptive_submitted = False
    if "adaptive_results" not in st.session_state:
        st.session_state.adaptive_results = None
    if "adaptive_question_index" not in st.session_state:
        st.session_state.adaptive_question_index = 0
    
    # 결과가 있으면 결과 표시
    if st.session_state.adaptive_submitted and st.session_state.adaptive_results:
        show_adaptive_test_results()
        return
    
    # 테스트가 로드되었으면 테스트 진행
    if st.session_state.adaptive_test:
        show_adaptive_test_interface()
        return
    
    # 테스트 시작 페이지
    show_adaptive_test_start_page()

def show_adaptive_test_start_page():
    """적응형 테스트 시작 페이지"""
    user_id = st.session_state.user.get("user_id")
    
    st.info("""
    ### 🧠 맞춤형 학습 테스트란?
    - 당신의 **약한 문제 유형**에 집중한 테스트입니다
    - BKT 알고리즘이 당신의 학습 상태를 분석하여 **최적의 문제**를 제공합니다
    - 문제 수: **10문제**
    - 시간 제한: **15분**
    """)
    
    # 약점 유형 미리보기
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 내 약점 유형 확인", use_container_width=True):
            show_weakness_preview(user_id)
    
    with col2:
        if st.button("🚀 맞춤형 테스트 시작", type="primary", use_container_width=True):
            start_adaptive_test(user_id)

def show_weakness_preview(user_id):
    """약점 유형 미리보기"""
    with st.spinner("약점 분석 중..."):
        result = api_request(f"bkt/weak-types/{user_id}?threshold=0.6")
        
        if result and result.get("status") == "success":
            weak_types = result.get("weak_types", [])
            
            if weak_types:
                st.subheader("🎯 집중 개선이 필요한 유형들")
                
                for i, weak_type in enumerate(weak_types[:5], 1):
                    type_name = weak_type.get("type", "알 수 없음")
                    mastery = weak_type.get("mastery", 0)
                    attempts = weak_type.get("attempts", 0)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{i}. {type_name}**")
                    with col2:
                        st.metric("습득도", f"{mastery*100:.1f}%")
                    with col3:
                        st.metric("시도", f"{attempts}회")
                
                st.success("맞춤형 테스트는 이러한 약점 유형에 집중합니다!")
            else:
                st.success("🎉 모든 유형에서 우수한 성과를 보이고 있습니다!")
                st.info("맞춤형 테스트는 전반적인 실력 향상에 도움이 됩니다.")
        else:
            st.error("약점 분석 중 오류가 발생했습니다.")

def start_adaptive_test(user_id):
    """적응형 테스트 시작"""
    with st.spinner("맞춤형 테스트 준비 중..."):
        result = api_request(f"exam/adaptive-test-by-type/{user_id}?num_questions=10")
        
        if result and result.get("status") == "success":
            st.session_state.adaptive_test = result.get("adaptive_test", [])
            st.session_state.adaptive_test_info = result.get("test_info", {})
            st.session_state.adaptive_answers = {}
            st.session_state.adaptive_submitted = False
            st.session_state.adaptive_results = None
            st.session_state.adaptive_question_index = 0
            st.session_state.adaptive_start_time = datetime.now()
            # ⭐ NEW: Navigation states 초기화
            st.session_state.adaptive_nav_button_clicked = False
            st.session_state.adaptive_prev_selectbox_index = 0
            
            st.success("✅ 맞춤형 테스트가 준비되었습니다!")
            st.rerun()
        else:
            st.error("❌ 맞춤형 테스트 준비에 실패했습니다.")

def show_adaptive_test_interface():
    """적응형 테스트 진행 인터페이스"""
    test = st.session_state.adaptive_test
    test_info = st.session_state.get("adaptive_test_info", {})
    
    if not test:
        st.error("테스트 문제를 불러올 수 없습니다.")
        return
    
    # 타이머 표시 (15분)
    start_time = st.session_state.adaptive_start_time
    duration_minutes = 15
    current_time = datetime.now()
    elapsed_time = current_time - start_time
    remaining_time = timedelta(minutes=duration_minutes) - elapsed_time
    
    # 시간 종료 확인
    if remaining_time.total_seconds() <= 0:
        st.error("⏰ 시간이 종료되었습니다! 자동으로 제출합니다.")
        submit_adaptive_test()
        return
    
    # 타이머 표시
    minutes = int(remaining_time.total_seconds() // 60)
    seconds = int(remaining_time.total_seconds() % 60)
    
    if minutes <= 2:
        st.error(f"⏰ 남은 시간: {minutes:02d}:{seconds:02d}")
    elif minutes <= 5:
        st.warning(f"⏰ 남은 시간: {minutes:02d}:{seconds:02d}")
    else:
        st.info(f"⏰ 남은 시간: {minutes:02d}:{seconds:02d}")
    
    # 진행률 표시
    current_index = st.session_state.adaptive_question_index
    answered_count = len(st.session_state.adaptive_answers)
    progress = answered_count / len(test)
    
    st.progress(progress)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("현재 문제", f"{current_index + 1}/{len(test)}")
    with col2:
        st.metric("답변 완료", f"{answered_count}/{len(test)}")
    with col3:
        st.metric("진행률", f"{progress*100:.0f}%")
    
    # 테스트 정보 표시
    target_types = test_info.get("target_types", [])
    if target_types:
        st.info(f"🎯 집중 유형: {', '.join(target_types[:3])}")
    
    # 현재 문제 표시
    current_question = test[current_index]
    show_adaptive_question(current_question, current_index, len(test))
    
    # 네비게이션
    show_adaptive_navigation(len(test))

def show_adaptive_question(question, question_index, total_questions):
    """적응형 테스트 문제 표시"""
    question_id = question.get("_id")
    problem_text = question.get("Problem", question.get("problem", f"문제 {question_index + 1}"))
    choices = question.get("Choices", question.get("choices", []))
    difficulty = question.get("difficulty", "")
    bkt_metadata = question.get("bkt_metadata", {})
    
    # BKT 메타데이터 표시
    target_type = bkt_metadata.get("target_type", "")
    reason = bkt_metadata.get("reason", "")
    
    if target_type and reason:
        st.success(f"🧠 {reason} - **{target_type}** 유형")
    
    # 난이도 표시
    if difficulty:
        difficulty_names = {"하": "쉬움", "중": "보통", "상": "어려움"}
        difficulty_colors = {"하": "success", "중": "warning", "상": "error"}
        difficulty_name = difficulty_names.get(difficulty, "알 수 없음")
        color = difficulty_colors.get(difficulty, "info")
        getattr(st, color)(f"🎯 난이도: {difficulty_name}")
    
    # 문제 텍스트
    st.markdown(f"### 문제 {question_index + 1}")
    st.markdown(f"**{problem_text}**")
    
    # 현재 선택된 답변
    current_answer = st.session_state.adaptive_answers.get(question_id, None)
    
    # 선택지 표시
    if choices and len(choices) > 0:
        st.markdown("### 선택지")
        
        selected_index = None
        if current_answer is not None:
            selected_index = current_answer - 1
            
        choice_options = [f"{i + 1}. {choice}" for i, choice in enumerate(choices)]
        
        selected_choice = st.radio(
            "답을 선택하세요:",
            choice_options,
            index=selected_index,
            key=f"adaptive_radio_{question_index}_{question_id}"
        )
        
        if selected_choice is not None:
            choice_index = choice_options.index(selected_choice)
            answer_value = choice_index + 1
            
            if current_answer != answer_value:
                st.session_state.adaptive_answers[question_id] = answer_value
                st.success(f"✅ 선택지 {answer_value}번이 선택되었습니다!")
        
        if current_answer is None:
            st.info("🔍 아직 답을 선택하지 않았습니다.")
    else:
        st.error("이 문제의 선택지를 찾을 수 없습니다.")

def show_adaptive_navigation(total_questions):
    """적응형 테스트 네비게이션 - Diagnosis test logic ile aynı"""
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    current_index = st.session_state.adaptive_question_index
    
    # ⭐ NAVIGATION BUTTON STATE TRACKING 추가 (diagnosis test'ten)
    if "adaptive_nav_button_clicked" not in st.session_state:
        st.session_state.adaptive_nav_button_clicked = False
    
    with col1:
        # 이전 문제 - FIXED: Diagnosis test logic
        if current_index > 0:
            if st.button("⬅️ 이전", key="adaptive_prev", use_container_width=True):
                if not st.session_state.adaptive_nav_button_clicked:
                    st.session_state.adaptive_nav_button_clicked = True
                    new_index = max(0, current_index - 1)
                    print(f"🔍 [DEBUG] Adaptive Previous button clicked: {current_index} -> {new_index}")
                    st.session_state.adaptive_question_index = new_index
                    st.rerun()
        else:
            st.button("⬅️ 이전", key="adaptive_prev_disabled", disabled=True, use_container_width=True)
    
    with col2:
        # 다음 문제 - FIXED: Diagnosis test logic
        if current_index < total_questions - 1:
            if st.button("➡️ 다음", key="adaptive_next", use_container_width=True):
                if not st.session_state.adaptive_nav_button_clicked:
                    st.session_state.adaptive_nav_button_clicked = True
                    new_index = min(total_questions - 1, current_index + 1)
                    print(f"🔍 [DEBUG] Adaptive Next button clicked: {current_index} -> {new_index}")
                    st.session_state.adaptive_question_index = new_index
                    st.rerun()
        else:
            st.button("➡️ 다음", key="adaptive_next_disabled", disabled=True, use_container_width=True)
    
    with col3:
        # 문제 선택 - FIXED: Diagnosis test logic ile aynı
        selectbox_key = f"adaptive_question_selector"
        
        # 현재 인덱스가 변경되었는지 확인
        prev_selectbox_index = st.session_state.get("adaptive_prev_selectbox_index", current_index)
        
        # 문제 옵션들
        question_options = [f"문제 {i+1}" for i in range(total_questions)]
        
        # Bounds check
        safe_current_index = min(current_index, total_questions - 1)
        
        selected_option = st.selectbox(
            "문제로 이동",
            question_options,
            index=safe_current_index,
            key=selectbox_key
        )
        
        # Selectbox selection'dan index çıkar
        if selected_option:
            selected_num = int(selected_option.split(" ")[1]) - 1  # "문제 X" -> X-1 (0-based)
            
            # Bounds check
            safe_selected_num = max(0, min(selected_num, total_questions - 1))
            
            # Sadece gerçekten değiştiğinde navigate et
            if safe_selected_num != current_index and safe_selected_num != prev_selectbox_index:
                print(f"🔍 [DEBUG] Adaptive Selectbox navigation: {current_index} -> {safe_selected_num}")
                st.session_state.adaptive_question_index = safe_selected_num
                st.session_state.adaptive_prev_selectbox_index = safe_selected_num
                st.rerun()
            else:
                st.session_state.adaptive_prev_selectbox_index = current_index
    
    with col4:
        # 제출 버튼
        answered_count = len(st.session_state.adaptive_answers)
        print(f"🔍 [DEBUG] Adaptive Submit button - Answered count: {answered_count}")
        
        if answered_count > 0:
            if st.button("🚀 제출", key="adaptive_submit", type="primary", use_container_width=True):
                print(f"🔍 [DEBUG] Adaptive Submit button clicked")
                submit_adaptive_test()
        else:
            st.button("🚀 제출", key="adaptive_submit_disabled", disabled=True, use_container_width=True)
    
    # Navigation button flag'i reset et (diagnosis test'teki gibi)
    if st.session_state.get("adaptive_nav_button_clicked", False):
        st.session_state.adaptive_nav_button_clicked = False

def submit_adaptive_test():
    """적응형 테스트 제출"""
    with st.spinner("맞춤형 테스트 평가 중..."):
        user_id = st.session_state.user.get("user_id")
        answers = st.session_state.adaptive_answers.copy()
        
        # 미답변 문제들 처리 (API에서 처리하도록 함)
        test = st.session_state.adaptive_test
        for question in test:
            question_id = question.get("_id")
            if question_id not in answers:
                # 기본값 설정하지 않음
                pass
        
        # API에 제출 (일반 submit_test 엔드포인트 사용)
        result = api_request("exam/submit-test", method="POST", data={
            "user_id": user_id,
            "answers": answers
        })
        
        if result and result.get("status") == "success":
            # 결과 저장
            st.session_state.adaptive_results = result
            st.session_state.adaptive_submitted = True
            
            # 사용자 정보 업데이트
            st.session_state.user["test_score"] = result.get("score", 0)
            st.session_state.user["level"] = result.get("level", "하")
            
            st.success("맞춤형 테스트가 성공적으로 완료되었습니다!")
            st.rerun()
        else:
            st.error("테스트 평가 중 오류가 발생했습니다.")

def show_adaptive_test_results():
    """적응형 테스트 결과 표시"""
    results = st.session_state.adaptive_results
    test_info = st.session_state.get("adaptive_test_info", {})
    
    st.header("🎉 맞춤형 테스트 결과")
    
    # 결과 요약
    score = results.get("score", 0)
    level = results.get("level", "하")
    correct_count = results.get("correct_count", 0)
    total_questions = results.get("total_questions", 0)
    accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총점", f"{score}")
    with col2:
        st.metric("정확도", f"{accuracy:.1f}%")
    with col3:
        st.metric("레벨", f"{level}")
    
    # BKT 분석 결과
    bkt_analysis = results.get("bkt_analysis", {})
    if bkt_analysis:
        st.subheader("🧠 학습 분석 결과")
        
        overall_mastery = bkt_analysis.get("overall_mastery", 0)
        weak_types = bkt_analysis.get("weak_types", [])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("전체 습득도", f"{overall_mastery*100:.1f}%")
        with col2:
            improvements = bkt_analysis.get("type_improvements", 0)
            st.metric("유형별 개선", f"{improvements}개")
        
        if weak_types:
            st.info("계속 집중이 필요한 유형들:")
            for weak_type in weak_types[:3]:
                type_name = weak_type.get("type", "")
                mastery = weak_type.get("mastery", 0)
                st.write(f"• **{type_name}**: {mastery*100:.1f}%")
    
    # 타겟 유형 결과
    target_types = test_info.get("target_types", [])
    if target_types:
        st.subheader("🎯 집중 학습 유형 결과")
        st.success(f"다음 유형들에 집중했습니다: {', '.join(target_types)}")
    
    # 다시 테스트 버튼들
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 새로운 맞춤형 테스트", use_container_width=True):
            # 세션 초기화 - ⭐ navigation states도 포함
            st.session_state.adaptive_test = None
            st.session_state.adaptive_answers = {}
            st.session_state.adaptive_submitted = False
            st.session_state.adaptive_results = None
            st.session_state.adaptive_question_index = 0
            st.session_state.adaptive_nav_button_clicked = False
            st.session_state.adaptive_prev_selectbox_index = 0
            st.rerun()
    
    with col2:
        if st.button("📊 학습 분석 보기", use_container_width=True):
            # BKT 탭으로 이동하는 방법을 구현해야 함
            st.info("학습 분석 탭으로 이동하여 상세 분석을 확인하세요.")
    
    with col3:
        if st.button("🏠 메인으로 돌아가기", use_container_width=True):
            # 모든 세션 초기화 - ⭐ navigation states도 포함
            st.session_state.adaptive_test = None
            st.session_state.adaptive_answers = {}
            st.session_state.adaptive_submitted = False
            st.session_state.adaptive_results = None
            st.session_state.adaptive_question_index = 0
            st.session_state.adaptive_nav_button_clicked = False
            st.session_state.adaptive_prev_selectbox_index = 0
            st.rerun()