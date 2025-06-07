from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Body
from typing import Dict, Any, List, Optional, Union
import pymongo
import uuid
import random
import utils
from pydantic import BaseModel, Field,field_validator
import tempfile
import os
from bson import ObjectId
import datetime

# MongoDB 
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["physical_therapy_questions"]

exam_router = APIRouter(prefix="/api/exam", tags=["exam"])

class Question(BaseModel):
    problem_id: Union[str, int]  # Hem string hem int kabul eder
    problem: str
    choices: List[str]
    
    # problem_id string
    @field_validator('problem_id')
    def convert_problem_id_to_string(cls, v):
        return str(v)

# Güncellenmiş Answer modeli  
class Answer(BaseModel):
    problem_id: Union[str, int]  # Hem string hem int kabul eder
    answer: Union[str, int]  # Cevap da string veya int olabilir
    session: Optional[str] = ""
    subject: Optional[str] = ""
    
    # problem_id'yi her zaman string'e dönüştür
    @field_validator('problem_id')
    def convert_problem_id_to_string(cls, v):
        return str(v)
    
    # answer'ı da uygun formata dönüştür
    @field_validator('answer')
    def convert_answer(cls, v):
        return str(v) if v is not None else None

class MergeData(BaseModel):
    questions: List[Question]
    answers: Optional[List[Answer]] = None
    collection_name: str = "exam_questions"

class TestSubmission(BaseModel):
    user_id: str
    answers: Dict[str, int]  # {question_id: selected_answer}

class AnswerCheck(BaseModel):
    question_id: str
    user_answer: int

class QuestionResponse(BaseModel):
    _id: str
    Session: str
    Subject: str
    Problem_ID: str
    Problem: str
    Choices: List[str]
    Answer_Key: Optional[str] = None

# upload questions from pdf 
@exam_router.post("/upload-questions-pdf")
async def upload_questions_pdf(file: UploadFile = File(...)):
    """
    PDF parsing memory version
    """
    try:
        # Dosya içeriğini hafızada tutalım
        file_content = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(file_content)
        
        # PDF'i parse et
        questions =utils.parse_questions_pdf(temp_file_path)
        
        # İşimiz bitti, şimdi dosyayı silebiliriz
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
       
        
        return {"status": "success", "questions": questions}
    
    except Exception as e:
        # Herhangi bir hata durumunda
        raise HTTPException(status_code=500, detail=f"PDF parse işlemi sırasında hata: {str(e)}")

# upload answers from pdf
@exam_router.post("/upload-answers-pdf")
async def upload_answers_pdf(file: UploadFile = File(...)):
    """
    answer key PDF parsing memory version
    """
    try:
        # Dosya içeriğini hafızada tutalım
        file_content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(file_content)
        
        # utils.py içindeki parse fonksiyonunu çağır
        answers = utils.parse_answer_key_pdf(temp_file_path)
        # İşimiz bitti, şimdi dosyayı silebiliriz
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        return {"status": "success", "answers": answers}
    
    except Exception as e:
        # Herhangi bir hata durumunda
        raise HTTPException(status_code=500, detail=f"PDF parse işlemi sırasında hata: {str(e)}")
