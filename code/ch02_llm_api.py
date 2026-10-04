# Openai 용
import os, sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL

client = get_openai_client()

def chat(system: str, user: str, temperature: float = 0.3) -> str:
    """시스템 지시(system)와 사용자 입력(user)을 받아 답변 텍스트를 돌려준다.
    핵심은 메시지 구성과 파라미터 두 가지다.
      - role 'system': 모델의 '역할·말투'를 지정.
      - temperature: 생성의 무작위성(0=일관, 높을수록 다양).
    """
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content

# 시스템 지시 없이 가장 단순하게 호출. temperature=0.7 로 다양한 홍보 문구를 유도.
resp = client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=[{"role": "user", "content": "승승장구몰을 한 문장으로 홍보해줘."}],
    temperature=0.7,
)

print("답변:", resp.choices[0].message.content)
# usage = 이번 호출에 쓴 토큰 수(prompt/응답/합계). 토큰이 곧 과금 기준이다.
print("토큰:", resp.usage)

# 같은 질문(q)이라도 system 역할 지시만 바꾸면 말투·페르소나가 통째로 바뀐다.
q = "환불 얼마나 걸려요?"

print("\n[친절한 상담원]")
print(chat("너는 승승장구몰의 친절한 CS 상담원이다. 존댓말로 간결히 답하라.", q))

print("\n[무뚝뚝한 엔지니어]")
print(chat("너는 무뚝뚝한 엔지니어다. 핵심만 한 줄로 답하라.", q))


# # 제미나이 용
# # 실행: python code/ch02_llm_api.py
# import os, sys, pathlib
# sys.path.append(str(pathlib.Path(__file__).resolve().parent))
# from common import get_genai_client, GEMINI_MODEL

# from google.genai import types

# client = get_genai_client()

# def chat(system: str, user: str, temperature: float = 0.3) -> str:
#     """시스템 지시(system)와 사용자 입력(user)을 받아 답변 텍스트를 돌려준다.

#     핵심은 config 안의 두 가지다.
#       - system_instruction: 모델의 '역할·말투'를 지정.
#       - temperature: 생성의 무작위성(0=일관, 높을수록 다양).
#     """
#     resp = client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=user,
#         config=types.GenerateContentConfig(
#             system_instruction=system, temperature=temperature),
#     )
#     return resp.text

# # 시스템 지시 없이 가장 단순하게 호출. temperature=0.7 로 다양한 홍보 문구를 유도.
# resp = client.models.generate_content(
#     model=GEMINI_MODEL,
#     contents="승승장구몰을 한 문장으로 홍보해줘.",
#     config=types.GenerateContentConfig(temperature=0.7),
# )

# print("답변:", resp.text)
# # usage_metadata = 이번 호출에 쓴 토큰 수(prompt/응답/합계). 토큰이 곧 과금 기준이다.
# print("토큰:", resp.usage_metadata)


# # 같은 질문(q)이라도 system_instruction 만 바꾸면 말투·페르소나가 통째로 바뀐다.
# q = "환불 얼마나 걸려요?"

# print("\n[친절한 상담원]")
# print(chat("너는 승승장구몰의 친절한 CS 상담원이다. 존댓말로 간결히 답하라.", q))

# print("\n[무뚝뚝한 엔지니어]")
# print(chat("너는 무뚝뚝한 엔지니어다. 핵심만 한 줄로 답하라.", q))
