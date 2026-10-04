""" # 가장 단순한 LLM 호출 한 번 (Gemini 기준)
from common import GEMINI_MODEL, get_genai_client

client = get_genai_client()   # .env 의 GOOGLE_API_KEY 로 Gemini 클라이언트 생성

def ask(question: str) -> str:
    # generate_content = "한 번 묻고 → 한 번 답받기"의 가장 기본 호출
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
    )
    return resp.text   # 모델이 생성한 답변(문자열)

# 질문 1: 일반 지식 → LLM이 잘 답함
print(ask("블루투스 이어버드를 고를 때 무엇을 봐야 하나요? 3가지만 짧게."))

# 질문 2: 실시간 사내 정보 → LLM 혼자서는 불가
print(ask("승승장구몰 주문번호 O000123은 지금 배송 어디까지 왔나요?")) """



# -*- coding: utf-8 -*-
# 가장 단순한 LLM 호출 한 번 (OpenAI 기준)
from common import OPENAI_MODEL, get_openai_client

client = get_openai_client()  # .env 의 OPENAI_API_KEY 로 OpenAI 클라이언트 생성

def ask(question: str) -> str:
    # client.chat.completions.create = OpenAI의 기본 "단발성 질의" 호출
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": question}
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content  # 모델이 생성한 답변 텍스트

if __name__ == "__main__":
    # 질문 1: 일반 지식 → LLM이 잘 답함
    print("[질문 1] 일반 지식")
    print(ask("블루투스 이어버드를 고를 때 무엇을 봐야 하나요? 3가지만 짧게."))
    print("-" * 50)

    # 질문 2: 실시간 사내 정보 → LLM 혼자서는 확인 불가 (환각 또는 거절)
    print("[질문 2] 사내 정보 (도구 없음)")
    print(ask("승승장구몰 주문번호 O000123은 지금 배송 어디까지 왔나요?"))