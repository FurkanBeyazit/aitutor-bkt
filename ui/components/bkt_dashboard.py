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
    """분석 결과 표시 - Güvenilirlik bilgisi ile"""
    # 전체 요약
    st.subheader("📈 전체 학습 현황 (güvenilirlik dahil)")
    
    overall_mastery = bkt_report.get("overall_mastery", 0)
    reliability_summary = bkt_report.get("reliability_summary", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("전체 습득도", f"{overall_mastery * 100:.1f}%")
    
    with col2:
        reliable_count = reliability_summary.get("reliable", 0)
        total_count = reliability_summary.get("total_tested", 0)
        st.metric("신뢰할 수 있는 유형", f"{reliable_count}/{total_count}")
    
    with col3:
        total_attempts = bkt_report.get("total_attempts", 0)
        st.metric("총 시도 횟수", total_attempts)
    
    with col4:
        reliability_pct = reliability_summary.get("reliability_percentage", 0)
        st.metric("신뢰도", f"{reliability_pct:.0f}%")
    
    # ⭐ 신뢰성 경고
    unreliable_count = reliability_summary.get("needs_more_practice", 0)
    if unreliable_count > 0:
        st.warning(f"""
        ⚠️ **신뢰성 알림**: {unreliable_count}개 유형에서 더 많은 연습이 필요합니다.
        
        💡 **권장사항**: 각 유형별로 최소 5-8문제를 풀어야 정확한 실력 측정이 가능합니다.
        """)
    
    # ⭐ SADECE test edilmiş types için analysis
    type_analysis = bkt_report.get("type_analysis", {})
    tested_types = {k: v for k, v in type_analysis.items() if v.get("attempts", 0) > 0}
    
    if tested_types:
        st.subheader("🎯 실제 테스트된 문제 유형별 분석")
        
        # 데이터 준비 - 신뢰성 정보 포함
        type_data = []
        for question_type, data in tested_types.items():
            type_data.append({
                "문제 유형": question_type,
                "습득도": data.get("mastery_probability", 0),
                "레벨": data.get("level", "알 수 없음"),
                "시도 수": data.get("attempts", 0),
                "정확도": data.get("accuracy", 0),
                "상태": data.get("emoji", "📚"),
                "신뢰도": data.get("confidence_level", "low"),
                "표시": data.get("display_text", ""),
                "신뢰성": "✅" if data.get("is_reliable", False) else "⚠️"
            })
        
        if type_data:
            type_df = pd.DataFrame(type_data)
            
            # 차트 선택
            chart_type = st.selectbox(
                "차트 유형 선택:",
                ["📋 상세 테이블 (신뢰성 포함)", "📊 막대 차트", "🥧 레벨 분포", "📈 레이더 차트"]
            )
            
            if chart_type == "📋 상세 테이블 (신뢰성 포함)":
                show_reliability_table(type_df)
            elif chart_type == "📊 막대 차트":
                show_bar_chart(type_df)
            elif chart_type == "🥧 레벨 분포":
                show_pie_chart(type_df)
            else:
                show_radar_chart(type_df)
        else:
            st.info("아직 테스트된 문제 유형이 없습니다.")
    else:
        st.info("아직 어떤 문제 유형도 테스트하지 않았습니다. 테스트를 시작해보세요!")
    
    # 권장사항 - 신뢰성 고려
    if tested_types:
        st.subheader("💡 신뢰성 기반 학습 권장사항")
        show_reliability_recommendations(bkt_report)
def show_reliability_table(type_df):
    """신뢰성 정보가 포함된 테이블"""
    # 스타일링된 테이블 표시
    st.markdown("### 📊 상세 분석표 (신뢰성 정보 포함)")
    
    # 신뢰성에 따라 정렬
    reliability_order = {"high": 4, "medium": 3, "low": 2, "very_low": 1}
    type_df["신뢰도_순서"] = type_df["신뢰도"].map(reliability_order)
    type_df_sorted = type_df.sort_values(["신뢰도_순서", "습득도"], ascending=[False, False])
    
    # 표시할 컬럼 선택
    display_df = type_df_sorted[["문제 유형", "표시", "신뢰성", "정확도"]].copy()
    display_df["정확도"] = display_df["정확도"].apply(lambda x: f"{x*100:.1f}%")
    
    st.dataframe(display_df, use_container_width=True)
    
    # 범례
    st.markdown("""
    **범례:**
    - ✅ **신뢰성 높음**: 5+ 문제 풀이 완료
    - ⚠️ **신뢰성 낮음**: 더 많은 연습 필요
    - 🏆 **Mastery**: 80%+ 달성 (충분한 문제 수)
    - 📚 **학습중**: 지속적인 향상 필요
    """)
def show_reliability_recommendations(bkt_report):
    """신뢰성을 고려한 권장사항"""
    type_analysis = bkt_report.get("type_analysis", {})
    tested_types = {k: v for k, v in type_analysis.items() if v.get("attempts", 0) > 0}
    
    if not tested_types:
        st.info("아직 테스트된 문제 유형이 없습니다.")
        return
    
    # 신뢰성에 따라 분류
    reliable_weak = []
    reliable_strong = []
    unreliable_types = []
    
    for question_type, data in tested_types.items():
        mastery = data.get("mastery_probability", 0)
        is_reliable = data.get("is_reliable", False)
        
        if is_reliable:
            if mastery < 0.5:
                reliable_weak.append((question_type, mastery, data))
            elif mastery >= 0.8:
                reliable_strong.append((question_type, mastery, data))
        else:
            unreliable_types.append((question_type, data.get("attempts", 0), data))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 확실한 약점 유형 (신뢰성 높음)")
        if reliable_weak:
            reliable_weak.sort(key=lambda x: x[1])  # mastery로 정렬
            for question_type, mastery, data in reliable_weak[:3]:
                st.error(f"**{question_type}**: {mastery*100:.0f}% ({data['attempts']}문제)")
                st.caption("💡 이 유형에 집중적으로 학습하세요!")
        else:
            st.success("🎉 신뢰할 수 있는 약점 유형이 없습니다!")
    
    with col2:
        st.markdown("#### 🏆 확실한 강점 유형 (신뢰성 높음)")
        if reliable_strong:
            reliable_strong.sort(key=lambda x: x[1], reverse=True)  # mastery로 정렬
            for question_type, mastery, data in reliable_strong[:3]:
                st.success(f"**{question_type}**: {mastery*100:.0f}% ({data['attempts']}문제)")
                st.caption("💡 이 유형은 완전히 마스터했습니다!")
        else:
            st.info("아직 완전히 마스터한 유형이 없습니다.")
    
    # 더 많은 연습이 필요한 유형들
    if unreliable_types:
        st.markdown("#### ⚠️ 더 많은 연습이 필요한 유형들")
        unreliable_types.sort(key=lambda x: x[1])  # attempts로 정렬
        
        for question_type, attempts, data in unreliable_types:
            mastery = data.get("mastery_probability", 0)
            needed = 5 - attempts
            st.warning(f"**{question_type}**: {mastery*100:.0f}% ({attempts}문제) - {needed}문제 더 필요")
        
        st.info("💡 각 유형별로 최소 5문제를 풀어야 정확한 실력 측정이 가능합니다.")
    
    # 적응형 테스트 안내
    st.markdown("---")
    st.markdown("#### 🚀 맞춤형 학습 전략")
    
    if reliable_weak:
        weak_type_names = [t[0] for t in reliable_weak[:3]]
        st.info(f"""
        ### 🎯 확실한 약점 집중 공략!
        **신뢰할 수 있는 약점**: {', '.join(weak_type_names)}
        
        이 유형들은 충분한 문제를 풀어서 **확실히 약하다고 판단**된 영역입니다.
        **'맞춤형 테스트'** 탭에서 집중 훈련을 받아보세요!
        """)
    elif unreliable_types:
        st.info(f"""
        ### 📊 더 많은 데이터 수집 필요
        아직 대부분의 유형에서 충분한 문제를 풀지 않았습니다.
        
        **'맞춤형 테스트'**로 다양한 유형의 문제를 풀어보세요!
        그러면 정확한 강점/약점 분석이 가능합니다.
        """)
    else:
        st.success(f"""
        ### 🏆 훌륭한 성과!
        모든 테스트된 유형에서 우수한 결과를 보이고 있습니다.
        
        **'맞춤형 테스트'**로 더 도전적인 문제에 도전해보세요!
        """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.success("👆 **'맞춤형 테스트'** 탭으로 이동하여 시작하세요!")    
def show_bar_chart(type_df):
    """막대 차트 표시 - 신뢰성 색상 포함"""
    # 신뢰성에 따른 색상 매핑
    color_map = {
        "high": "#00CC96",      # 진한 초록
        "medium": "#FFA15A",    # 주황 
        "low": "#FF6692",       # 빨강
        "very_low": "#CCCCCC"   # 회색
    }
    
    # 색상 리스트 생성
    colors = [color_map.get(conf, "#CCCCCC") for conf in type_df["신뢰도"]]
    
    fig = px.bar(
        type_df,
        x="문제 유형",
        y="습득도",
        title="문제 유형별 습득도 (신뢰성 반영)",
        color="신뢰도",
        color_discrete_map=color_map,
        hover_data=["시도 수", "신뢰성"]
    )
    
    fig.update_layout(
        xaxis_tickangle=-45, 
        height=500,
        showlegend=True
    )
    
    # 범례 추가
    fig.add_annotation(
        text="범례: 초록=신뢰함, 주황=보통, 빨강=신뢰도낮음",
        xref="paper", yref="paper",
        x=0.5, y=-0.2,
        showarrow=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_pie_chart(type_df):
    """파이 차트 표시 - 신뢰성 필터링"""
    # 신뢰할 수 있는 데이터만 사용
    reliable_df = type_df[type_df["신뢰성"] == "✅"]
    
    if len(reliable_df) == 0:
        st.warning("신뢰할 수 있는 데이터가 부족합니다. 더 많은 문제를 풀어주세요.")
        return
    
    level_counts = reliable_df["레벨"].value_counts()
    
    fig = px.pie(
        values=level_counts.values,
        names=level_counts.index,
        title="신뢰할 수 있는 데이터 기준 레벨 분포",
        color_discrete_map={
            "마스터": "#00CC96",
            "숙련": "#FFA15A",
            "학습중": "#19D3F3", 
            "초급": "#FF6692"
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"📊 신뢰할 수 있는 {len(reliable_df)}개 유형의 데이터를 기준으로 합니다.")

def show_radar_chart(type_df):
    """레이더 차트 표시 - 신뢰성 필터링"""
    # 신뢰할 수 있는 데이터만 사용
    reliable_df = type_df[type_df["신뢰성"] == "✅"]
    
    if len(reliable_df) < 3:
        st.warning("레이더 차트를 위해서는 최소 3개의 신뢰할 수 있는 유형이 필요합니다.")
        st.info("더 많은 문제를 풀어서 신뢰성을 높여주세요.")
        return
    
    # 상위 8개 유형만 표시
    top_types = reliable_df.nlargest(8, "습득도")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=top_types["습득도"].tolist() + [top_types["습득도"].iloc[0]],
        theta=top_types["문제 유형"].tolist() + [top_types["문제 유형"].iloc[0]],
        fill='toself',
        name='신뢰할 수 있는 습득도',
        line_color='blue'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        title="신뢰할 수 있는 데이터 기준 레이더 차트"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.success(f"📊 신뢰할 수 있는 {len(reliable_df)}개 유형의 데이터를 기준으로 합니다.")    # 적응형 테스트 안내
    st.markdown("---")
    st.markdown("#### 🚀 유형별 맞춤형 학습 추천")
    
    st.info("""
    ### 🎯 맞춤형 테스트 안내
    위의 분석 결과를 바탕으로 **'맞춤형 테스트'** 탭에서 
    당신의 약점에 집중한 특별한 테스트를 받아보세요!
    
    **맞춤형 테스트 특징:**
    - 🎯 약한 유형에 집중된 문제 선별
    - 🧠 BKT 알고리즘 기반 난이도 조정
    - ⏰ 15분 집중 테스트
    - 📊 실시간 학습 성과 분석
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.success("👆 **'맞춤형 테스트'** 탭으로 이동하여 시작하세요!")

# request_adaptive_test 함수 제거 (더 이상 필요 없음)