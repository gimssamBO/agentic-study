# Openai
from common import get_openai_client, OPENAI_MODEL

client = get_openai_client()

def count_tokens(text: str):
    """문장 하나를 보내 입력/출력/합계 토큰을 돌려준다."""
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": text}],
        temperature=0,
    )
    u = resp.usage
    return u.prompt_tokens, u.completion_tokens, u.total_tokens

pairs = {
    "한국어": "승승장구몰의 무선 블루투스 이어버드를 한 문장으로 친절하게 홍보해줘.",
    "영어":   "Write one friendly sentence promoting SeungSeung Mall's wireless earbuds.",
}

for lang, text in pairs.items():
    in_tok, out_tok, total = count_tokens(text)
    print(f"[{lang}] 입력={in_tok} / 출력={out_tok} / 합계={total}")


# # 제미나이
# from common import get_genai_client, GEMINI_MODEL
# from google.genai import types

# client = get_genai_client()

# def count_tokens(text: str):
#     """문장 하나를 보내 입력/출력/합계 토큰을 돌려준다."""
#     resp = client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=text,
#         config=types.GenerateContentConfig(temperature=0),
#     )
#     u = resp.usage_metadata
#     return u.prompt_token_count, u.candidates_token_count, u.total_token_count

# pairs = {
#     "한국어": "승승장구몰의 무선 블루투스 이어버드를 한 문장으로 친절하게 홍보해줘.",
#     "영어":   "Write one friendly sentence promoting SeungSeung Mall's wireless earbuds.",
# }

# for lang, text in pairs.items():
#     in_tok, out_tok, total = count_tokens(text)
#     print(f"[{lang}] 입력={in_tok} / 출력={out_tok} / 합계={total}")