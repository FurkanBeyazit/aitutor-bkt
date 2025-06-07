# ui/components/timer_component.py
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta

def show_exam_timer(start_time, duration_minutes):
    """
    JavaScript tabanlı sınav zamanlayıcısı
    Daha smooth ve performanslı timer için
    """
    
    # Toplam saniye hesapla
    total_seconds = duration_minutes * 60
    
    # Başlangıç zamanından geçen süreyi hesapla
    elapsed = datetime.now() - start_time
    elapsed_seconds = int(elapsed.total_seconds())
    remaining_seconds = max(0, total_seconds - elapsed_seconds)
    
    # JavaScript timer component
    timer_html = f"""
    <div id="exam-timer" style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-family: 'Arial', sans-serif;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    ">
        <div style="font-size: 14px; margin-bottom: 5px; opacity: 0.9;">
            ⏰ 남은 시간
        </div>
        <div id="timer-display" style="
            font-size: 32px;
            font-weight: bold;
            letter-spacing: 2px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        ">
            --:--
        </div>
        <div id="timer-warning" style="
            font-size: 12px;
            margin-top: 5px;
            opacity: 0.8;
        "></div>
    </div>

    <script>
        let remainingSeconds = {remaining_seconds};
        let timerInterval;
        
        function updateTimer() {{
            if (remainingSeconds <= 0) {{
                clearInterval(timerInterval);
                document.getElementById('timer-display').innerText = '00:00';
                document.getElementById('timer-warning').innerText = '⚠️ 시간 종료!';
                document.getElementById('exam-timer').style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)';
                return;
            }}
            
            const minutes = Math.floor(remainingSeconds / 60);
            const seconds = remainingSeconds % 60;
            const timeString = `${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
            
            document.getElementById('timer-display').innerText = timeString;
            
            // Warning messages based on remaining time
            if (remainingSeconds <= 300) {{ // 5 minutes
                document.getElementById('timer-warning').innerText = '🚨 5분 이하 남음!';
                document.getElementById('exam-timer').style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)';
            }} else if (remainingSeconds <= 600) {{ // 10 minutes  
                document.getElementById('timer-warning').innerText = '⚠️ 10분 이하 남음';
                document.getElementById('exam-timer').style.background = 'linear-gradient(135deg, #ffa502 0%, #ff6348 100%)';
            }} else {{
                document.getElementById('timer-warning').innerText = '';
            }}
            
            remainingSeconds--;
        }}
        
        // Initial call
        updateTimer();
        
        // Start interval
        timerInterval = setInterval(updateTimer, 1000);
        
        // Cleanup when component is destroyed
        window.addEventListener('beforeunload', function() {{
            clearInterval(timerInterval);
        }});
    </script>
    """
    
    # Streamlit component로 렌더링
    components.html(timer_html, height=120)
    
    # 시간 종료 체크 (백업용)
    if remaining_seconds <= 0:
        return True  # 시간 종료됨
    
    return False  # 아직 시간 남음

def show_progress_bar(current_question, total_questions, answered_count):
    """
    향상된 진행률 표시기
    """
    progress_percentage = (answered_count / total_questions) * 100
    current_percentage = (current_question / total_questions) * 100
    
    progress_html = f"""
    <div style="
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #dee2e6;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 14px;
            color: #495057;
        ">
            <span>📝 문제 {current_question}/{total_questions}</span>
            <span>✅ 답변 완료: {answered_count}/{total_questions}</span>
            <span>📊 진행률: {progress_percentage:.0f}%</span>
        </div>
        
        <div style="
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        ">
            <!-- 전체 진행률 바 (답변 완료된 문제들) -->
            <div style="
                width: {progress_percentage}%;
                height: 100%;
                background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
                transition: width 0.3s ease;
                position: absolute;
                top: 0;
                left: 0;
            "></div>
            
            <!-- 현재 문제 위치 표시 -->
            <div style="
                position: absolute;
                left: {current_percentage}%;
                top: 0;
                width: 3px;
                height: 100%;
                background: #dc3545;
                box-shadow: 0 0 5px rgba(220, 53, 69, 0.5);
            "></div>
        </div>
        
        <div style="
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 12px;
            color: #6c757d;
        ">
            <span>시작</span>
            <span>현재 위치</span>
            <span>완료</span>
        </div>
    </div>
    """
    
    components.html(progress_html, height=100)

def show_question_navigator(total_questions, current_index, answered_questions):
    """
    Interactive question navigator
    """
    # 문제 상태 배열 생성
    question_states = []
    for i in range(total_questions):
        if i == current_index:
            question_states.append('current')
        elif i in answered_questions:
            question_states.append('answered')
        else:
            question_states.append('unanswered')
    
    # JavaScript로 상호작용 가능한 네비게이터 생성
    navigator_html = f"""
    <div style="
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #dee2e6;
    ">
        <h4 style="margin: 0 0 15px 0; color: #495057; font-size: 16px;">
            📋 문제 네비게이터
        </h4>
        
        <div style="
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 8px;
            margin-bottom: 15px;
        " id="question-grid">
        </div>
        
        <div style="
            display: flex;
            justify-content: space-around;
            font-size: 12px;
            color: #6c757d;
        ">
            <span>🔵 현재 문제</span>
            <span>✅ 완료</span>
            <span>⭕ 미완료</span>
        </div>
    </div>

    <script>
        const totalQuestions = {total_questions};
        const currentIndex = {current_index};
        const answeredQuestions = {list(answered_questions)};
        const questionStates = {question_states};
        
        function createQuestionGrid() {{
            const grid = document.getElementById('question-grid');
            if (!grid) return;
            
            grid.innerHTML = '';
            
            for (let i = 0; i < totalQuestions; i++) {{
                const button = document.createElement('div');
                button.textContent = i + 1;
                button.style.cssText = `
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                    font-size: 12px;
                    text-align: center;
                    min-height: 35px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                `;
                
                // 상태에 따른 스타일 적용
                if (questionStates[i] === 'current') {{
                    button.style.background = 'linear-gradient(135deg, #007bff, #0056b3)';
                    button.style.color = 'white';
                    button.style.boxShadow = '0 2px 8px rgba(0,123,255,0.3)';
                    button.textContent = '🔵 ' + (i + 1);
                }} else if (questionStates[i] === 'answered') {{
                    button.style.background = 'linear-gradient(135deg, #28a745, #1e7e34)';
                    button.style.color = 'white';
                    button.textContent = '✅ ' + (i + 1);
                }} else {{
                    button.style.background = '#e9ecef';
                    button.style.color = '#495057';
                    button.style.border = '2px solid #dee2e6';
                    button.textContent = '⭕ ' + (i + 1);
                }}
                
                grid.appendChild(button);
            }}
        }}
        
        // 초기 그리드 생성
        createQuestionGrid();
    </script>
    """
    
    components.html(navigator_html, height=200)

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
                        #st.rerun()
                else:
                    if st.button(f"⭕ {i+1}", key=f"nav_{i}", use_container_width=True):
                        st.session_state.current_question_index = i
                        #st.rerun()
    
    # 범례
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🔵 현재 문제")
    with col2:
        st.success("✅ 답변 완료")
    with col3:
        st.warning("⭕ 미완료")