# merge questions and answers and save to mongodb
@exam_router.post("/merge-and-save")
async def merge_questions_and_answers(data: dict):
    try:
        questions_raw = data.get("questions", [])
        answers_raw = data.get("answers", [])
        collection_name = data.get("collection_name", "exam_questions")
        selected_session = data.get("selected_session", None)
        
        # DEBUG: Gelen verileri kontrol et
        #print(f"📊 Gelen veriler:")
        #print(f"  - Sorular: {len(questions_raw)}")
        #print(f"  - Cevaplar: {len(answers_raw) if answers_raw else 0}")
        #print(f"  - Seçilen Session: '{selected_session}'")
        
        # Questions'ı normalize et
        normalized_questions = []
        for q in questions_raw:
            normalized_q = {
                "problem_id": q.get("problem_id", ""),
                "problem": q.get("problem", ""),
                "choices": q.get("choices", [])
            }
            normalized_questions.append(normalized_q)
        
        
        # Answers'ı normalize et VE session filtreleme uygula
        normalized_answers = []
        if answers_raw:
            for a in answers_raw:
                answer_session = a.get("session", "")
                problem_id = a.get("problem_id", "")
                answer_value = a.get("answer", "")
                
                # Veri doğrulama
                if not problem_id or (not answer_value and answer_value != 0):
                    continue
                
                # Session filtresi kontrolü
                if selected_session and selected_session != "Tümü":
                    if answer_session != selected_session:
                        continue
                
                # Normalize et ve ekle
                normalized_a = {
                    "problem_id": int(problem_id) if str(problem_id).isdigit() else problem_id,
                    "answer": int(answer_value) if str(answer_value).isdigit() else answer_value,
                    "session": answer_session,
                    "subject": a.get("subject", "")
                }
                normalized_answers.append(normalized_a)
        
        #print(f"🔄 Filtreleme sonucu:")
        #print(f"  - Orijinal cevaplar: {len(answers_raw) if answers_raw else 0}")
        #print(f"  - Filtrelenmiş cevaplar: {len(normalized_answers)}")
        
        # Koleksiyonu al
        custom_collection = db[collection_name]
        
        # Kaydedilecek veriyi hazırla - SADECE MERGE İŞLEMİ
        data_to_save = []
        
        if normalized_answers:
            # Soruları ve cevapları birleştir
            merged_data = utils.merge_questions_and_answers_helper(normalized_questions, normalized_answers)
            
            # MongoDB formatına dönüştür
            for item in merged_data:
                mongo_item = {
                    # _id alanını KALDIR - MongoDB otomatik olarak ObjectId atayacak
                    "session": item.get("session", ""),
                    "subject": item.get("subject", ""),
                    "problem_id": item["problem_id"],
                    "problem": item["problem"],
                    "choices": item["choices"],
                    "answer_key": item.get("answer_key"),
                    "created_at": item.get("created_at", datetime.datetime.now()),
                }
                data_to_save.append(mongo_item)
            
            print(f"✅ Birleştirme tamamlandı: {len(merged_data)} kayıt hazır")
        
        # MongoDB'ye kaydet - ObjectId otomatik atanacak
        if data_to_save:
            result = custom_collection.insert_many(data_to_save)
            
            # Başarı mesajını oluştur
            if normalized_answers:
                if selected_session and selected_session != "Tümü":
                    message = f"✅ {len(result.inserted_ids)} soru ve cevap ({selected_session} session'ı) başarıyla kaydedildi"
                else:
                    message = f"✅ {len(result.inserted_ids)} soru ve cevap başarıyla kaydedildi"
            else:
                message = f"✅ {len(result.inserted_ids)} soru başarıyla kaydedildi (cevap anahtarı olmadan)"
            
            print(f"🎉 Kaydetme başarılı: {len(result.inserted_ids)} kayıt")
            #print(f"📋 Atanan ObjectId'ler: {[str(id) for id in result.inserted_ids[:5]]}...")  # İlk 5 ID'yi göster
            
            return {
                "status": "success",
                "message": message,
                "collection": collection_name,
                "saved_count": len(result.inserted_ids),
                "filtered_session": selected_session,
                "sample_ids": [str(id) for id in result.inserted_ids[:3]]  # Örnek ID'ler
            }
        else:
            return {"status": "warning", "message": "Kaydedilecek veri bulunamadı"}
    
    except Exception as e:
        print(f"❌ Kaydetme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Veri kaydetme işlemi sırasında hata: {str(e)}")

