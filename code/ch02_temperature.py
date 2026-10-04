# Openai
from common import get_openai_client, OPENAI_MODEL

client = get_openai_client()

def promote(temperature: float) -> str:
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": "승승장구몰을 한 문장으로 홍보해줘."}],
        temperature=temperature,
    )
    return resp.choices[0].message.content

# 온도 0: 여러 번 불러도 거의 같은 답
print("[temperature=0]")
for _ in range(3):
    print("-", promote(0.0))

# 온도 1.0: 부를 때마다 색다른 답
print("\n[temperature=1.0]")
for _ in range(3):
    print("-", promote(1.0))
    
    
# # 제미나이
# from common import get_genai_client, GEMINI_MODEL
# from google.genai import types

# client = get_genai_client()

# def promote(temperature: float) -> str:
#     resp = client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents="승승장구몰을 한 문장으로 홍보해줘.",
#         config=types.GenerateContentConfig(temperature=temperature),
#     )
#     return resp.text

# # 온도 0: 여러 번 불러도 거의 같은 답
# print("[temperature=0]")
# for _ in range(3):
#     print("-", promote(0.0))

# # 온도 1.0: 부를 때마다 색다른 답
# print("\n[temperature=1.0]")
# for _ in range(3):
#     print("-", promote(1.0))
    
    
    