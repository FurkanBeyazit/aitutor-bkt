import streamlit as st

# API 설정
API_BASE_URL = "http://localhost:8000/api"

def configure_page():
    """페이지 기본 설정"""
    st.set_page_config(
        page_title="시험 플랫폼",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 스타일 설정
    st.markdown("""
    <style>
        .main {
            padding: 1rem;
        }
        .stButton>button {
            width: 100%;
        }
        .css-1d391kg {
            padding: 1rem 1rem 1rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px 4px 0px 0px;
            padding: 10px 16px;
            font-size: 16px;
        }
        h1, h2, h3 {
            margin-bottom: 1rem;
        }
        hr {
            margin: 1.5rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

# 레벨 설명
LEVEL_DESCRIPTIONS = {
    "상": "🌟 고급 레벨 - 주제를 깊이 이해하고 있습니다.",
    "중": "📚 중급 레벨 - 기본 개념은 탄탄하나, 개선할 영역이 있습니다.",
    "하": "📖 초급 레벨 - 기본 개념을 강화해야 합니다."
}

DIFFICULTY_NAMES = {"하": "쉬움", "중": "보통", "상": "어려움"}
DIFFICULTY_COLORS = {"하": "success", "중": "warning", "상": "error"}