# Diagnosis test endpoint
@exam_router.get("/level-test")
async def get_level_test():
    """
    Diagnosis test. This endpoint returns a standardized level test with fixed questions.
    """
    try:
        # Doğru veritabanı ve koleksiyonu kullan
        collection = db["diagnosis_test"]
        
        # Sabit seed ile rastgele seçim - herkes aynı soruları görecek
        #import random
        #random.seed(12345)  # Sabit seed
        
        # Her bir zorluk seviyesinden soruları çek
        easy_questions = list(collection.find({"difficulty": "하"}))
        medium_questions = list(collection.find({"difficulty": "중"}))
        hard_questions = list(collection.find({"difficulty": "상"}))
        
        print(f"Zorluk seviyelerindeki soru sayıları: Kolay:{len(easy_questions)}, Orta:{len(medium_questions)}, Zor:{len(hard_questions)}")
        
        # Her zorluk seviyesinden kaç soru alınacağını belirle
        easy_count = min(10, len(easy_questions))
        medium_count = min(10, len(medium_questions))
        hard_count = min(10, len(hard_questions))
        
        # Sabit seed ile rastgele soruları seç (herkes aynı soruları alacak)
        selected_easy = random.sample(easy_questions, easy_count) if easy_count > 0 else []
        selected_medium = random.sample(medium_questions, medium_count) if medium_count > 0 else []
        selected_hard = random.sample(hard_questions, hard_count) if hard_count > 0 else []
        
        # Tüm soruları birleştir
        all_questions = selected_easy + selected_medium + selected_hard
        
        # Hiç soru bulunamazsa uyarı ver
        if not all_questions:
            raise HTTPException(status_code=404, detail="Hiç soru bulunamadı. Lütfen veritabanınızı kontrol edin.")
        
        # Soruları sabit sırayla karıştır (herkes aynı sırayı görecek)
        random.shuffle(all_questions)
        
        # ObjectId'leri string'e dönüştür
        for question in all_questions:
            if '_id' in question and not isinstance(question['_id'], str):
                question['_id'] = str(question['_id'])
                
            # Streamlit uygulaması için alan adlarını standartlaştır
            if 'Choices' not in question and 'choices' in question:
                question['Choices'] = question['choices']
            elif 'choices' not in question and 'Choices' in question:
                question['choices'] = question['Choices']
                
            if 'Problem' not in question and 'problem' in question:
                question['Problem'] = question['problem']
            elif 'problem' not in question and 'Problem' in question:
                question['problem'] = question['Problem']
                
            if 'Answer Key' not in question and 'answer_key' in question:
                question['Answer Key'] = question['answer_key']
            elif 'answer_key' not in question and 'Answer Key' in question:
                question['answer_key'] = question['Answer Key']
        
        print(f"✅ Standart seviye tespit sınavı hazırlandı: {len(all_questions)} soru")
        print(f"📊 Soru dağılımı - Kolay: {easy_count}, Orta: {medium_count}, Zor: {hard_count}")
        
        return {
            "status": "success",
            "test": all_questions,
            "test_info": {
                "total_questions": len(all_questions),
                "easy_questions": easy_count,
                "medium_questions": medium_count,
                "hard_questions": hard_count,
                "is_standardized": True  # Bu testin standart olduğunu belirt
            }
        }
    
    except Exception as e:
        print(f"Error processing diagnosis test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing diagnosis test:  {str(e)}")


