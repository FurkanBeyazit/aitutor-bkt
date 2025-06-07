# ui/components/bkt_dashboard.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from api.client import api_request

def show_bkt_dashboard_tab():
    """TYPE 기반 BKT 대시보드 메인 함수"""
    st.header("🧠 문제 유형별 학습 분석 (BKT)")
    
    user_id = st.session_state.user.get("user_id")
    
    if not user_id:
        st.error("사용자 정보를 찾을 수 없습니다.")
        return
    
    # 버튼들
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 학습 분석 업데이트", use_container_width=True):
            with st.spinner("학습 상태 분석 중..."):
                load_bkt_data(user_id)
    
    with col2:
        if st.button("🔍 문제 유형 확인", use_container_width=True):
            show_available_types()
    
    # BKT 데이터 표시
    if "bkt_report" in st.session_state and st.session_state.bkt_report:
        show_analysis_results(st.session_state.bkt_report)
    else:
        st.info("🔍 '학습 분석 업데이트' 버튼을 클릭하여 상세 분석을 확인하세요.")

def load_bkt_data(user_id):
    """BKT 데이터 로드"""
    try:
        mastery_result = api_request(f"bkt/mastery-report/{user_id}")
        
        if mastery_result and mastery_result.get("status") == "success":
            st.session_state.bkt_report = mastery_result.get("report")
            st.success("✅ 문제 유형별 학습 분석 완료!")
        else:
            st.error("❌ 학습 분석 데이터를 가져올 수 없습니다.")
            
    except Exception as e:
        st.error(f"❌ 분석 중 오류 발생: {str(e)}")

def show_available_types():
    """사용 가능한 문제 유형들 표시"""
    try:
        result = api_request("bkt/available-types")
        
        if result and result.get("status") == "success":
            types = result.get("types", [])
            
            st.subheader("📋 시스템에서 추적하는 문제 유형들")
            
            cols = st.columns(3)
            for i, question_type in enumerate(types):
                col_idx = i % 3
                with cols[col_idx]:
                    st.info(f"🔹 {question_type}")
            
            st.success(f"✅ 총 {len(types)}개의 문제 유형을 추적하고 있습니다.")
            
    except Exception as e:
        st.error(f"❌ 오류: {str(e)}")

def show_analysis_results(bkt_report):
    """분석 결과 표시"""
    # 전체 요약
    st.subheader("📈 전체 학습 현황")
    
    overall_mastery = bkt_report.get("overall_mastery", 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("전체 습득도", f"{overall_mastery * 100:.1f}%")
    
    with col2:
        type_count = len(bkt_report.get("type_analysis", {}))
        st.metric("추적 유형 수", type_count)
    
    with col3:
        total_attempts = bkt_report.get("total_attempts", 0)
        st.metric("총 시도 횟수", total_attempts)
    
    with col4:
        mastered_types = sum(1 for type_data in bkt_report.get("type_analysis", {}).values() 
                           if type_data.get("mastery_probability", 0) >= 0.8)
        st.metric("마스터 유형", f"{mastered_types}개")
    
    # 유형별 분석
    type_analysis = bkt_report.get("type_analysis", {})
    
    if type_analysis:
        st.subheader("🎯 문제 유형별 상세 분석")
        
        # 데이터 준비
        type_data = []
        for question_type, data in type_analysis.items():
            type_data.append({
                "문제 유형": question_type,
                "습득도": data.get("mastery_probability", 0),
                "레벨": data.get("level", "알 수 없음"),
                "시도 수": data.get("attempts", 0),
                "정확도": data.get("accuracy", 0),
                "상태": data.get("emoji", "📚")
            })
        
        type_df = pd.DataFrame(type_data)
        
        # 차트 선택
        chart_type = st.selectbox(
            "차트 유형 선택:",
            ["📊 막대 차트", "📋 상세 테이블"]
        )
        
        if chart_type == "📊 막대 차트":
            show_bar_chart(type_df)
        else:
            show_table(type_df)
    
    # 권장사항
    st.subheader("💡 학습 권장사항")
    show_recommendations(bkt_report)

def show_bar_chart(type_df):
    """막대 차트 표시"""
    fig = px.bar(
        type_df,
        x="문제 유형",
        y="습득도",
        color="레벨",
        title="문제 유형별 습득도"
    )
    fig.update_layout(xaxis_tickangle=-45, height=500)
    st.plotly_chart(fig, use_container_width=True)

def show_table(type_df):
    """테이블 표시"""
    styled_df = type_df.copy()
    styled_df["습득도"] = styled_df["습득도"].apply(lambda x: f"{x*100:.1f}%")
    styled_df["정확도"] = styled_df["정확도"].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(styled_df, use_container_width=True)

def show_recommendations(bkt_report):
    """권장사항 표시"""
    type_analysis = bkt_report.get("type_analysis", {})
    
    weak_types = []
    strong_types = []
    
    for question_type, data in type_analysis.items():
        mastery = data.get("mastery_probability", 0)
        if mastery < 0.5 and data.get("attempts", 0) > 0:
            weak_types.append((question_type, mastery, data.get("level", "초급")))
        elif mastery >= 0.8 and data.get("attempts", 0) > 0:
            strong_types.append((question_type, mastery, data.get("level", "마스터")))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 집중 개선 유형")
        if weak_types:
            weak_types.sort(key=lambda x: x[1])
            for question_type, mastery, level in weak_types[:3]:
                st.warning(f"**{question_type}** - {level} ({mastery*100:.1f}%)")
        else:
            st.success("🎉 모든 유형에서 우수한 성과!")
    
    with col2:
        st.markdown("#### 🏆 우수 유형")
        if strong_types:
            strong_types.sort(key=lambda x: x[1], reverse=True)
            for question_type, mastery, level in strong_types[:3]:
                st.success(f"**{question_type}** - {level} ({mastery*100:.1f}%)")
        else:
            st.info("더 많은 학습으로 우수 유형을 만들어보세요!")
    
    # 적응형 테스트 버튼
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 약점 집중 테스트", use_container_width=True):
            request_adaptive_test()
    
    with col2:
        if st.button("🔍 전체 유형 확인", use_container_width=True):
            show_available_types()

def request_adaptive_test():
    """적응형 테스트 요청"""
    user_id = st.session_state.user.get("user_id")
    
    with st.spinner("맞춤형 테스트 준비 중..."):
        result = api_request(f"exam/adaptive-test-by-type/{user_id}?num_questions=10")
        
        if result and result.get("status") == "success":
            st.session_state.adaptive_test = result.get("adaptive_test", [])
            st.session_state.adaptive_test_info = result.get("test_info", {})
            st.session_state.test_type = "adaptive"
            
            st.success("✅ 맞춤형 테스트가 준비되었습니다!")
            st.info("'레벨 테스트' 탭으로 이동하여 테스트를 시작하세요.")
        else:
            st.error("❌ 테스트 준비에 실패했습니다.")