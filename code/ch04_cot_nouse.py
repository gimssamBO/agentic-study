from common import get_openai_client, OPENAI_MODEL

client = get_openai_client()

def ask_direct(question: str):
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": f"{question}\n설명 없이 정답만 한 단어로 답하라."}
        ],
        temperature=0,
    )
    return resp.choices[0].message.content.strip(), resp.usage.total_tokens

def ask_cot(question: str):
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": f"{question}\n단계적으로 풀어라. 마지막 줄에 '정답: <값>'."}
        ],
        temperature=0,
    )
    return resp.choices[0].message.content.strip(), resp.usage.total_tokens

d_txt, d_tok = ask_direct("대한민국의 수도는 어디인가?")
c_txt, c_tok = ask_cot("대한민국의 수도는 어디인가?")
print(f"직접: {d_txt} (토큰 {d_tok})")
print(f"CoT : 토큰 {c_tok}  ← 같은 정답인데 토큰만 더 씀")

# # Gemini
# from common import get_genai_client, GEMINI_MODEL
# from google.genai import types

# client = get_genai_client()

# def ask_direct(question: str):
#     resp = client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=f"{question}\n설명 없이 정답만 한 단어로 답하라.",
#         config=types.GenerateContentConfig(temperature=0),
#     )
#     return resp.text.strip(), resp.usage_metadata.total_token_count

# def ask_cot(question: str):
#     resp = client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=f"{question}\n단계적으로 풀어라. 마지막 줄에 '정답: <값>'.",
#         config=types.GenerateContentConfig(temperature=0),
#     )
#     return resp.text.strip(), resp.usage_metadata.total_token_count

# d_txt, d_tok = ask_direct("대한민국의 수도는 어디인가?")
# c_txt, c_tok = ask_cot("대한민국의 수도는 어디인가?")
# print(f"직접: {d_txt} (토큰 {d_tok})")
# print(f"CoT : 토큰 {c_tok}  ← 같은 정답인데 토큰만 더 씀")