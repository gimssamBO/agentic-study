# 가장 단순한 LLM 호출 한 번
from google import genai

client = genai.Client(api_key="")   # Gemini 클라이언트 생성

def ask(question: str) -> str:
    # generate_content = "한 번 묻고 → 한 번 답받기"의 가장 기본 호출
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=question,
    )
    return resp.text   # 모델이 생성한 답변(문자열)

# 질문 1: 일반 지식 → LLM이 잘 답함
print(ask("블루투스 이어버드를 고를 때 무엇을 봐야 하나요? 3가지만 짧게."))

# 질문 2: 실시간 사내 정보 → LLM 혼자서는 불가
print(ask("승승장구몰 주문번호 O000123은 지금 배송 어디까지 왔나요?"))