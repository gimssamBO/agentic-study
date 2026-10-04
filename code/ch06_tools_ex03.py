import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL
import json

client = get_openai_client()

# OpenAI Tool 규격 스키마 (기존 get_price, get_stock 포함)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "상품명을 받아 판매가(원)를 반환한다. 가격/얼마 질문에 사용.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "가격을 조회할 상품명"},
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock",
            "description": "상품명을 받아 현재 재고 수량과 창고를 반환한다. 재고/품절 질문에 사용.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "재고를 조회할 상품명"},
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_review_summary",
            "description": "상품명을 받아 고객 평점 평균과 리뷰 개수를 반환한다. 상품의 평점/후기 평가 질문에 사용.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "리뷰를 조회할 상품명"},
                },
                "required": ["product_name"],
            },
        },
    },
]

def which_tool(q: str):
    r = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": q}],
        tools=TOOLS,
        temperature=0,
    )
    calls = r.choices[0].message.tool_calls or []
    if not calls:
        print(f"  '{q}' → (도구 미선택)")
        return
    for fc in calls:
        args = json.loads(fc.function.arguments)
        print(f"  '{q}' → {fc.function.name}({args})")

which_tool("후드티 평이 어때?")