# Diagnosis test submission endpoint
@exam_router.post("/submit-test")
async def submit_test(submission: TestSubmission):
    """
    This endpoint processes the diagnosis test submission. Saving the results to the database and calculating the score.
    """
    try:
        # Doğru koleksiyon adını kullan
        collection = db["diagnosis_test"]
        user_collection = db["users"]
        
        # Debug bilgisi - gelen verileri logla
        print(f"Gelen istek: user_id={submission.user_id}, yanıt sayısı={len(submission.answers)}")
        
        # Veritabanından soruları çek
        questions = []
        for question_id, answer in submission.answers.items():
            # String ID ile ara
            question = collection.find_one({"_id": question_id})
            
            # Bulunamadıysa farklı yollar dene
            if not question:
                try:
                    # ObjectId ile dene
                    obj_id = ObjectId(question_id)
                    question = collection.find_one({"_id": obj_id})
                    
                    if question:
                        print(f"Soru ObjectId ile bulundu: {question_id}")
                except:
                    print(f"ObjectId dönüşümü başarısız: {question_id}")
            
            if question:
                questions.append(question)
            else:
                print(f"UYARI: Soru bulunamadı: {question_id}")
        
        print(f"Bulunan toplam soru: {len(questions)}")
        
        # Score calculation
        score_result = utils.real_calculate_score(submission.answers, questions)
        
        # Detaylı test sonuçlarını hazırla
        detailed_results = []
        for result in score_result["results"]:
            question_id = result["question_id"]
            
            # Soruyu bul
            question_info = next((q for q in questions if str(q.get("_id")) == question_id), None)
            
            if question_info:
                detailed_result = {
                    "question_id": question_id,
                    "question_text": question_info.get("Problem", question_info.get("problem", "")),
                    "choices": question_info.get("Choices", question_info.get("choices", [])),
                    "correct_answer": result["correct_answer"],
                    "student_answer": result["student_answer"],
                    "is_correct": result["correct"],
                    "points_earned": result["points"],
                    "difficulty": question_info.get("difficulty", "하")
                }
                detailed_results.append(detailed_result)
        
        # Test sonuçlarını users koleksiyonuna kaydet
        test_record = {
            "test_date": datetime.datetime.utcnow(),
            "test_type": "level_test",
            "total_score": score_result["score"],
            "level": score_result["level"],
            "correct_count": score_result["correct_count"],
            "total_questions": len(submission.answers),
            "detailed_results": detailed_results
        }
        
        print(f"💾 Kaydedilecek test verisi: {test_record}")
        
        # Kullanıcı bilgilerini güncelle - test geçmişini de ekle
        try:
            # Önce mevcut test geçmişini al - ObjectId ile arama ekle
            user = user_collection.find_one({"_id": submission.user_id})
            
            # String ID ile bulunamadıysa ObjectId ile dene
            if not user:
                try:
                    obj_id = ObjectId(submission.user_id)
                    user = user_collection.find_one({"_id": obj_id})
                    if user:
                        print(f"✅ Kullanıcı ObjectId ile bulundu: {submission.user_id}")
                        # Artık ObjectId ile çalışacağız
                        submission.user_id = obj_id
                except:
                    print(f"❌ ObjectId dönüşümü başarısız: {submission.user_id}")
            
            if not user:
                print(f"❌ Kullanıcı bulunamadı: {submission.user_id}")
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
            
            print(f"✅ Kullanıcı bulundu: {user.get('name', 'İsimsiz')}")
            
            test_history = user.get("test_history", [])
            print(f"📊 Mevcut test geçmişi uzunluğu: {len(test_history)}")
            
            # Yeni test sonucunu ekle
            test_history.append(test_record)
            print(f"➕ Yeni test eklendi, toplam: {len(test_history)}")
            
            # Sadece son 10 testi sakla (çok fazla büyümesin)
            if len(test_history) > 10:
                test_history = test_history[-10:]
                print(f"✂️ Test geçmişi kırpıldı, yeni uzunluk: {len(test_history)}")
            
            # Kullanıcıyı güncelle
            update_result = user_collection.update_one(
                {"_id": submission.user_id},  # Artık ObjectId olabilir
                {"$set": {
                    "test_score": score_result["score"], 
                    "level": score_result["level"],
                    "test_history": test_history,
                    "last_test_date": datetime.datetime.utcnow()
                }}
            )
            
            print(f"✅ Kullanıcı güncellendi: {update_result.modified_count} kayıt")
            
            if update_result.modified_count == 0:
                print("⚠️ Hiçbir kayıt güncellenmedi!")
            
        except Exception as user_update_error:
            print(f"❌ Kullanıcı güncelleme hatası: {str(user_update_error)}")
            import traceback
            print(f"🔍 Hata detayı: {traceback.format_exc()}")
            # Hatayı yine de devam ettir
        
        # API yanıtını döndür
        return {
            "status": "success",
            "score": score_result["score"],
            "level": score_result["level"],
            "correct_count": score_result["correct_count"],
            "total_questions": len(submission.answers),
            "results": score_result["results"],
            "detailed_results": detailed_results  # Frontend için detaylı sonuçlar
        }
    
    except Exception as e:
        import traceback
        print(f"Test değerlendirme hatası: {str(e)}")
        print(traceback.format_exc())
        
        raise HTTPException(status_code=500, detail=f"Test değerlendirme sırasında hata: {str(e)}")


