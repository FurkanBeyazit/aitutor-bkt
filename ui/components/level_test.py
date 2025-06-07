import streamlit as st
import time
from datetime import datetime, timedelta
from api.client import get_level_test, submit_test
from ui.components.test_result import show_test_results_with_multiple_charts
# timer_component import (eğer dosya yoksa basit versiyonu kullanacağız)
try:
    from ui.components.timer_component import (
        show_exam_timer, show_progress_bar, 
        show_question_navigator, show_simple_timer_display, show_question_grid
    )
    HAS_TIMER_COMPONENT = True
except ImportError:
    HAS_TIMER_COMPONENT = False

def show_level_test_tab():
    """레벨 테스트 탭 표시"""
    if st.session_state.test_submitted and st.session_state.test_results:
        show_test_results_with_multiple_charts()
    elif st.session_state.current_test:
        show_timed_test_interface()
    else:
        _show_test_start_page()

def _show_test_start_page():
    """테스트 시작 페이지"""
    st.header("🎯 레벨 판정 시험")
    
    # 테스트 정보 카드
    st.info("""
    ### 📋 시험 정보
    - **문제 수**: 30문제
    - **시험 시간**: 30분
    - **문제 유형**: 객관식 (5지 선다)
    - **난이도**: 쉬움/보통/어려움 혼합
    """)
    
    st.warning("""
    ### ⚠️ 주의사항
    - 시험이 시작되면 30분 타이머가 작동합니다
    - 시간이 종료되면 자동으로 제출됩니다
    - 문제를 건너뛸 수 있지만, 나중에 돌아와서 답할 수 있습니다
    - 모든 문제에 답하는 것을 권장합니다
    """)
    
    # 테스트 시작 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 레벨 테스트 시작", key="start_test_button", use_container_width=True):
            with st.spinner("테스트 준비 중..."):
                result = get_level_test()
                
                if result and result.get("status") == "success":
                    # 테스트를 세션 상태에 저장
                    st.session_state.current_test = result.get("test", [])
                    st.session_state.current_answers = {}
                    st.session_state.test_submitted = False
                    st.session_state.test_results = None
                    
                    # 타이머 관련 세션 상태 초기화
                    st.session_state.test_start_time = datetime.now()
                    st.session_state.test_duration_minutes = 30
                    st.session_state.current_question_index = 0
                    st.session_state.auto_submitted = False
                    st.session_state.show_submit_confirmation = False
                    
                    st.success("테스트 준비 완료!")
                    st.rerun()
                else:
                    st.error("테스트 준비 중 오류가 발생했습니다.")

def show_timed_test_interface():
    """타이머가 있는 테스트 인터페이스"""
    test = st.session_state.current_test
    
    if not test:
        st.warning("테스트 문제를 불러올 수 없습니다.")
        return
    
    print(f"🔍 [DEBUG] show_timed_test_interface() called")
    print(f"  - Test length: {len(test)}")
    print(f"  - Current question index: {st.session_state.current_question_index}")
    print(f"  - Answered questions: {len(st.session_state.current_answers)}")
    print(f"  - Test submitted: {st.session_state.get('test_submitted', False)}")
    
    # Index sınır kontrolü
    if st.session_state.current_question_index >= len(test):
        print(f"🚨 [DEBUG] Index out of bounds! Correcting: {st.session_state.current_question_index} -> {len(test) - 1}")
        st.session_state.current_question_index = len(test) - 1
    
    # 시간 계산
    start_time = st.session_state.test_start_time
    duration_minutes = st.session_state.test_duration_minutes
    current_time = datetime.now()
    elapsed_time = current_time - start_time
    remaining_time = timedelta(minutes=duration_minutes) - elapsed_time
    
    print(f"🔍 [DEBUG] Timer info:")
    print(f"  - Start time: {start_time}")
    print(f"  - Current time: {current_time}")
    print(f"  - Remaining seconds: {remaining_time.total_seconds()}")
    
    # 시간이 종료되었는지 확인
    if remaining_time.total_seconds() <= 0 and not st.session_state.auto_submitted:
        print(f"🚨 [DEBUG] Time expired! Auto-submitting...")
        st.error("⏰ 시간이 종료되었습니다! 자동으로 제출합니다.")
        auto_submit_test()
        return
    
    # 타이머 표시
    if HAS_TIMER_COMPONENT:
        time_expired = show_exam_timer(start_time, duration_minutes)
    else:
        time_expired = show_simple_timer_display(start_time, duration_minutes)
    
    # 진행률 표시
    current_question_index = st.session_state.current_question_index
    answered_questions = set()
    for i, question in enumerate(test):
        question_id = question.get("_id")
        if question_id in st.session_state.current_answers:
            answered_questions.add(i)
    
    print(f"🔍 [DEBUG] Progress info:")
    print(f"  - Current index: {current_question_index}")
    print(f"  - Answered questions indices: {answered_questions}")
    
    if HAS_TIMER_COMPONENT:
        show_progress_bar(
            current_question_index + 1, 
            len(test), 
            len(answered_questions)
        )
    else:
        # 간단한 진행률 표시
        progress = len(answered_questions) / len(test)
        st.progress(progress)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("현재 문제", f"{current_question_index + 1}/{len(test)}")
        with col2:
            st.metric("답변 완료", f"{len(answered_questions)}/{len(test)}")
        with col3:
            st.metric("진행률", f"{progress*100:.0f}%")
    
    # 현재 문제 표시
    current_question = test[current_question_index]
    show_current_question(current_question, current_question_index, len(test))
    
    # 네비게이션 컨트롤
    show_navigation_controls(len(test))
    
    # 문제 네비게이터 표시
    if HAS_TIMER_COMPONENT:
        show_question_navigator(
            len(test),
            current_question_index,
            answered_questions
        )
    else:
        show_question_grid(
            len(test),
            current_question_index,
            answered_questions
        )

