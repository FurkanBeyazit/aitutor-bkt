from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
#USERS
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    grade: int
    department: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleLogin(BaseModel):
    email: EmailStr
    name: str

class UpdateProfile(BaseModel):
    email: EmailStr
    department: str
    grade: int

class UpdateScore(BaseModel):
    email: EmailStr
    test_score: int

class UserResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    department: Optional[str] = None
    grade: Optional[int] = None
    test_score: Optional[int] = 0
    level: Optional[str] = None
    role: Optional[str] = "student"

# TESTS
class Question(BaseModel):
    problem_id: str
    problem: str
    choices: List[str]

class Answer(BaseModel):
    problem_id: str
    answer_key: int

class MergeData(BaseModel):
    questions: List[Question]
    answers: Optional[List[Answer]] = None
    collection_name: str = "exam_questions"

class TestSubmission(BaseModel):
    user_id: str
    answers: Dict[str, int]  # {question_id: selected_answer}

# API responses
class ApiResponse(BaseModel):
    status: str
    message: Optional[str] = None

class UserApiResponse(ApiResponse):
    user: UserResponse

class QuestionsResponse(ApiResponse):
    questions: Optional[List[Dict[str, Any]]] = None
    total: Optional[int] = None
    limit: Optional[int] = None
    skip: Optional[int] = None

class CollectionsResponse(ApiResponse):
    collections: List[str]

class TestResponse(ApiResponse):
    test: List[Dict[str, Any]]

class TestSubmitResponse(ApiResponse):
    score: int
    level: str
    correct_count: int
    total_questions: int
    results: List[Dict[str, Any]]

class AnswerCheckResponse(ApiResponse):
    is_correct: bool
    correct_answer: int
    question: str
    choices: List[str]

class ExplanationResponse(ApiResponse):
    is_correct: bool
    explanation: str
    question: str
    choices: List[str]
    correct_answer: int
    student_answer: int