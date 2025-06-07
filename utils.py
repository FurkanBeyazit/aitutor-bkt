import re
import json
from llama_cloud_services import LlamaParse
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import os
load_dotenv()
openai_api_key = os.getenv("openai_api_key")

def parse_questions_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Parsing pdf questions with LlamaParse and returning structured JSON
    """
    parser = LlamaParse(
        api_key="llx-Wc0S4RgbjeszJCO442tTyczADaD2HDhCmKfJ6RXrjkxbTlkP",
        num_workers=4,
        verbose=True,
        language="ko",
        parse_mode="parse_page_with_lvm",
        gpt4o_api_key=openai_api_key,
        system_prompt='Keep the numbers and format of the document. The document is a multiple choice question with 5 choices. The choices are in the format of ①, ②, ③, ④, ⑤. Please extract the question and choices from the document.'
    )
    
    result = parser.parse(file_path)
    content = result.get_markdown_nodes()[0].text
    
    # Temizleme işlemi
    clean_result = re.sub(r'^.*?(?=1\.)', '', content, flags=re.DOTALL)
    
    # Parse edilmiş soruları döndür
    return process_questions_with_global_id(clean_result, starting_id=1)

def parse_korean_medical_questions(text: str, id_offset: int = 0, global_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Questions in Korean medical exam format are parsed from a given text.
    """
    # Metni tek tek sorulara böl
    question_blocks = re.split(r'(?=\d+\.[\s\n])', text.strip())
    
    # Boş blokları kaldır
    question_blocks = [block for block in question_blocks if block.strip()]
    
    parsed_questions = []
    current_global_id = global_id if global_id is not None else None
    
    for block in question_blocks:
        # Soru ID'sini ve içeriğini çıkar
        match = re.match(r'(\d+)\.[\s\n]', block)
        if not match:
            continue
        
        local_problem_id = int(match.group(1))
        
        # Kullanılacak problem ID'sini belirle
        if current_global_id is not None:
            problem_id = current_global_id
            current_global_id += 1
            
        else:
            # Global problem ID'sini almak için offset uygula
            problem_id = local_problem_id + id_offset
        
        # ID kısmını bloktan kaldır
        content = block[match.end():]
        
        # İçeriği problem ve seçeneklere böl
        parts = re.split(r'(?=[①②③④⑤])', content)
        
        if len(parts) < 2:
            continue
        
        problem = parts[0].strip()
        choices = []
        
        # Seçenekleri çıkar
        for i in range(1, len(parts)):
            # Daire numarasını (①, ②, vb.) kaldır ve seçeneği al
            choice_text = re.sub(r'^[①②③④⑤]\s*', '', parts[i]).strip()
            choices.append(choice_text)
        
        # Yapılandırılmış soruyu oluştur
        question_data = {
            "problem_id": problem_id,
            "problem": problem,
            "choices": choices
        }
        
        parsed_questions.append(question_data)
    
    return parsed_questions

def process_questions_with_global_id(input_text: str, starting_id: int = 1) -> List[Dict[str, Any]]:
    """
    Fixing the question id (index number +1 for each question)
    """
    return parse_korean_medical_questions(input_text, global_id=starting_id)

def parse_answer_key_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Answer key PDF parsing with LlamaParse and returning structured JSON
    """
    parser = LlamaParse(
        api_key="llx-Wc0S4RgbjeszJCO442tTyczADaD2HDhCmKfJ6RXrjkxbTlkP",
        num_workers=4,
        verbose=True,
        language="ko",
        parse_mode="parse_page_with_lvm",
        gpt4o_api_key=openai_api_key,
        system_prompt='This is an answer sheet of multiple choice questions. There is a table with sessions, subjects, questionid, answers. Only parse the table'
    )
    
    result = parser.parse(file_path)
    content = result.get_markdown_nodes()[0].text
    
    # Temizleme işlemi
    clean_result = re.sub(r'^.*?(?=\|)', '', content, flags=re.DOTALL)
    print(clean_result)
    # JSON stringi parse et
    json_data = table_text_to_json(clean_result)
    return json.loads(json_data)


def table_text_to_json(table_text: str) -> str:
    """
    Table format to JSON conversion
    """
    # Metni satırlara böl
    lines = [line.strip() for line in table_text.split('\n') if line.strip()]
    
    # Ayırıcı satırı atla (tire içeren)
    data_lines = [line for line in lines if '----' not in line]
    
    # Başlık tanımlama
    header_keywords = ['교시', '과목', '문제번호', '가답안', '최종답안']
    
    # İlk satırdan başlıkları al
    headers = []
    if data_lines:
        header_line = data_lines[0]
        raw_headers = [h.strip() for h in header_line.split('|') if h.strip()]
        
        # Basit mapping - pozisyona göre
        # Tablodan görünen sıralama: | 교시 | 과목 | 문제번호 | 가답안 |
        if len(raw_headers) >= 4:
            headers = ['session', 'subject', 'problem_id', 'answer']
        else:
            # Fallback
            headers = ['session', 'subject', 'problem_id', 'answer'][:len(raw_headers)]
    
    # Veri satırlarını işle
    result = []
    for line in data_lines[1:]:  # İlk başlık satırını atla
        if '---' in line:
            continue
        
        values = [v.strip() for v in line.split('|') if v.strip()]
        
        # Başlık satırı kontrolü
        is_header_line = any(value in header_keywords for value in values)
        if is_header_line:
            continue
        
        # Veri satırı işle
        if len(values) >= 4:  # En az 4 sütun olmalı
            row_dict = {
                "session": values[0],           # 1. sütun: 교시
                "subject": values[1],           # 2. sütun: 과목  
                "problem_id": int(values[2]) if values[2].isdigit() else values[2],  # 3. sütun: 문제번호
                "answer": int(values[3]) if values[3].isdigit() else values[3]       # 4. sütun: 가답안
            }
            result.append(row_dict)
    
    return json.dumps(result, ensure_ascii=False, separators=(',', ':'))

def merge_questions_and_answers(questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merging questions and answers
    """
    merged_data = []
    
    # Cevapları sözlüğe dönüştür (problem_id => cevap kaydı)
    answer_dict = {str(ans['problem_id']): ans for ans in answers}
    
    for question in questions:
        # Bu soru için cevap var mı?
        problem_id = str(question['problem_id'])
        if problem_id in answer_dict:
            answer_record = answer_dict[problem_id]
            
            # Birleştirilmiş kayıt oluştur
            merged_record = {
                "problem_id": int(question['problem_id']),
                "problem": question['problem'],
                "choices": question['choices'],
                "answer_key": answer_record.get('answer', None),
                "session": answer_record.get('session', ''),
                "subject": answer_record.get('subject', '')
            }
            
            merged_data.append(merged_record)
    
    return merged_data