# Retrieve user test history endpoint
@exam_router.get("/user-test-history/{user_id}")
async def get_user_test_history(user_id: str):
    """
    Retrieve user test history
    """
    try:
        user_collection = db["users"]
        print(f"🔍 Test geçmişi isteniyor: user_id={user_id}")
        print(f"🔍 User ID tipi: {type(user_id)}")
        print(f"🔍 User ID uzunluğu: {len(user_id)}")
        
        # Önce string ID ile ara
        print("🔄 String ID ile aranıyor...")
        user = user_collection.find_one({"_id": user_id})
        
        if user:
            print(f"✅ Kullanıcı string ID ile bulundu!")
        else:
            print("❌ String ID ile bulunamadı, ObjectId deneniyor...")
            
            # ObjectId ile dene
            try:
                print(f"🔄 ObjectId dönüşümü deneniyor: {user_id}")
                obj_id = ObjectId(user_id)
                print(f"✅ ObjectId oluşturuldu: {obj_id}")
                
                user = user_collection.find_one({"_id": obj_id})
                
                if user:
                    print(f"✅ Kullanıcı ObjectId ile bulundu: {user_id}")
                else:
                    print(f"❌ ObjectId ile de bulunamadı: {obj_id}")
                    
            except Exception as oid_error:
                print(f"❌ ObjectId dönüşümü başarısız: {str(oid_error)}")
        
        if not user:
            print(f"❌ Kullanıcı hiçbir şekilde bulunamadı: {user_id}")
            
            # Veritabanında gerçekten var mı kontrol et
            print("🔍 Veritabanında tüm kullanıcıları kontrol ediyorum...")
            all_users = list(user_collection.find({}, {"_id": 1, "name": 1}))
            print(f"📊 Toplam kullanıcı sayısı: {len(all_users)}")
            
            for i, u in enumerate(all_users[:5]):  # İlk 5 kullanıcıyı göster
                print(f"  {i+1}. ID: {u.get('_id')} ({type(u.get('_id'))}), Name: {u.get('name')}")
            
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        print(f"✅ Kullanıcı bulundu: {user.get('name', 'İsimsiz')}")
        
        test_history = user.get("test_history", [])
        print(f"📊 Test geçmişi uzunluğu: {len(test_history)}")
        
        if len(test_history) == 0:
            print("ℹ️ Test geçmişi boş")
            return {
                "status": "success",
                "test_history": [],
                "total_tests": 0
            }
        
        # Test geçmişini temizle ve seri hale getirilebilir yap
        cleaned_history = []
        for i, test in enumerate(test_history):
            try:
                print(f"🔄 Test {i+1} işleniyor...")
                
                # Datetime nesnelerini string'e dönüştür
                test_date = test.get("test_date")
                if test_date and hasattr(test_date, 'isoformat'):
                    test_date = test_date.isoformat()
                elif test_date and isinstance(test_date, str):
                    test_date = test_date  # Zaten string
                else:
                    test_date = None
                
                cleaned_test = {
                    "test_date": test_date,
                    "test_type": test.get("test_type", "level_test"),
                    "total_score": test.get("total_score", 0),
                    "level": test.get("level", "하"),
                    "correct_count": test.get("correct_count", 0),
                    "total_questions": test.get("total_questions", 0),
                    "detailed_results": test.get("detailed_results", [])
                }
                
                cleaned_history.append(cleaned_test)
                print(f"✅ Test {i+1} başarıyla işlendi")
                
            except Exception as test_error:
                print(f"❌ Test {i+1} işlenirken hata: {str(test_error)}")
                continue
        
        # Tarihe göre sırala (en yeni en üstte)
        try:
            cleaned_history.sort(
                key=lambda x: x.get("test_date", "1900-01-01T00:00:00") or "1900-01-01T00:00:00", 
                reverse=True
            )
            print("✅ Testler tarihe göre sıralandı")
        except Exception as sort_error:
            print(f"⚠️ Sıralama hatası: {str(sort_error)}")
        
        print(f"🎉 Test geçmişi başarıyla hazırlandı: {len(cleaned_history)} test")
        
        return {
            "status": "success",
            "test_history": cleaned_history,
            "total_tests": len(cleaned_history)
        }
    
    except Exception as e:
        print(f"❌ Test geçmişi getirme hatası: {str(e)}")
        import traceback
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test geçmişi alınırken hata: {str(e)}")