def show_current_question(question, question_index, total_questions):
    """현재 문제 표시"""
    question_id = question.get("_id")
    problem_text = question.get("Problem", question.get("problem", f"문제 {question_index + 1}"))
    choices = question.get("Choices", question.get("choices", []))
    difficulty = question.get("difficulty", "")
    
    print(f"🔍 [DEBUG] Current question:")
    print(f"  - Question index: {question_index}")
    print(f"  - Question ID: {question_id}")
    print(f"  - Choices count: {len(choices)}")
    print(f"  - Current answer: {st.session_state.current_answers.get(question_id, 'None')}")
    
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
    
    # 현재 선택된 답변 가져오기
    current_answer = st.session_state.current_answers.get(question_id, None)
    
    # 선택지 표시 - RADIO BUTTON 방식으로 변경하여 selection tracking 보장
    if choices and len(choices) > 0:
        st.markdown("### 선택지")
        
        # Radio button index 계산 (1-based에서 0-based로)
        selected_index = None
        if current_answer is not None:
            selected_index = current_answer - 1  # 1-based to 0-based
            
        # Radio button ile seçim yap
        choice_options = [f"{i + 1}. {choice}" for i, choice in enumerate(choices)]
        
        # UNIQUE KEY BURDADA DEĞİŞTİRİLDİ
        radio_key = f"question_radio_{question_index}_{question_id}"
        
        selected_choice = st.radio(
            "답을 선택하세요:",
            choice_options,
            index=selected_index,  # Previously selected option (or None)
            key=radio_key
        )
        
        # Seçim yapıldıysa kaydet
        if selected_choice is not None:
            # Radio button selection'dan index çıkar (0-based)
            choice_index = choice_options.index(selected_choice)
            answer_value = choice_index + 1  # Convert to 1-based
            
            # Önceki cevapla farklıysa güncelle
            if current_answer != answer_value:
                st.session_state.current_answers[question_id] = answer_value
                print(f"🔍 [DEBUG] Answer updated: {answer_value} for question {question_id}")
                st.success(f"✅ 선택지 {answer_value}번이 선택되었습니다!")
            
    else:
        st.error("이 문제의 선택지를 찾을 수 없습니다.")

