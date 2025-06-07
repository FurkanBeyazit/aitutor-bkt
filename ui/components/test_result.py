import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.settings import LEVEL_DESCRIPTIONS, DIFFICULTY_NAMES

def show_test_results_with_multiple_charts():
    """테스트 결과를 다양한 차트로 표시"""
    results = st.session_state.test_results
    
    if not results:
        st.warning("테스트 결과를 찾을 수 없습니다.")
        return
    
    st.header("🎉 테스트 결과")
    
    # 결과 요약
    score = results.get("score", 0)
    level = results.get("level", "하")
    correct_count = results.get("correct_count", 0)
    total_questions = results.get("total_questions", 0)
    accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # 결과 카드
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총점", f"{score}")
    with col2:
        st.metric("레벨", f"{level}")
    with col3:
        st.metric("정확도", f"%{accuracy:.1f}")
    
    # 레벨 설명
    if level in LEVEL_DESCRIPTIONS:
        st.info(LEVEL_DESCRIPTIONS[level])
    
    # 난이도별 분석
    question_results = results.get("results", [])
    
    if question_results:
        # 테스트 데이터와 문제 및 난이도 매칭
        test_data = st.session_state.current_test or []
        
        # 난이도별 통계
        difficulty_stats = {"하": {"total": 0, "correct": 0}, "중": {"total": 0, "correct": 0}, "상": {"total": 0, "correct": 0}}
        
        for result in question_results:
            q_id = result.get("question_id", "")
            is_correct = result.get("correct", False)
            
            # 이 문제의 난이도 찾기
            question_info = next((q for q in test_data if str(q.get("_id")) == q_id), None)
            
            if question_info:
                difficulty = question_info.get("difficulty", "하")
                difficulty_stats[difficulty]["total"] += 1
                if is_correct:
                    difficulty_stats[difficulty]["correct"] += 1
        
        # 차트 옵션
        st.subheader("📊 성능 분석")
        
        # 사용자에게 차트 유형 선택하게 하기
        chart_type = st.selectbox(
            "차트 유형 선택:",
            [
                "🥧 난이도별 개별 파이 차트",
                "📊 성공률 막대 차트", 
                "🎯 도넛 차트로 전체 성공률",
                "📈 레이더 차트로 성능",
                "🔄 모든 차트 표시"
            ]
        )
        
        if chart_type == "🥧 난이도별 개별 파이 차트" or chart_type == "🔄 모든 차트 표시":
            show_individual_pie_charts(difficulty_stats)
        
        if chart_type == "📊 성공률 막대 차트" or chart_type == "🔄 모든 차트 표시":
            show_success_rate_bar_chart(difficulty_stats)
        
        if chart_type == "🎯 도넛 차트로 전체 성공률" or chart_type == "🔄 모든 차트 표시":
            show_overall_donut_chart(difficulty_stats, correct_count, total_questions)
        
        if chart_type == "📈 레이더 차트로 성능" or chart_type == "🔄 모든 차트 표시":
            show_radar_chart(difficulty_stats)
        
        # 통계 테이블
        show_stats_table(difficulty_stats)

def show_individual_pie_charts(difficulty_stats):
    """각 난이도별 개별 파이 차트"""
    st.subheader("🥧 난이도별 상세 성공률")
    
    col1, col2, col3 = st.columns(3)
    
    colors = {"하": ["#90EE90", "#FFB6C1"], "중": ["#87CEEB", "#DDA0DD"], "상": ["#FFD700", "#FF6347"]}
    
    for i, (level_key, col) in enumerate(zip(["하", "중", "상"], [col1, col2, col3])):
        stat = difficulty_stats[level_key]
        
        if stat["total"] > 0:
            # 파이 차트 데이터 준비
            correct = stat["correct"]
            wrong = stat["total"] - correct
            
            fig = px.pie(
                values=[correct, wrong],
                names=["정답", "오답"],
                title=f"{DIFFICULTY_NAMES[level_key]} 레벨 ({stat['total']} 문제)",
                color_discrete_sequence=colors[level_key]
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=300)
            
            with col:
                st.plotly_chart(fig, use_container_width=True)
        else:
            with col:
                st.info(f"{DIFFICULTY_NAMES[level_key]} 레벨에 문제가 없습니다")