# Retrieve specific test details endpoint
@exam_router.get("/test-details/{user_id}/{test_index}")
async def get_test_details(user_id: str, test_index: int):
    """
    Retrieve user test history details by user_id and test_index
    """
    try:
        user_collection = db["users"]
        print(f"🔍 Test detayları isteniyor: user_id={user_id}, test_index={test_index}")
        
        # Önce string ID ile ara
        user = user_collection.find_one({"_id": user_id})
        
        # Bulunamadıysa ObjectId ile dene
        if not user:
            try:
                obj_id = ObjectId(user_id)
                user = user_collection.find_one({"_id": obj_id})
                if user:
                    print(f"✅ Kullanıcı ObjectId ile bulundu: {user_id}")
            except Exception as oid_error:
                print(f"❌ ObjectId dönüşümü başarısız: {str(oid_error)}")
        
        if not user:
            print(f"❌ Kullanıcı bulunamadı: {user_id}")
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        print(f"✅ Kullanıcı bulundu: {user.get('name', 'İsimsiz')}")
        
        test_history = user.get("test_history", [])
        print(f"📊 Test geçmişi uzunluğu: {len(test_history)}")
        
        if test_index >= len(test_history) or test_index < 0:
            print(f"❌ Geçersiz test indeksi: {test_index} (maks: {len(test_history)-1})")
            raise HTTPException(status_code=404, detail="Test bulunamadı")
        
        # Tarihe göre sırala ve istenen testi al
        try:
            # Tarihleri güvenli şekilde sıralama
            test_history_with_dates = []
            for i, test in enumerate(test_history):
                test_date = test.get("test_date")
                if hasattr(test_date, 'timestamp'):
                    sort_key = test_date.timestamp()
                elif isinstance(test_date, str):
                    try:
                        from datetime import datetime
                        parsed_date = datetime.fromisoformat(test_date.replace('Z', '+00:00'))
                        sort_key = parsed_date.timestamp()
                    except:
                        sort_key = 0
                else:
                    sort_key = 0
                
                test_history_with_dates.append((sort_key, i, test))
            
            # Sıralama (en yeni en üstte)
            test_history_with_dates.sort(key=lambda x: x[0], reverse=True)
            sorted_tests = [item[2] for item in test_history_with_dates]
            
            print(f"✅ Testler sıralandı, istenilen indeks: {test_index}")
            
        except Exception as sort_error:
            print(f"⚠️ Sıralama hatası: {str(sort_error)}, sıralama olmadan devam ediliyor")
            sorted_tests = test_history
        
        # İstenen testi al
        test_details = sorted_tests[test_index]
        print(f"✅ Test {test_index} seçildi")
        
        # Datetime nesnelerini string'e dönüştür
        if "test_date" in test_details:
            test_date = test_details["test_date"]
            if hasattr(test_date, 'isoformat'):
                test_details["test_date"] = test_date.isoformat()
            print(f"✅ Test tarihi dönüştürüldü")
        
        # Detailed results'ı temizle
        detailed_results = test_details.get("detailed_results", [])
        print(f"📊 Detaylı sonuçlar: {len(detailed_results)} soru")
        
        # Her soru sonucunu kontrol et
        for i, result in enumerate(detailed_results[:3]):  # İlk 3 soruyu logla
            print(f"  Soru {i+1}: {result.get('question_text', 'Metin yok')[:50]}...")
            print(f"    Doğru cevap: {result.get('correct_answer')}")
            print(f"    Öğrenci cevabı: {result.get('student_answer')}")
            print(f"    Seçenekler: {len(result.get('choices', []))} adet")
        
        return {
            "status": "success",
            "test_details": test_details
        }
    
    except Exception as e:
        print(f"❌ Test detayları getirme hatası: {str(e)}")
        import traceback
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test detayları alınırken hata: {str(e)}")
#UNUSED
#@exam_router.post("/check-answer")
#async def check_answer(data: AnswerCheck):
    #"""
    #Tek bir sorunun cevabını kontrol eder
    #"""
    #try:
        #collection = db["physical_therapy_questions"]
#        
        ## MongoDB'den soruyu bul - ObjectId ile
        #try:
            #obj_id = ObjectId(data.question_id)
            #question = collection.find_one({"_id": obj_id})
        #except:
            ## String ID ile dene
            #question = collection.find_one({"_id": data.question_id})
#        
        #if not question:
            #raise HTTPException(status_code=404, detail="Soru bulunamadı")
#        
        ## Doğru cevabı kontrol et
        #correct_answer = question.get("answer_key")
        #is_correct = data.user_answer == correct_answer
#        
        #return {
            #"status": "success",
            #"is_correct": is_correct,
            #"correct_answer": correct_answer
        #}
#    
    #except Exception as e:
        #raise HTTPException(status_code=500, detail=f"Cevap kontrolü sırasında hata: {str(e)}")


