# type_based_bkt_router.py - Type-Based BKT API

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import pymongo
from type_based_bkt_system import TypeBasedPhysioTherapyBKT
from pydantic import BaseModel

# MongoDB connection
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
bkt_system = TypeBasedPhysioTherapyBKT(mongo_client)

bkt_router = APIRouter(prefix="/api/bkt", tags=["bkt"])

class BKTUpdateRequest(BaseModel):
    user_id: str
    question_data: Dict  # type, difficulty 포함
    student_answer: int
    is_correct: bool

@bkt_router.post("/update-knowledge")
async def update_bkt_knowledge(request: BKTUpdateRequest):
    """학생 답변 후 BKT 지식 상태 업데이트 (TYPE 기반)"""
    try:
        result = bkt_system.update_bkt_with_answer(
            user_id=request.user_id,
            question_data=request.question_data,
            student_answer=request.student_answer,
            is_correct=request.is_correct
        )
        
        return {
            "status": "success",
            "bkt_update": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BKT update error: {str(e)}")

@bkt_router.get("/mastery-report/{user_id}")
async def get_mastery_report(user_id: str):
    """사용자의 상세 습득도 리포트 (TYPE 기반)"""
    try:
        report = bkt_system.get_mastery_report(user_id)
        return {
            "status": "success",
            "report": report
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")

@bkt_router.get("/type-summary/{user_id}")
async def get_type_summary(user_id: str):
    """사용자의 type별 간단 요약"""
    try:
        summary = bkt_system.get_type_summary(user_id)
        return {
            "status": "success",
            "summary": summary
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary error: {str(e)}")

@bkt_router.get("/weak-types/{user_id}")
async def get_weak_types(user_id: str, threshold: float = 0.6):
    """사용자의 약한 문제 유형들"""
    try:
        weak_types = bkt_system.get_weak_types(user_id, threshold)
        return {
            "status": "success",
            "weak_types": weak_types,
            "count": len(weak_types)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weak types error: {str(e)}")

@bkt_router.get("/adaptive-questions/{user_id}")
async def get_adaptive_questions(user_id: str, num_questions: int = 10):
    """type별 약점 기반 적응형 문제 추천"""
    try:
        questions = bkt_system.get_adaptive_questions_by_type(user_id, num_questions)
        
        return {
            "status": "success",
            "recommended_questions": questions,
            "total_count": len(questions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adaptive questions error: {str(e)}")

@bkt_router.get("/available-types")
async def get_available_types():
    """시스템에서 추적 가능한 모든 문제 유형 목록"""
    try:
        types = bkt_system._get_unique_types()
        return {
            "status": "success",
            "types": types,
            "total_count": len(types)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Types error: {str(e)}")

@bkt_router.get("/type-performance/{user_id}/{question_type}")
async def get_type_performance(user_id: str, question_type: str):
    """특정 type에 대한 상세 성과"""
    try:
        bkt_state = bkt_system.get_user_bkt_state(user_id)
        
        if question_type not in bkt_state["type_mastery"]:
            return {
                "status": "success",
                "type": question_type,
                "message": "해당 유형에 대한 데이터가 없습니다.",
                "performance": None
            }
        
        type_data = bkt_state["type_mastery"][question_type]
        
        performance = {
            "type": question_type,
            "mastery_probability": type_data["mastery_probability"],
            "total_attempts": type_data["total_attempts"],
            "correct_answers": type_data["correct_answers"],
            "accuracy": type_data["correct_answers"] / type_data["total_attempts"] if type_data["total_attempts"] > 0 else 0,
            "last_updated": type_data["last_updated"],
            "difficulty_breakdown": type_data["difficulty_performance"]
        }
        
        return {
            "status": "success",
            "performance": performance
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Type performance error: {str(e)}")

@bkt_router.post("/reset-user-bkt/{user_id}")
async def reset_user_bkt(user_id: str):
    """사용자의 BKT 데이터 초기화 (개발/테스트용)"""
    try:
        # BKT 컬렉션에서 사용자 데이터 삭제
        result = bkt_system.bkt_collection.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            message = f"사용자 {user_id}의 BKT 데이터가 초기화되었습니다."
        else:
            message = f"사용자 {user_id}의 BKT 데이터가 존재하지 않습니다."
        
        return {
            "status": "success",
            "message": message,
            "deleted_count": result.deleted_count
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset error: {str(e)}")

@bkt_router.get("/debug/all-types")
async def debug_get_all_types():
    """디버그: 데이터베이스의 모든 types 확인"""
    try:
        collections = ["diagnosis_test", "exam_questions"]
        all_types = {}
        
        for collection_name in collections:
            collection = bkt_system.db[collection_name]
            
            # type 필드의 모든 unique values
            types = collection.distinct("type")
            
            # 각 type의 문제 수도 확인
            type_counts = {}
            for qtype in types:
                if qtype:  # None이 아닌 경우만
                    count = collection.count_documents({"type": qtype})
                    type_counts[str(qtype)] = count
            
            all_types[collection_name] = {
                "unique_types": [str(t) for t in types if t],
                "type_counts": type_counts,
                "total_unique": len([t for t in types if t])
            }
        
        return {
            "status": "success",
            "collections": all_types
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")