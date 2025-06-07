import streamlit as st

def show_questions_json_preview(api_result):
    """FastAPI에서 반환된 문제 JSON 표시"""
    st.markdown("### 📋 문제 미리보기 (FastAPI JSON)")
    
    if api_result and api_result.get("status") == "success":
        questions = api_result.get("questions", [])
        
        # 요약 정보
        st.info(f"📊 총 {len(questions)}개 문제가 파싱되었습니다")
        
        # 전체 JSON을 예쁘게 표시
        with st.expander("🔍 FastAPI JSON 응답 (전체 데이터)", expanded=False):
            st.json(api_result)
        
        # 처음 3개 문제를 개별적으로 표시
        st.write("**📖 처음 3개 문제 (JSON 형식):**")
        for i, question in enumerate(questions[:3]):
            with st.expander(f"문제 {i+1} JSON", expanded=False):
                st.json(question)
    else:
        st.error("❌ API 응답에 오류가 있습니다")
        st.json(api_result)

def show_answers_json_preview(api_result):
    """FastAPI에서 반환된 답안 JSON 표시"""
    st.markdown("### 🔑 답안 미리보기 (FastAPI JSON)")
    
    if api_result and api_result.get("status") == "success":
        answers = api_result.get("answers", [])
        
        # 요약 정보
        st.info(f"📊 총 {len(answers)}개 답안이 파싱되었습니다")
        
        # 세션 분석
        sessions = list(set([ans.get('session', '') for ans in answers if ans.get('session', '').strip()]))
        if sessions:
            st.success(f"📚 발견된 세션: {', '.join(sorted(sessions))}")
        
        # 전체 JSON을 예쁘게 표시
        with st.expander("🔍 FastAPI JSON 응답 (전체 데이터)", expanded=False):
            st.json(api_result)
        
        # 처음 10개 답안을 개별적으로 표시
        st.write("**📋 처음 10개 답안 (JSON 형식):**")
        for i, answer in enumerate(answers[:10]):
            with st.expander(f"답안 {i+1} JSON", expanded=False):
                st.json(answer)
    else:
        st.error("❌ API 응답에 오류가 있습니다")
        st.json(api_result)