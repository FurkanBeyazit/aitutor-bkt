import pymongo
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

class TypeBasedPhysioTherapyBKT:
    """
    Type-Based Physical Therapy BKT System
    Veritabanındaki 'type' alanını (uzman bilgisi) kullanır
    """
    
    def __init__(self, mongo_client):
        self.db = mongo_client["physical_therapy_questions"]
        self.users_collection = self.db["users"]
        self.bkt_collection = self.db["bkt_tracking"]
        
        # ⭐ İYİLEŞTİRİLMİŞ - Daha konservatif ve güvenilir parametreler
        self.difficulty_params = {
            "하": {  # 쉬움
                "slip": 0.05,        # ⬇️ Azaltıldı: Bildiği halde hata yapma
                "guess": 0.20,       # ⬇️ Azaltıldı: Şans eseri doğru yapma  
                "learn": 0.10,       # ⬇️ Azaltıldı: Yavaş öğrenme
                "prior": 0.2         # ⬇️ Azaltıldı: Düşük başlangıç
            },
            "중": {  # 보통
                "slip": 0.08,        # ⬇️ Azaltıldı
                "guess": 0.15,       # ⬇️ Azaltıldı
                "learn": 0.08,       # ⬇️ Azaltıldı
                "prior": 0.15        # ⬇️ Azaltıldı
            },
            "상": {  # 어려움
                "slip": 0.12,        # ⬇️ Azaltıldı
                "guess": 0.10,       # ⬇️ Azaltıldı
                "learn": 0.05,       # ⬇️ Azaltıldı
                "prior": 0.1         # ⬇️ Azaltıldı
            }
        }
        
        # ⭐ YENİ: Güvenilirlik ayarları
        self.reliability_settings = {
            "min_attempts_for_reliable": 5,
            "min_attempts_for_mastery": 8,
            "mastery_threshold": 0.8,
            "confidence_levels": {
                "very_low": (0, 3),      # 0-2 soru: Çok düşük güven
                "low": (3, 5),           # 3-4 soru: Düşük güven  
                "medium": (5, 10),       # 5-9 soru: Orta güven
                "high": (10, float('inf'))  # 10+ soru: Yüksek güven
            }
        }
    def get_confidence_level(self, attempts: int) -> str:
        """Attempt sayısına göre güven seviyesi"""
        for level, (min_att, max_att) in self.reliability_settings["confidence_levels"].items():
            if min_att <= attempts < max_att:
                return level
        return "very_low"        
    def calculate_reliable_mastery(self, type_data: Dict) -> Dict:
        """Güvenilirlik bilgisi ile mastery hesaplama"""
        attempts = type_data.get("total_attempts", 0)
        raw_mastery = type_data.get("mastery_probability", 0)
        confidence_level = self.get_confidence_level(attempts)
        
        # Güvenilirlik durumu
        is_reliable = attempts >= self.reliability_settings["min_attempts_for_reliable"]
        is_mastery_ready = attempts >= self.reliability_settings["min_attempts_for_mastery"]
        
        # Display text oluştur
        if confidence_level == "very_low":
            status = "⏳ Çok az veri"
            color = "warning"
        elif confidence_level == "low":
            status = "🌱 Başlangıç"
            color = "info"
        elif confidence_level == "medium":
            status = "📚 Gelişiyor"
            color = "success"
        else:  # high
            if raw_mastery >= self.reliability_settings["mastery_threshold"]:
                status = "🏆 Gerçek Mastery"
                color = "success"
            else:
                status = "💪 Güvenilir Veri"
                color = "info"
        
        display_text = f"{raw_mastery*100:.0f}% ({attempts} soru) {status}"
        
        # Mastery seviyesi belirleme
        if raw_mastery >= 0.8 and is_mastery_ready:
            level = "마스터"
            emoji = "🏆"
        elif raw_mastery >= 0.65 and is_reliable:
            level = "숙련"
            emoji = "🥈"
        elif raw_mastery >= 0.45:
            level = "학습중"
            emoji = "📚"
        else:
            level = "초급"
            emoji = "🌱"
        
        return {
            "mastery_probability": raw_mastery,
            "level": level,
            "emoji": emoji,
            "color": color,
            "attempts": attempts,
            "display_text": display_text,
            "confidence_level": confidence_level,
            "is_reliable": is_reliable,
            "is_mastery_ready": is_mastery_ready,
            "status": status,
            "needs_more_practice": attempts < self.reliability_settings["min_attempts_for_reliable"]
        }


    def get_user_bkt_state(self, user_id: str) -> Dict:
        """사용자의 현재 BKT 상태 가져오기"""
        bkt_record = self.bkt_collection.find_one({"user_id": user_id})
        
        if not bkt_record:
            initial_state = self._create_initial_bkt_state(user_id)
            self.bkt_collection.insert_one(initial_state)
            return initial_state
        
        return bkt_record

    def _create_initial_bkt_state(self, user_id: str) -> Dict:
        """새 사용자의 초기 BKT 상태 생성"""
        # 데이터베이스에서 unique types 가져오기
        unique_types = self._get_unique_types()
        
        initial_state = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type_mastery": {},  # type별 습득 확률
            "total_attempts": 0,
            "total_correct": 0,
            "overall_mastery": 0.4  # 전체 습득도
        }
        
        # 모든 type에 대해 초기값 설정
        for question_type in unique_types:
            initial_state["type_mastery"][question_type] = {
                "mastery_probability": 0.4,  # 초기 습득 확률
                "total_attempts": 0,
                "correct_answers": 0,
                "last_updated": datetime.now(),
                "difficulty_performance": {  # 난이도별 성과
                    "하": {"attempts": 0, "correct": 0, "mastery": 0.5},
                    "중": {"attempts": 0, "correct": 0, "mastery": 0.4},
                    "상": {"attempts": 0, "correct": 0, "mastery": 0.3}
                }
            }
        
        return initial_state

    def _get_unique_types(self) -> List[str]:
        """데이터베이스에서 unique types 가져오기 - SADECE DB'deki types"""
        collections = ["diagnosis_test", "exam_questions"]
        unique_types = set()
        
        for collection_name in collections:
            try:
                collection = self.db[collection_name]
                
                # 'type' 필드에서 unique values 가져오기
                types = collection.distinct("type")
                
                # ⭐ SADECE NULL olmayan ve boş olmayan types ekle - hiçbir manual filtreleme yok
                for t in types:
                    if t and str(t).strip():
                        type_str = str(t).strip()
                        unique_types.add(type_str)
                
                print(f"📋 Collection {collection_name}: Found {len(types)} total types")
                filtered_count = len([t for t in types if t and str(t).strip()])
                print(f"    Valid types: {filtered_count}")
                
            except Exception as e:
                print(f"⚠️ Collection {collection_name}에서 types 가져오기 실패: {str(e)}")
        
        unique_types_list = list(unique_types)
        print(f"✅ Total unique types found: {len(unique_types_list)}")
        print(f"📝 Types: {sorted(unique_types_list)}")
        
        return unique_types_list
    def _is_korean_type(self, type_str: str) -> bool:
        """⭐ REMOVED - 모든 types kabul edilir artık"""
        # Artık tüm types kabul ediliyor, filtreleme yok
        return True

    def update_bkt_with_answer(self, user_id: str, question_data: Dict, 
                              student_answer: int, is_correct: bool) -> Dict:
        """
        학생의 답변을 바탕으로 BKT 상태 업데이트 (Korean TYPE 기반)
        """
        # 현재 BKT 상태 가져오기
        bkt_state = self.get_user_bkt_state(user_id)
        
        # 문제 정보 추출 - TYPE이 가장 중요!
        difficulty = question_data.get("difficulty", "중")
        question_type = question_data.get("type", "general")
        
        # ⭐ SADECE BOŞ KONTROL - manuel filtreleme yok
        if not question_type or not str(question_type).strip():
            print(f"⚠️ Empty type, using 'general': {question_type}")
            question_type = "general"
        else:
            # type을 string으로 확실히 변환
            question_type = str(question_type).strip()
        
        print(f"🔍 BKT Update: user={user_id}, type={question_type}, difficulty={difficulty}, correct={is_correct}")
        
        # BKT 파라미터 가져오기
        params = self.difficulty_params[difficulty]
        
        # type이 없으면 새로 생성
        if question_type not in bkt_state["type_mastery"]:
            print(f"📝 Creating new type entry: {question_type}")
            bkt_state["type_mastery"][question_type] = {
                "mastery_probability": params["prior"],
                "total_attempts": 0,
                "correct_answers": 0,
                "last_updated": datetime.utcnow(),
                "difficulty_performance": {
                    "하": {"attempts": 0, "correct": 0, "mastery": 0.5},
                    "중": {"attempts": 0, "correct": 0, "mastery": 0.4},
                    "상": {"attempts": 0, "correct": 0, "mastery": 0.3}
                }
            }
        
        type_data = bkt_state["type_mastery"][question_type]
        current_mastery = type_data["mastery_probability"]
        
        # Bayesian 업데이트 수행
        updated_mastery = self._bayesian_update(current_mastery, is_correct, params)
        
        # type 데이터 업데이트
        type_data["mastery_probability"] = updated_mastery
        type_data["total_attempts"] += 1
        if is_correct:
            type_data["correct_answers"] += 1
        type_data["last_updated"] = datetime.utcnow()
        
        # 난이도별 성과 업데이트
        diff_perf = type_data["difficulty_performance"][difficulty]
        diff_perf["attempts"] += 1
        if is_correct:
            diff_perf["correct"] += 1
        
        # 해당 난이도에서의 mastery 업데이트
        diff_perf["mastery"] = updated_mastery
        
        # 전체 상태 업데이트
        bkt_state["total_attempts"] += 1
        if is_correct:
            bkt_state["total_correct"] += 1
        
        # 전체 mastery 재계산 (모든 type들의 가중평균)
        total_mastery = 0
        total_weight = 0
        
        for qtype, data in bkt_state["type_mastery"].items():
            # Tüm types dahil
            weight = max(1, data["total_attempts"])  # 최소 weight 1
            total_mastery += data["mastery_probability"] * weight
            total_weight += weight
        
        bkt_state["overall_mastery"] = total_mastery / total_weight if total_weight > 0 else 0.4
        bkt_state["updated_at"] = datetime.utcnow()
        
        # 데이터베이스에 저장
        self.bkt_collection.update_one(
            {"user_id": user_id},
            {"$set": bkt_state},
            upsert=True
        )
        
        print(f"✅ BKT Updated: {question_type} mastery {current_mastery:.3f} → {updated_mastery:.3f}")
        
        return {
            "type": question_type,
            "difficulty": difficulty,
            "previous_mastery": current_mastery,
            "updated_mastery": updated_mastery,
            "overall_mastery": bkt_state["overall_mastery"],
            "attempts_in_type": type_data["total_attempts"],
            "skipped": False
        }   

    def _bayesian_update(self, prior_mastery: float, is_correct: bool, 
                        params: Dict) -> float:
        """베이지안 업데이트 수행"""
        slip = params["slip"]      # P(wrong|known)
        guess = params["guess"]    # P(correct|unknown)
        learn = params["learn"]    # P(학습)
        
        P_mastery = prior_mastery
        
        if is_correct:
            # 맞췄을 때: P(known|correct)
            P_correct = P_mastery * (1 - slip) + (1 - P_mastery) * guess
            if P_correct > 0:
                P_mastery_updated = (P_mastery * (1 - slip)) / P_correct
            else:
                P_mastery_updated = P_mastery
        else:
            # 틀렸을 때: P(known|wrong)
            P_wrong = P_mastery * slip + (1 - P_mastery) * (1 - guess)
            if P_wrong > 0:
                P_mastery_updated = (P_mastery * slip) / P_wrong
            else:
                P_mastery_updated = P_mastery
        
        # 학습 효과 추가
        final_mastery = P_mastery_updated + (1 - P_mastery_updated) * learn
        
        # 0.01과 0.99 사이로 제한
        return max(0.01, min(0.99, final_mastery))

    def get_weak_types(self, user_id: str, threshold: float = 0.6) -> List[Dict]:
        """약한 type들 찾기 - sadece güvenilir olanlar"""
        bkt_state = self.get_user_bkt_state(user_id)
        
        weak_types = []
        for question_type, data in bkt_state["type_mastery"].items():
            attempts = data.get("total_attempts", 0)
            mastery = data.get("mastery_probability", 0)
            
            # ⭐ Sadece güvenilir attempts olan types
            if attempts >= self.reliability_settings["min_attempts_for_reliable"]:
                if mastery < threshold:
                    reliable_info = self.calculate_reliable_mastery(data)
                    
                    weak_types.append({
                        "type": question_type,
                        "mastery": mastery,
                        "attempts": attempts,
                        "accuracy": data.get("correct_answers", 0) / attempts if attempts > 0 else 0,
                        "confidence_level": reliable_info["confidence_level"],
                        "status": reliable_info["status"]
                    })
        
        # Mastery'e göre sırala (en zayıf önce)
        weak_types.sort(key=lambda x: x["mastery"])
        return weak_types

    def get_adaptive_questions_by_type(self, user_id: str, num_questions: int = 10) -> List[Dict]:
        """type별 약점을 기반으로 적응형 문제 추천"""
        weak_types = self.get_weak_types(user_id)
        
        if not weak_types:
            # 약한 type이 없으면 전체적으로 균등하게
            return self._get_balanced_questions(num_questions)
        
        print(f"🎯 Weak types for {user_id}: {[t['type'] for t in weak_types[:3]]}")
        
        recommended_questions = []
        collections = ["diagnosis_test", "exam_questions"]
        
        # 가장 약한 type들에 집중
        for type_info in weak_types[:3]:  # 상위 3개 약한 type
            question_type = type_info["type"]
            mastery = type_info["mastery"]
            
            # 습득도에 따른 난이도 결정
            if mastery < 0.3:
                target_difficulty = "하"  # 기초 다지기
            elif mastery < 0.5:
                target_difficulty = "중"  # 실력 향상
            else:
                target_difficulty = "상"  # 완성도 높이기
            
            # 해당 type과 난이도의 문제 찾기
            questions_found = 0
            for collection_name in collections:
                if questions_found >= 3:  # type당 최대 3문제
                    break
                    
                collection = self.db[collection_name]
                
                # type과 difficulty로 검색
                query = {
                    "type": question_type,
                    "difficulty": target_difficulty
                }
                
                questions = list(collection.find(query).limit(3))
                
                for question in questions:
                    if len(recommended_questions) < num_questions:
                        question_meta = {
                            "question_id": str(question.get("_id")),
                            "type": question_type,
                            "difficulty": target_difficulty,
                            "current_mastery": mastery,
                            "reason": f"약한 유형 ({question_type}) 개선"
                        }
                        
                        recommended_questions.append(question_meta)
                        questions_found += 1
        
        return recommended_questions[:num_questions]

    def _get_balanced_questions(self, num_questions: int) -> List[Dict]:
        """균등한 문제 분배"""
        questions = []
        collections = ["diagnosis_test", "exam_questions"]
        
        for collection_name in collections:
            collection = self.db[collection_name]
            random_questions = list(collection.aggregate([{"$sample": {"size": num_questions}}]))
            
            for q in random_questions:
                if len(questions) < num_questions:
                    questions.append({
                        "question_id": str(q.get("_id")),
                        "type": q.get("type", "general"),
                        "difficulty": q.get("difficulty", "중"),
                        "current_mastery": 0.5,
                        "reason": "균등 분배"
                    })
        
        return questions

    def get_mastery_report(self, user_id: str) -> Dict:
        """상세 습득도 리포트 생성 (güvenilirlik bilgisi ile)"""
        bkt_state = self.get_user_bkt_state(user_id)
        
        # type별 분석 - ⭐ güvenilirlik dahil
        type_analysis = {}
        reliable_types = {}  # Sadece güvenilir olanlar
        
        for question_type, data in bkt_state["type_mastery"].items():
            attempts = data.get("total_attempts", 0)
            
            # Sadece test edilmiş types dahil et
            if attempts > 0:
                reliable_info = self.calculate_reliable_mastery(data)
                
                # Ana analiz
                type_analysis[question_type] = {
                    **reliable_info,
                    "last_updated": data.get("last_updated"),
                    "difficulty_performance": data.get("difficulty_performance", {}),
                    "accuracy": data.get("correct_answers", 0) / attempts if attempts > 0 else 0
                }
                
                # Güvenilir olanları ayrı tut
                if reliable_info["is_reliable"]:
                    reliable_types[question_type] = type_analysis[question_type]
        
        # Genel istatistikler
        total_attempts = bkt_state.get("total_attempts", 0)
        total_correct = bkt_state.get("total_correct", 0)
        overall_accuracy = total_correct / total_attempts if total_attempts > 0 else 0
        
        # ⭐ Overall mastery hesaplama - sadece güvenilir types
        if reliable_types:
            total_mastery = 0
            total_weight = 0
            
            for qtype, data in reliable_types.items():
                weight = max(1, data["attempts"])
                total_mastery += data["mastery_probability"] * weight
                total_weight += weight
            
            overall_mastery = total_mastery / total_weight if total_weight > 0 else 0.3
        else:
            overall_mastery = bkt_state.get("overall_mastery", 0.3)
        
        # Güçlü ve zayıf alanlar - sadece güvenilir types
        strong_types = []
        weak_types = []
        
        for qtype, data in reliable_types.items():
            mastery = data["mastery_probability"]
            if mastery >= 0.7:
                strong_types.append((qtype, data))
            elif mastery < 0.5:
                weak_types.append((qtype, data))
        
        strong_types.sort(key=lambda x: x[1]["mastery_probability"], reverse=True)
        weak_types.sort(key=lambda x: x[1]["mastery_probability"])
        
        # Güvenilirlik uyarıları
        unreliable_count = len([t for t in type_analysis.values() if not t["is_reliable"]])
        total_tested_types = len(type_analysis)
        
        return {
            "user_id": user_id,
            "overall_mastery": overall_mastery,
            "overall_accuracy": overall_accuracy,
            "total_attempts": total_attempts,
            "total_correct": total_correct,
            "type_analysis": type_analysis,  # Tüm test edilmiş types
            "reliable_types": reliable_types,  # Sadece güvenilir olanlar
            "strong_types": strong_types[:5],
            "weak_types": weak_types[:5],
            "total_types_tracked": total_tested_types,
            "reliable_types_count": len(reliable_types),
            "unreliable_types_count": unreliable_count,
            "last_updated": bkt_state.get("updated_at"),
            "reliability_summary": {
                "total_tested": total_tested_types,
                "reliable": len(reliable_types),
                "needs_more_practice": unreliable_count,
                "reliability_percentage": len(reliable_types) / total_tested_types * 100 if total_tested_types > 0 else 0
            }
        }

    def get_type_summary(self, user_id: str) -> Dict:
        """간단한 type별 요약"""
        bkt_state = self.get_user_bkt_state(user_id)
        
        summary = {
            "total_types": 0,
            "mastered_types": 0,
            "learning_types": 0,
            "weak_types": 0,
            "overall_mastery": bkt_state["overall_mastery"]
        }
        
        for question_type, data in bkt_state["type_mastery"].items():
            if data["total_attempts"] > 0:  # 실제로 시도한 type만
                summary["total_types"] += 1
                mastery = data["mastery_probability"]
                
                if mastery >= 0.7:
                    summary["mastered_types"] += 1
                elif mastery >= 0.45:
                    summary["learning_types"] += 1
                else:
                    summary["weak_types"] += 1
        
        return summary