#Listing collections from mongodb
@exam_router.get("/collections")
async def get_collections():
    """
    MongoDB all collections list
    """
    try:
        collections = db.list_collection_names()
        return {"status": "success", "collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Koleksiyonları listelerken hata: {str(e)}")


# Practice question endpoint
@exam_router.get("/practice-question/{difficulty}")
async def get_practice_question(difficulty: str):
    """
    Retrieve a random practice question based on difficulty level
    - difficulty: "하" (easy), "중" (medium), "상" (hard)
    """
    try:
        # Zorluk seviyesi kontrolü
        valid_difficulties = ["하", "중", "상"]
        if difficulty not in valid_difficulties:
            raise HTTPException(status_code=400, detail=f"Geçersiz zorluk seviyesi. Geçerli değerler: {valid_difficulties}")
        
        # İlgili zorluk seviyesindeki soruları getir
        collection = db["diagnosis_test"]
        questions = list(collection.find({"difficulty": difficulty}))
        
        if not questions:
            raise HTTPException(status_code=404, detail=f"'{difficulty}' seviyesinde soru bulunamadı")
        
        # Rastgele bir soru seç
        import random
        selected_question = random.choice(questions)
        
        # ObjectId'yi string'e dönüştür
        if '_id' in selected_question and not isinstance(selected_question['_id'], str):
            selected_question['_id'] = str(selected_question['_id'])
        
        # Alan adlarını standartlaştır
        if 'Choices' not in selected_question and 'choices' in selected_question:
            selected_question['Choices'] = selected_question['choices']
        elif 'choices' not in selected_question and 'Choices' in selected_question:
            selected_question['choices'] = selected_question['Choices']
            
        if 'Problem' not in selected_question and 'problem' in selected_question:
            selected_question['Problem'] = selected_question['problem']
        elif 'problem' not in selected_question and 'Problem' in selected_question:
            selected_question['problem'] = selected_question['Problem']
            
        if 'Answer Key' not in selected_question and 'answer_key' in selected_question:
            selected_question['Answer Key'] = selected_question['answer_key']
        elif 'answer_key' not in selected_question and 'Answer Key' in selected_question:
            selected_question['answer_key'] = selected_question['Answer Key']
        
        return {
            "status": "success",
            "question": selected_question,
            "difficulty": difficulty
        }
    
    except Exception as e:
        print(f"Pratik soru getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pratik soru getirilirken hata: {str(e)}")


#Submit practice answer endpoint
@exam_router.post("/submit-practice-answer")
async def submit_practice_answer(data: dict):
    """
    Submit a practice question answer for evaluation
    """
    try:
        question_id = data.get("question_id")
        student_answer = data.get("student_answer")
        
        if not question_id or student_answer is None:
            raise HTTPException(status_code=400, detail="question_id ve student_answer gereklidir")
        
        # Soruyu bul
        collection = db["diagnosis_test"]
        question = collection.find_one({"_id": question_id})
        
        if not question:
            try:
                obj_id = ObjectId(question_id)
                question = collection.find_one({"_id": obj_id})
            except:
                pass
        
        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")
        
        # Doğru cevabı al
        correct_answer = question.get("Answer Key", question.get("answer_key"))
        
        if correct_answer is None:
            raise HTTPException(status_code=400, detail="Sorunun doğru cevabı bulunamadı")
        
        # Cevap kontrolü
        is_correct = int(student_answer) == int(correct_answer)
        
        return {
            "status": "success",
            "is_correct": is_correct,
            "correct_answer": int(correct_answer),
            "student_answer": int(student_answer),
            "question_id": str(question.get("_id"))
        }
    
    except Exception as e:
        print(f"Pratik cevap değerlendirme hatası: {str(e)}")

# Retrieve questions from a specific collection
@exam_router.get("/get-questions/{collection_name}")
async def get_questions(collection_name: str, limit: int = 20, skip: int = 0):
    """
    Retrieve questions from a specific collection
    """
    try:
        custom_collection = db[collection_name]
        total = custom_collection.count_documents({})
        questions = list(custom_collection.find({}).skip(skip).limit(limit))
        
        # ObjectId'yi string'e dönüştür
        for question in questions:
            if '_id' in question and not isinstance(question['_id'], str):
                question['_id'] = str(question['_id'])
        
        return {
            "status": "success", 
            "questions": questions,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veri çekme işlemi sırasında hata: {str(e)}")