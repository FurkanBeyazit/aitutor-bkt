import requests
import streamlit as st
from config.settings import API_BASE_URL

def api_request(endpoint, method="GET", data=None, files=None):
    """API에 요청 보내고 결과 반환"""
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files)
            else:
                response = requests.post(url, json=data)
        else:
            st.error(f"지원되지 않는 HTTP 메서드: {method}")
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 오류: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"API 연결 오류: {str(e)}")
        return None

# 인증 관련 API
def login(email, password):
    """사용자 로그인"""
    data = {"email": email, "password": password}
    return api_request("user/login", method="POST", data=data)

def register(email, password, name, grade, department):
    """새 사용자 등록"""
    data = {
        "email": email,
        "password": password,
        "name": name,
        "grade": grade,
        "department": department
    }
    return api_request("user/register", method="POST", data=data)

def google_login(email, name):
    """Google 계정으로 로그인"""
    data = {"email": email, "name": name}
    return api_request("user/google-login", method="POST", data=data)

def update_profile(email, department, grade):
    """사용자 프로필 업데이트"""
    data = {"email": email, "department": department, "grade": grade}
    return api_request("user/update-profile", method="POST", data=data)

# 시험 관련 API
def get_level_test():
    """레벨 테스트 가져오기"""
    response = api_request("exam/level-test")
    
    if response and response.get("status") == "success":
        test_data = response.get("test", [])
        
        # 데이터 형식 정리
        for question in test_data:
            if "Problem" not in question and "problem" in question:
                question["Problem"] = question["problem"]
            
            if "Choices" not in question and "choices" in question:
                question["Choices"] = question["choices"]
            
            if "Answer Key" not in question and "answer_key" in question:
                question["Answer Key"] = question["answer_key"]
    
    return response

def submit_test(user_id, answers):
    """테스트 답안 제출"""
    data = {"user_id": user_id, "answers": answers}
    return api_request("exam/submit-test", method="POST", data=data)

def get_practice_question(difficulty):
    """지정된 난이도의 연습 문제 가져오기"""
    return api_request(f"exam/practice-question/{difficulty}")

def submit_practice_answer(question_id, student_answer):
    """연습 문제 답안 제출"""
    data = {"question_id": question_id, "student_answer": student_answer}
    return api_request("exam/submit-practice-answer", method="POST", data=data)

def explain_answer(question_id, student_answer):
    """문제 해설 가져오기"""
    data = {"question_id": question_id, "student_answer": student_answer}
    return api_request("llm/explain-answer", method="POST", data=data)

def get_user_test_history(user_id):
    """사용자 테스트 기록 가져오기"""
    return api_request(f"exam/user-test-history/{user_id}")

def get_test_details(user_id, test_index):
    """특정 테스트의 세부사항 가져오기"""
    return api_request(f"exam/test-details/{user_id}/{test_index}")

# 문제 관리 관련 API
def get_collections():
    """기존 컬렉션 목록 가져오기"""
    return api_request("exam/collections")

def get_questions(collection_name, limit=20, skip=0):
    """특정 컬렉션의 문제들 가져오기"""
    return api_request(f"exam/get-questions/{collection_name}?limit={limit}&skip={skip}")

def upload_questions_pdf(file):
    """문제 PDF 업로드"""
    files = {"file": file}
    return api_request("exam/upload-questions-pdf", method="POST", files=files)

def upload_answers_pdf(file):
    """답안 키 PDF 업로드"""
    files = {"file": file}
    return api_request("exam/upload-answers-pdf", method="POST", files=files)

def merge_and_save(questions, answers=None, collection_name="exam_questions", selected_session=None):
    """문제와 답안을 병합하여 저장"""
    data = {
        "questions": questions,
        "answers": answers,
        "collection_name": collection_name,
        "selected_session": selected_session
    }
    return api_request("exam/merge-and-save", method="POST", data=data)

def get_type_based_bkt_report(user_id):
    """TYPE 기반 BKT 마스터리 리포트"""
    return api_request(f"bkt/mastery-report/{user_id}")

def get_weak_types(user_id, threshold=0.6):
    """약한 문제 유형들"""
    return api_request(f"bkt/weak-types/{user_id}?threshold={threshold}")

def get_type_summary(user_id):
    """유형별 요약"""
    return api_request(f"bkt/type-summary/{user_id}")

def get_available_types():
    """사용 가능한 문제 유형들"""
    return api_request("bkt/available-types")

def get_adaptive_test_by_type(user_id, num_questions=10):
    """유형별 적응형 테스트"""
    return api_request(f"exam/adaptive-test-by-type/{user_id}?num_questions={num_questions}")

def update_type_based_bkt(user_id, question_data, student_answer, is_correct):
    """TYPE 기반 BKT 지식 상태 업데이트"""
    data = {
        "user_id": user_id,
        "question_data": question_data,  # type, difficulty 포함
        "student_answer": student_answer,
        "is_correct": is_correct
    }
    return api_request("bkt/update-knowledge", method="POST", data=data)