import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_genai_client, GEMINI_MODEL
client = get_genai_client()

# 실습 문제1.types 추가
from google.genai import types

def ask(question: str) -> str:
    # 문제1. 퍼소나 추가
    resp = client.models.generate_content(model=GEMINI_MODEL, contents=question, 
                                          # system_instruction = 모델에게 부여하는 '역할/규칙'
                                          config = types.GenerateContentConfig(system_instruction="한 문장으로만 답하는 무뚝뚝한 엔지니어"))
    return resp.text

if __name__ == "__main__":
    # ----- 질문 1: 일반 지식 (LLM이 답할 수 있음) -----
    print("=" * 60)
    print("질문 1 (일반 지식 — LLM이 답할 수 있음)")
    q1 = "블루투스 이어버드를 고를 때 무엇을 봐야 하나요? 3가지만 짧게."
    print("Q:", q1)
    print("A:", ask(q1))

    # ----- 질문 2: 실시간 사내 정보 (LLM 혼자서는 불가) -----
    print("=" * 60)
    print("질문 2 (실시간 사내 정보 — LLM 혼자서는 불가)")
    q2 = "승승장구몰 주문번호 O000123은 지금 배송 어디까지 왔나요?"
    print("Q:", q2)
    print("A:", ask(q2))
    print("=" * 60)
    print("관찰: 질문 2는 '주문 조회 도구'가 있어야만 정확히 답할 수 있습니다 (→ 5강).")