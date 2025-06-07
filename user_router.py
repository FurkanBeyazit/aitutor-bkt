from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any, List, Optional
import pymongo
import uuid
import bcrypt
import random
import string
import datetime 
from pydantic import BaseModel, EmailStr, Field

# MongoDB bağlantısı
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["physical_therapy_questions"]
user_collection = db["users"]

# User router
user_router = APIRouter(prefix="/api/user", tags=["user"])
from models import UserRegister, UserLogin, GoogleLogin, UpdateProfile, UpdateScore

@user_router.post("/register")
async def register_user(user_data: UserRegister):
    """
    New user registration endpoint.
    """
    try:
        # check if the email already exists
        existing_user = user_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일 주소입니다.")
        
        # PW hashing
        password_bytes = user_data.password.encode('utf-8')
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        
        # Kullanıcı ID'si oluştur
        #user_id = str(uuid.uuid4())
        
        # data
        new_user = {
            #"_id": user_id,
            "email": user_data.email,
            "password": hashed_password.decode('utf-8'),  # Hash'i string olarak kaydet
            "name": user_data.name,
            "grade": user_data.grade,
            "department": user_data.department,
            "role": "student",
            "test_score": 0,
            "level": None,
            "test_history": [],  # YENİ: Test geçmişi
            "last_test_date": None,  # YENİ: Son test tarihi
            "created_at": datetime.datetime.utcnow(),  # YENİ: Kayıt tarihi
            "updated_at": datetime.datetime.utcnow()   # YENİ: Güncelleme tarihi
        }
        
        # MongoDB 
        result = user_collection.insert_one(new_user)
        
        # remove pw
        response_user = new_user.copy()
        response_user.pop("password")
        
        # ObjectId => string
        if "_id" in response_user:
            response_user["user_id"] = str(response_user.pop("_id"))
        
        
        if "created_at" in response_user and hasattr(response_user["created_at"], 'isoformat'):
            response_user["created_at"] = response_user["created_at"].isoformat()
        if "updated_at" in response_user and hasattr(response_user["updated_at"], 'isoformat'):
            response_user["updated_at"] = response_user["updated_at"].isoformat()
        if "last_login" in response_user and hasattr(response_user["last_login"], 'isoformat'):
            response_user["last_login"] = response_user["last_login"].isoformat()
        if "last_test_date" in response_user and hasattr(response_user["last_test_date"], 'isoformat'):
            response_user["last_test_date"] = response_user["last_test_date"].isoformat()
        
        return {
            "status": "success",
            "message": "Kullanıcı başarıyla kaydedildi",
            "user": response_user
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kullanıcı kaydı sırasında hata: {str(e)}")

@user_router.post("/login")
async def login_user(login_data: UserLogin):
    """
    Kullanıcı girişi yap - Role bilgisini de döndür
    """
    try:
        # Kullanıcıyı e-posta ile bul
        user = user_collection.find_one({"email": login_data.email})
        
        if not user:
            raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre")
        
        # pw check
        stored_password = user.get("password", "")
        
        
        if stored_password.startswith("$2b$"):
            # Şifre doğrulama
            is_valid = bcrypt.checkpw(
                login_data.password.encode('utf-8'),
                stored_password.encode('utf-8')
            )
            
            if not is_valid:
                raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre")
        else:
            # Şifre hash'lenmemişse (eski kayıtlar için)
            if stored_password != login_data.password:
                raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre")
            
            # Şifreyi hash'leyip güncelle
            hashed_password = bcrypt.hashpw(
                login_data.password.encode('utf-8'),
                bcrypt.gensalt()
            )
            
            user_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"password": hashed_password.decode('utf-8')}}
            )
        
        # Son giriş tarihini güncelle - YENİ EKLENEN
        user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.datetime.utcnow()}}
        )
        
        # Kullanıcı bilgilerini döndür (şifre hariç) - ROL BİLGİSİNİ DE EKLEYİN
        response_user = {
            "user_id": str(user["_id"]),  # ObjectId'yi string'e dönüştür
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "department": user.get("department", ""),
            "grade": user.get("grade", 0),
            "test_score": user.get("test_score", 0),
            "level": user.get("level", None),
            "role": user.get("role", "student"),  # ROL BİLGİSİNİ EKLEMEYE UNUTMAYIN!
            "test_count": len(user.get("test_history", [])),  # YENİ: Test sayısı
        }
        
        # Datetime alanlarını güvenli şekilde dönüştür
        last_test_date = user.get("last_test_date")
        if last_test_date and hasattr(last_test_date, 'isoformat'):
            response_user["last_test_date"] = last_test_date.isoformat()
        else:
            response_user["last_test_date"] = None
        
        return {
            "status": "success",
            "message": "Giriş başarılı",
            "user": response_user
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Giriş sırasında hata: {str(e)}")

@user_router.post("/google-login")
async def google_login(login_data: GoogleLogin):
    """
    Google hesabıyla giriş yap veya kayıt ol.
    """
    try:
        # Kullanıcıyı e-posta ile kontrol et
        user = user_collection.find_one({"email": login_data.email})
        
        if not user:
            # Kullanıcı yoksa yeni kayıt oluştur
            # Rastgele 8 karakterli şifre oluştur
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # Şifreyi hashle
            hashed_password = bcrypt.hashpw(random_password.encode('utf-8'), bcrypt.gensalt())
            
            # Kullanıcı ID'si oluştur
            #user_id = str(uuid.uuid4())
            
            # Yeni kullanıcı verilerini hazırla - YENİ ALANLAR EKLENEN
            new_user = {
                #"_id": user_id,
                "email": login_data.email,
                "password": hashed_password.decode('utf-8'),
                "name": login_data.name,
                "department": "no info",
                "grade": 0,
                "role": "googleuser",
                "test_score": 0,
                "level": None,
                "test_history": [],  # YENİ: Test geçmişi
                "last_test_date": None,  # YENİ: Son test tarihi
                "created_at": datetime.datetime.now(),  
                "updated_at": datetime.datetime.now(),  
                "last_login": datetime.datetime.now()   
            }
            
            # MongoDB'ye ekle
            result = user_collection.insert_one(new_user)
            
            # Response için kullanıcı bilgilerini hazırla
            response_user = new_user.copy()
            response_user.pop("password")
            
            # ObjectId'leri string'e dönüştür
            if "_id" in response_user:
                response_user["user_id"] = str(response_user.pop("_id"))
            
            # Datetime objelerini string'e dönüştür
            if "created_at" in response_user and hasattr(response_user["created_at"], 'isoformat'):
                response_user["created_at"] = response_user["created_at"].isoformat()
            if "updated_at" in response_user and hasattr(response_user["updated_at"], 'isoformat'):
                response_user["updated_at"] = response_user["updated_at"].isoformat()
            if "last_login" in response_user and hasattr(response_user["last_login"], 'isoformat'):
                response_user["last_login"] = response_user["last_login"].isoformat()
            if "last_test_date" in response_user and hasattr(response_user["last_test_date"], 'isoformat'):
                response_user["last_test_date"] = response_user["last_test_date"].isoformat()
            
            response_user["test_count"] = 0  # YENİ: Test sayısı
            
            return {
                "status": "success",
                "message": "Google user registered successfully",
                "user": response_user
            }
        else:
            # Kullanıcı zaten varsa giriş yap
            # Son giriş tarihini güncelle - YENİ EKLENEN
            user_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.datetime.utcnow()}}
            )
            
            response_user = {
                #"user_id": str(user["_id"]),  # ObjectId'yi string'e dönüştür
                "name": user.get("name", login_data.name),
                "email": user.get("email", login_data.email),
                "department": user.get("department", "no info"),
                "grade": user.get("grade", 0),
                "test_score": user.get("test_score", 0),
                "level": user.get("level", None),
                "role": user.get("role", "googleuser"),
                "test_count": len(user.get("test_history", [])),  # YENİ: Test sayısı
            }
            
            # Datetime alanlarını güvenli şekilde dönüştür
            last_test_date = user.get("last_test_date")
            if last_test_date and hasattr(last_test_date, 'isoformat'):
                response_user["last_test_date"] = last_test_date.isoformat()
            else:
                response_user["last_test_date"] = None
            
            return {
                "status": "success",
                "message": "Google login successful",
                "user": response_user
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google login error: {str(e)}")

@user_router.post("/update-profile")
async def update_profile(profile_data: UpdateProfile):
    """
    Kullanıcı profilini güncelle.
    """
    try:
        # Kullanıcıyı e-posta ile bul
        user = user_collection.find_one({"email": profile_data.email})
        
        if not user:
            raise HTTPException(status_code=404, detail="no user found with this email")
        
        # Profil bilgilerini güncelle - YENİ GÜNCELLEME TARİHİ EKLENEN
        updated_data = {
            "department": profile_data.department,
            "grade": profile_data.grade,
            "updated_at": datetime.datetime.now()  # YENİ: Güncelleme tarihi
        }
        
        result = user_collection.update_one(
            {"email": profile_data.email},
            {"$set": updated_data}
        )
        
        if result.modified_count == 0:
            # Değişiklik yapılmadıysa, mevcut kullanıcı bilgilerini döndür
            response_user = {
                #"user_id": str(user["_id"]),  # ObjectId'yi string'e dönüştür
                "name": user.get("name", ""),
                "email": user.get("email", ""),
                "department": user.get("department", ""),
                "grade": user.get("grade", 0),
                "test_score": user.get("test_score", 0),
                "level": user.get("level", None),
                "role": user.get("role", "student"),
                "test_count": len(user.get("test_history", [])),  # YENİ: Test sayısı
            }
            
            # Datetime alanlarını güvenli şekilde dönüştür
            last_test_date = user.get("last_test_date")
            if last_test_date and hasattr(last_test_date, 'isoformat'):
                response_user["last_test_date"] = last_test_date.isoformat()
            else:
                response_user["last_test_date"] = None
            
            return {
                "status": "warning",
                "message": "No changes made to the profile",
                "user": response_user
            }
        
        # Güncellenmiş kullanıcı bilgilerini al
        updated_user = user_collection.find_one({"email": profile_data.email})
        
        # Response için kullanıcı bilgilerini hazırla
        response_user = {
            "user_id": str(updated_user["_id"]),  # ObjectId'yi string'e dönüştür
            "name": updated_user.get("name", ""),
            "email": updated_user.get("email", ""),
            "department": updated_user.get("department", ""),
            "grade": updated_user.get("grade", 0),
            "test_score": updated_user.get("test_score", 0),
            "level": updated_user.get("level", None),
            "role": updated_user.get("role", "student"),
            "test_count": len(updated_user.get("test_history", [])),  # YENİ: Test sayısı
        }
        
        # Datetime alanlarını güvenli şekilde dönüştür
        last_test_date = updated_user.get("last_test_date")
        if last_test_date and hasattr(last_test_date, 'isoformat'):
            response_user["last_test_date"] = last_test_date.isoformat()
        else:
            response_user["last_test_date"] = None
        
        return {
            "status": "success",
            "message": "updated profile successfully",
            "user": response_user
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile update error: {str(e)}")

@user_router.post("/update-score")
async def update_score(score_data: UpdateScore):
    """
    Kullanıcının test skorunu güncelle.
    """
    try:
        # Kullanıcıyı e-posta ile bul
        user = user_collection.find_one({"email": score_data.email})
        
        if not user:
            raise HTTPException(status_code=404, detail="No user found with this email")
        
        # Öğrenci seviyesini belirle
        student_level = "하"  # Varsayılan seviye
        if score_data.test_score >= 80:
            student_level = "상"
        elif score_data.test_score >= 50:
            student_level = "중"
        
        # Skoru güncelle - YENİ GÜNCELLEME TARİHİ EKLENEN
        updated_data = {
            "test_score": score_data.test_score,
            "level": student_level,
            "updated_at": datetime.datetime.now # YENİ: Güncelleme tarihi
        }
        
        result = user_collection.update_one(
            {"email": score_data.email},
            {"$set": updated_data}
        )
        
        if result.modified_count == 0:
            # Değişiklik yapılmadıysa, mevcut kullanıcı bilgilerini döndür
            response_user = {
                "user_id": str(user["_id"]),  # ObjectId'yi string'e dönüştür
                "name": user.get("name", ""),
                "email": user.get("email", ""),
                "department": user.get("department", ""),
                "grade": user.get("grade", 0),
                "test_score": user.get("test_score", 0),
                "level": user.get("level", None),
                "role": user.get("role", "student"),
                "test_count": len(user.get("test_history", [])),  # YENİ: Test sayısı
            }
            
            # Datetime alanlarını güvenli şekilde dönüştür
            last_test_date = user.get("last_test_date")
            if last_test_date and hasattr(last_test_date, 'isoformat'):
                response_user["last_test_date"] = last_test_date.isoformat()
            else:
                response_user["last_test_date"] = None
            
            return {
                "status": "warning",
                "message": "No changes made to the score",
                "user": response_user
            }
        
        # Güncellenmiş kullanıcı bilgilerini al
        updated_user = user_collection.find_one({"email": score_data.email})
        
        # Response için kullanıcı bilgilerini hazırla
        response_user = {
            "user_id": str(updated_user["_id"]),  # ObjectId'yi string'e dönüştür
            "name": updated_user.get("name", ""),
            "email": updated_user.get("email", ""),
            "department": updated_user.get("department", ""),
            "grade": updated_user.get("grade", 0),
            "test_score": updated_user.get("test_score", 0),
            "level": updated_user.get("level", None),
            "role": updated_user.get("role", "student"),
            "test_count": len(updated_user.get("test_history", [])),  # YENİ: Test sayısı
        }
        
        # Datetime alanlarını güvenli şekilde dönüştür
        last_test_date = updated_user.get("last_test_date")
        if last_test_date and hasattr(last_test_date, 'isoformat'):
            response_user["last_test_date"] = last_test_date.isoformat()
        else:
            response_user["last_test_date"] = None
        
        return {
            "status": "success",
            "message": "Test score update successful",
            "user": response_user
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Score update error: {str(e)}")

# YENİ ENDPOINT: Kullanıcı istatistiklerini getir
@user_router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """
    Kullanıcının detaylı istatistiklerini getir
    """
    try:
        user = user_collection.find_one({"_id": user_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        test_history = user.get("test_history", [])
        
        # İstatistikleri hesapla
        stats = {
            "total_tests": len(test_history),
            "average_score": 0,
            "highest_score": 0,
            "latest_level": user.get("level"),
            "total_correct_answers": 0,
            "total_questions_attempted": 0,
            "level_distribution": {"하": 0, "중": 0, "상": 0},
            "monthly_test_count": {},
            "improvement_trend": []
        }
        
        if test_history:
            # Skorlar
            scores = [test.get("total_score", 0) for test in test_history]
            stats["average_score"] = round(sum(scores) / len(scores), 1)
            stats["highest_score"] = max(scores)
            
            # Doğru cevaplar
            stats["total_correct_answers"] = sum(test.get("correct_count", 0) for test in test_history)
            stats["total_questions_attempted"] = sum(test.get("total_questions", 0) for test in test_history)
            
            # Seviye dağılımı
            for test in test_history:
                level = test.get("level", "하")
                if level in stats["level_distribution"]:
                    stats["level_distribution"][level] += 1
            
            # İlerleme trendi (son 5 test)
            recent_tests = test_history[-5:]
            stats["improvement_trend"] = [test.get("total_score", 0) for test in recent_tests]
        
        return {
            "status": "success",
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 문제제: {str(e)}")