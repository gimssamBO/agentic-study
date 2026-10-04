# 실행: python code/ch01_intro.py
import sys, pathlib

# [왜 필요한가] 이 스크립트는 같은 폴더(code/)의 common.py 를 import 한다.
#   파이썬은 '실행 위치'에 따라 import 가 실패할 수 있으므로,
#   이 파일이 있는 폴더(code/)를 모듈 검색 경로에 강제로 추가한다.
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# common.py 의 도우미를 가져온다(모든 강 공통 사용).
#  - get_openai_client: .env 의 OPENAI_API_KEY 로 OpenAI 클라이언트를 만들어 주는 함수
#  - OPENAI_MODEL: 사용할 모델 이름(기본 "gpt-4o-mini")
from common import get_openai_client, OPENAI_MODEL

# 클라이언트 생성. 이 객체로 모델에 요청을 보낸다.
client = get_openai_client()

# 질문 문자열을 받아 LLM의 답변 텍스트를 돌려주는 가장 단순한 함수.
def ask(question: str) -> str:
    """
    chat.completions.create: '한 번 요청 → 한 번 응답'의 가장 기본적인 LLM 호출.
      - model: 어떤 모델을 쓸지 (gpt-4o-mini 등)
      - messages: 보낼 대화 내역(역할과 내용)
    resp.choices[0].message.content: 모델이 생성한 답변(문자열).
    """
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": question}
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content


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


# # 실행: python code/ch01_intro.py => 제미나이용
# import sys, pathlib

# # [왜 필요한가] 이 스크립트는 같은 폴더(code/)의 common.py 를 import 한다.
# #   파이썬은 '실행 위치'에 따라 import 가 실패할 수 있으므로,
# #   이 파일이 있는 폴더(code/)를 모듈 검색 경로에 강제로 추가한다.
# sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# # common.py 의 도우미를 가져온다(모든 강이 공통 사용).
# #  - get_genai_client: .env 의 API 키로 Gemini 클라이언트를 만들어 주는 함수
# #  - GEMINI_MODEL: 사용할 모델 이름(기본 "gemini-2.5-flash = 지금은 무료에선 지원안해서 3.5 써야함")
# from common import get_genai_client, GEMINI_MODEL

# # 클라이언트 생성. 이 객체로 모델에 요청을 보낸다.
# client = get_genai_client()

# # 질문 문자열을 받아 LLM의 답변 텍스트를 돌려주는 가장 단순한 함수.
# def ask(question: str) -> str:
#     """
#     generate_content: '한 번 요청 → 한 번 응답'의 가장 기본적인 LLM 호출.
#       - model:    어떤 모델을 쓸지
#       - contents: 보낼 내용(여기선 질문)
#     resp.text: 모델이 생성한 답변(문자열).
#     """
#     resp = client.models.generate_content(model=GEMINI_MODEL, contents=question)
#     return resp.text


# if __name__ == "__main__":
#     # ----- 질문 1: 일반 지식 (LLM이 답할 수 있음) -----
#     print("=" * 60)
#     print("질문 1 (일반 지식 — LLM이 답할 수 있음)")
#     q1 = "블루투스 이어버드를 고를 때 무엇을 봐야 하나요? 3가지만 짧게."
#     print("Q:", q1)
#     print("A:", ask(q1))

#     # ----- 질문 2: 실시간 사내 정보 (LLM 혼자서는 불가) -----
#     print("=" * 60)
#     print("질문 2 (실시간 사내 정보 — LLM 혼자서는 불가)")
#     q2 = "승승장구몰 주문번호 O000123은 지금 배송 어디까지 왔나요?"
#     print("Q:", q2)
#     print("A:", ask(q2))
#     print("=" * 60)
#     print("관찰: 질문 2는 '주문 조회 도구'가 있어야만 정확히 답할 수 있습니다 (→ 5강).")

