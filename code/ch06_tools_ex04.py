import sys, pathlib
from collections import Counter
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL

client = get_openai_client()

# 동일한 역할을 하는 두 도구 스키마 정의
get_price_schema = {
    "type": "function",
    "function": {
        "name": "get_price",
        "description": "상품명을 받아 판매가(원)를 반환한다. 가격/얼마 질문에 사용.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "조회할 상품명"},
            },
            "required": ["product_name"],
        },
    },
}

lookup_amount_schema = {
    "type": "function",
    "function": {
        "name": "lookup_amount",
        "description": "상품의 금액을 조회한다. 가격을 알려준다.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "조회할 상품명"},
            },
            "required": ["product_name"],
        },
    },
}

def pick(tools, q="슬림핏 청바지 얼마야?"):
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": q}],
        tools=tools,
        temperature=0,
    )
    calls = resp.choices[0].message.tool_calls or []
    return calls[0].function.name if calls else "(없음)"

# (1) 중복 도구 둘 다 등록 → 5번 집계
print("[중복 있음]")
picks = [pick([get_price_schema, lookup_amount_schema]) for _ in range(5)]
print(Counter(picks))

# (2) 중복 제거 → 5번 집계
print("[중복 제거]")
picks2 = [pick([get_price_schema]) for _ in range(5)]
print(Counter(picks2))