def show_success_rate_bar_chart(difficulty_stats):
    """성공률 막대 차트"""
    st.subheader("📊 성공률 비교")
    
    # 데이터 준비
    levels = []
    success_rates = []
    total_questions = []
    
    for level_key in ["하", "중", "상"]:
        stat = difficulty_stats[level_key]
        if stat["total"] > 0:
            success_rate = (stat["correct"] / stat["total"]) * 100
            levels.append(DIFFICULTY_NAMES[level_key])
            success_rates.append(success_rate)
            total_questions.append(stat["total"])
    
    if levels:
        # 막대 차트 생성
        fig = px.bar(
            x=levels,
            y=success_rates,
            title="난이도별 성공률",
            labels={"x": "난이도", "y": "성공률 (%)"},
            color=success_rates,
            color_continuous_scale="RdYlGn",  # 빨강-노랑-초록
            text=success_rates
        )
        
        # 막대 위에 값 추가
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)

def show_overall_donut_chart(difficulty_stats, correct_count, total_questions):
    """전체 성공률 도넛 차트"""
    st.subheader("🎯 전체 테스트 성공률")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 메인 도넛 차트 - 전체 성공률
        wrong_count = total_questions - correct_count
        
        fig = px.pie(
            values=[correct_count, wrong_count],
            names=["정답", "오답"],
            title="전체 테스트 성공률",
            hole=0.4,  # 도넛 효과
            color_discrete_sequence=["#00CC96", "#FF6B6B"]
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 난이도 분포 도넛 차트
        difficulty_totals = []
        difficulty_labels = []
        
        for level_key in ["하", "중", "상"]:
            stat = difficulty_stats[level_key]
            if stat["total"] > 0:
                difficulty_totals.append(stat["total"])
                difficulty_labels.append(DIFFICULTY_NAMES[level_key])
        
        if difficulty_totals:
            fig2 = px.pie(
                values=difficulty_totals,
                names=difficulty_labels,
                title="문제 난이도 분포",
                hole=0.4,
                color_discrete_sequence=["#FFE5B4", "#FFCC99", "#FF9966"]
            )
            
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(height=400)
            
            st.plotly_chart(fig2, use_container_width=True)

def show_radar_chart(difficulty_stats):
    """레이더 차트로 성능 표시"""
    st.subheader("📈 성능 레이더 분석")
    
    # 레이더 차트 데이터
    categories = []
    success_rates = []
    
    level_names = {"하": "쉬운 문제", "중": "보통 문제", "상": "어려운 문제"}
    
    for level_key in ["하", "중", "상"]:
        stat = difficulty_stats[level_key]
        if stat["total"] > 0:
            success_rate = (stat["correct"] / stat["total"]) * 100
            categories.append(level_names[level_key])
            success_rates.append(success_rate)
    
    if len(categories) >= 3:  # 레이더 차트를 위해 최소 3개 카테고리 필요
        # 닫힌 모양을 위해 첫 번째 값을 마지막에 추가
        categories_closed = categories + [categories[0]]
        success_rates_closed = success_rates + [success_rates[0]]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=success_rates_closed,
            theta=categories_closed,
            fill='toself',
            name='성공률',
            line_color='blue',
            fillcolor='rgba(0, 100, 255, 0.2)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            title="난이도별 성능 레이더",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("레이더 차트를 위해서는 최소 3가지 다른 난이도의 문제가 필요합니다.")

def show_stats_table(difficulty_stats):
    """상세 통계 테이블"""
    st.subheader("📋 상세 통계")
    
    stats_data = []
    
    for level_key in ["하", "중", "상"]:
        stat = difficulty_stats[level_key]
        if stat["total"] > 0:
            success_rate = (stat["correct"] / stat["total"] * 100)
            wrong_count = stat["total"] - stat["correct"]
            
            stats_data.append({
                "🎯 난이도": DIFFICULTY_NAMES[level_key],
                "📝 총 문제": stat["total"],
                "✅ 정답": stat["correct"],
                "❌ 오답": wrong_count,
                "📊 성공률": f"%{success_rate:.1f}",
                "⭐ 상태": "🥇 우수" if success_rate >= 80 else "🥈 양호" if success_rate >= 60 else "🥉 개선 필요"
            })
    
    if stats_data:
        st.dataframe(pd.DataFrame(stats_data), use_container_width=True)