def show_navigation_controls(total_questions):
    """Streamlit native navigation controls"""
    
    # Submit confirmation kontrolü
    if st.session_state.get("show_submit_confirmation", False):
        show_submit_confirmation()
        return  # Submit confirmation gösteriliyorsa navigation'ı gösterme
    
    st.markdown("---")
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    current_index = st.session_state.current_question_index
    
    print(f"🔍 [DEBUG] Navigation controls:")
    print(f"  - Current index: {current_index}")
    print(f"  - Total questions: {total_questions}")
    print(f"  - Can go prev: {current_index > 0}")
    print(f"  - Can go next: {current_index < total_questions - 1}")
    
    # NAVIGATION BUTTON STATE TRACKING 추가
    if "nav_button_clicked" not in st.session_state:
        st.session_state.nav_button_clicked = False
    
    with col1:
        # 이전 문제
        if current_index > 0:
            if st.button("⬅️ 이전", key="prev_question", use_container_width=True):
                if not st.session_state.nav_button_clicked:
                    st.session_state.nav_button_clicked = True
                    new_index = max(0, current_index - 1)
                    print(f"🔍 [DEBUG] Previous button clicked: {current_index} -> {new_index}")
                    st.session_state.current_question_index = new_index
                    st.rerun()
        else:
            st.button("⬅️ 이전", key="prev_question_disabled", disabled=True, use_container_width=True)
    
    with col2:
        # 다음 문제
        if current_index < total_questions - 1:
            if st.button("➡️ 다음", key="next_question", use_container_width=True):
                if not st.session_state.nav_button_clicked:
                    st.session_state.nav_button_clicked = True
                    new_index = min(total_questions - 1, current_index + 1)
                    print(f"🔍 [DEBUG] Next button clicked: {current_index} -> {new_index}")
                    st.session_state.current_question_index = new_index
                    st.rerun()
        else:
            st.button("➡️ 다음", key="next_question_disabled", disabled=True, use_container_width=True)
    
    with col3:
        # SELECTBOX NAVIGATION - STABLE VERSION
        # Selectbox state tracking을 개선
        selectbox_key = f"question_selector"
        
        # 현재 인덱스가 변경되었는지 확인
        prev_selectbox_index = st.session_state.get("prev_selectbox_index", current_index)
        
        # 문제 옵션들
        question_options = [f"문제 {i+1}" for i in range(total_questions)]
        
        selected_option = st.selectbox(
            "문제로 이동",
            question_options,
            index=current_index,
            key=selectbox_key
        )
        
        # Selectbox selection'dan index çıkar
        if selected_option:
            selected_num = int(selected_option.split(" ")[1]) - 1  # "문제 X" -> X-1 (0-based)
            
            # Sadece gerçekten değiştiğinde navigate et
            if selected_num != current_index and selected_num != prev_selectbox_index:
                print(f"🔍 [DEBUG] Selectbox navigation: {current_index} -> {selected_num}")
                st.session_state.current_question_index = selected_num
                st.session_state.prev_selectbox_index = selected_num
                st.rerun()
            else:
                st.session_state.prev_selectbox_index = current_index
    
    with col4:
        # 건너뛰기 (다음 미답변 문제로)
        if st.button("⏭️ 건너뛰기", key="skip_question", use_container_width=True):
            if not st.session_state.nav_button_clicked:
                st.session_state.nav_button_clicked = True
                next_unanswered = find_next_unanswered_question()
                if next_unanswered is not None:
                    print(f"🔍 [DEBUG] Skip to unanswered: {current_index} -> {next_unanswered}")
                    st.session_state.current_question_index = next_unanswered
                    st.rerun()
                else:
                    st.session_state.nav_button_clicked = False  # Reset flag
                    st.info("모든 문제가 답변되었습니다!")
    
    with col5:
        # 테스트 제출
        answered_count = len(st.session_state.current_answers)
        print(f"🔍 [DEBUG] Submit button - Answered count: {answered_count}")
        
        if answered_count > 0:
            if st.button("🚀 제출", key="submit_test", type="primary", use_container_width=True):
                print(f"🔍 [DEBUG] Submit button clicked - showing confirmation")
                st.session_state.show_submit_confirmation = True
                st.rerun()
        else:
            st.button("🚀 제출", key="submit_test_disabled", disabled=True, use_container_width=True)
    
    # Navigation button flag'i reset et (bu fonksiyonun sonunda)
    if st.session_state.get("nav_button_clicked", False):
        st.session_state.nav_button_clicked = False

def find_next_unanswered_question():
    """다음 미답변 문제 찾기"""
    test = st.session_state.current_test
    current_index = st.session_state.current_question_index
    answered_questions = st.session_state.current_answers
    
    # 현재 문제 다음부터 검색
    for i in range(current_index + 1, len(test)):
        question_id = test[i].get("_id")
        if question_id not in answered_questions:
            return i
    
    # 처음부터 현재 문제까지 검색
    for i in range(0, current_index):
        question_id = test[i].get("_id")
        if question_id not in answered_questions:
            return i
    
    return None  # 모든 문제가 답변됨