def merge_questions_and_answers_helper(questions: List[Dict], answers: List[Dict]) -> List[Dict]:
    """
    Soru ve cevapları birleştirir - Normalize edilmiş veriler için
    """
    merged_data = []
    
    # Cevapları sözlüğe dönüştür (problem_id => cevap kaydı)
    answer_dict = {str(ans['problem_id']): ans for ans in answers}
    
    for question in questions:
        # Bu soru için cevap var mı?
        problem_id = str(question['problem_id'])
        if problem_id in answer_dict:
            answer_record = answer_dict[problem_id]
            
            # Birleştirilmiş kayıt oluştur
            merged_record = {
                "problem_id": int(question['problem_id']),
                "problem": question['problem'],
                "choices": question['choices'],
                "answer_key": answer_record.get('answer', None),
                "session": answer_record.get('session', ''),
                "subject": answer_record.get('subject', '')
            }
            
            merged_data.append(merged_record)
    
    return merged_data
# SCORE CALCULATION
def real_calculate_score(student_answers, questions):
            print("Gerçek hesaplama fonksiyonu çalışıyor...")
            
            total_score = 0
            correct_count = 0
            results = []
            
            for question in questions:
                question_id = str(question.get("_id"))  # ObjectId'yi string'e dönüştür
                
                # Bu soru için yanıt var mı?
                if question_id not in student_answers:
                    print(f"Soru {question_id} için yanıt bulunamadı")
                    continue
                
                student_answer = student_answers[question_id]
                
                # Doğru cevabı al
                correct_answer = question.get("answer_key")
                
                print(f"Soru ID: {question_id}")
                print(f"Öğrenci yanıtı (API'den gelen): {student_answer}")
                print(f"Doğru cevap (veritabanında): {correct_answer}")
                
                if correct_answer is None:
                    print(f"UYARI: Soru {question_id} için doğru cevap bulunamadı")
                    continue
                
                # Veri türü dönüşümü
                if isinstance(student_answer, str) and student_answer.isdigit():
                    student_answer = int(student_answer)
                    
                if isinstance(correct_answer, str) and correct_answer.isdigit():
                    correct_answer = int(correct_answer)
                
                # Karşılaştırma yap - Artık frontend'den düzeltilmiş değerler geldiği için +1 eklemiyoruz
                is_correct = student_answer == correct_answer
                
                print(f"Cevap doğru mu? {is_correct} ({student_answer} == {correct_answer})")
                
                # Zorluk seviyesine göre puan hesapla
                points = 0
                if is_correct:
                    difficulty = question.get("difficulty", "하")
                    if difficulty == "상":
                        points = 5
                    elif difficulty == "중":
                        points = 3
                    else:  # "하"
                        points = 2
                    
                    correct_count += 1
                
                total_score += points
                
                # Sonuç bilgisini ekle
                results.append({
                    "question_id": question_id,
                    "correct": is_correct,
                    "points": points,
                    "correct_answer": correct_answer,
                    "student_answer": student_answer
                })
            
            # Öğrenci seviyesini belirle
            student_level = "하"  # Varsayılan seviye
            if total_score >= 80:
                student_level = "상"
            elif total_score >= 50:
                student_level = "중"
            
            print(f"Toplam skor: {total_score}, Doğru sayısı: {correct_count}")
            
            return {
                "score": total_score,
                "level": student_level,
                "correct_count": correct_count,
                "results": results
            }