def show_submit_confirmation():
    """제출 확인 모달"""
    total_questions = len(st.session_state.current_test)
    answered_count = len(st.session_state.current_answers)
    unanswered_count = total_questions - answered_count
    
    print(f"🔍 [DEBUG] Submit confirmation:")
    print(f"  - Total questions: {total_questions}")
    print(f"  - Answered: {answered_count}")
    print(f"  - Unanswered: {unanswered_count}")
    print(f"  - Current answers: {list(st.session_state.current_answers.keys())}")
    
    st.markdown("---")
    st.subheader("⚠️ 테스트 제출 확인")
    
    if unanswered_count > 0:
        st.warning(f"아직 {unanswered_count}개 문제가 답변되지 않았습니다.")
        st.info("답변하지 않은 문제는 0점으로 처리됩니다.")
    else:
        st.success("모든 문제가 답변되었습니다!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❌ 취소", key="cancel_submit", use_container_width=True):
            print("🔍 [DEBUG] Submit cancelled by user")
            st.session_state.show_submit_confirmation = False
            st.rerun()
    
    with col2:
        if st.button("✅ 제출", key="confirm_submit", type="primary", use_container_width=True):
            print("🔍 [DEBUG] Submit confirmed by user - calling submit_final_test()")
            st.session_state.show_submit_confirmation = False
            submit_final_test()

def auto_submit_test():
    """시간 종료시 자동 제출"""
    st.session_state.auto_submitted = True
    submit_final_test()

def submit_final_test():
    """최종 답변 제출"""
    with st.spinner("테스트 답변을 평가 중..."):
        user_id = st.session_state.user.get("user_id")
        answers = st.session_state.current_answers
        
        # 답변되지 않은 문제들을 기본값(1)으로 채우기
        test = st.session_state.current_test
        for question in test:
            question_id = question.get("_id")
            if question_id not in answers:
                answers[question_id] = 1  # 기본값으로 1번 선택
        
        # API에 제출
        result = submit_test(user_id, answers)
        
        if result and result.get("status") == "success":
            # 결과 저장
            st.session_state.test_results = result
            st.session_state.test_submitted = True
            
            # 사용자 정보 업데이트
            st.session_state.user["test_score"] = result.get("score", 0)
            st.session_state.user["level"] = result.get("level", "하")
            
            # 테스트 관련 세션 상태 정리
            st.session_state.test_start_time = None
            st.session_state.current_question_index = 0
            
            st.success("테스트가 성공적으로 완료되었습니다!")
            st.rerun()
        else:
            st.error("테스트 평가 중 오류가 발생했습니다.")
            if result:
                st.error(f"오류 세부사항: {result.get('detail', '알 수 없는 오류')}")

def show_question_grid(total_questions, current_index, answered_questions):
    """
    Streamlit 기본 컴포넌트로 만든 문제 그리드
    """
    st.subheader("📋 문제 현황")
    
    # 10개씩 행으로 나누어 표시
    rows = (total_questions + 9) // 10  # 올림 계산
    
    for row in range(rows):
        cols = st.columns(10)
        start_idx = row * 10
        end_idx = min(start_idx + 10, total_questions)
        
        for i in range(start_idx, end_idx):
            col_idx = i % 10
            with cols[col_idx]:
                if i == current_index:
                    st.button(f"🔵 {i+1}", key=f"nav_{i}", disabled=True, use_container_width=True)
                elif i in answered_questions:
                    if st.button(f"✅ {i+1}", key=f"nav_{i}", use_container_width=True):
                        st.session_state.current_question_index = i
                        st.rerun()
                else:
                    if st.button(f"⭕ {i+1}", key=f"nav_{i}", use_container_width=True):
                        st.session_state.current_question_index = i
                        st.rerun()
    
    # 범례
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🔵 현재 문제")
    with col2:
        st.success("✅ 답변 완료")
    with col3:
        st.warning("⭕ 미완료")

def show_simple_timer_display(start_time, duration_minutes):
    """
    간단한 타이머 (JavaScript 없이)
    """
    elapsed = datetime.now() - start_time
    remaining = timedelta(minutes=duration_minutes) - elapsed
    
    if remaining.total_seconds() <= 0:
        st.error("⏰ 시간 종료!")
        return True
    
    minutes = int(remaining.total_seconds() // 60)
    seconds = int(remaining.total_seconds() % 60)
    
    if minutes <= 5:
        st.error(f"⏰ 남은 시간: {minutes:02d}:{seconds:02d}")
    elif minutes <= 10:
        st.warning(f"⏰ 남은 시간: {minutes:02d}:{seconds:02d}")
    else:
        st.info(f"⏰ 남은 시간: {minutes:02d}:{seconds:02d}")
    
    return False