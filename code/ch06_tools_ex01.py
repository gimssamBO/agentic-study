import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL
import json

client = get_openai_client()

# OpenAI 도구 스키마 정의
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "상품명(일부만 입력해도 됨)을 받아 판매가(원)를 반환한다. 가격/얼마 질문에 사용.",
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
            "description": "상품명(일부만 입력해도 됨)을 받아 현재 재고 수량과 창고를 반환한다. 재고/품절 질문에 사용.",
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
            "name": "get_order_status",
            "description": "주문번호(예: O000106)를 받아 배송 상태를 반환한다. 주문/배송 추적에 사용.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "조회할 주문번호 (예: O000106)"},
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": "카테고리나 키워드로 상품을 검색해 이름 목록을 반환한다. '어떤 상품 있어?' 류에 사용.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "검색할 카테고리명 또는 상품 키워드"},
                },
                "required": ["keyword"],
            },
        },
    },
]

def which_tool(question: str):
    """모델이 '어떤 도구를 고를지(tool_calls)'만 출력한다."""
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": question}],
        tools=TOOLS,
        temperature=0,
    )
    calls = resp.choices[0].message.tool_calls or []
    if not calls:
        print(f"  '{question}' → (도구 미선택)")
        return

    for tc in calls:
        args = json.loads(tc.function.arguments)
        print(f"  '{question}' → {tc.function.name}({args})")

which_tool("슬림핏 청바지 얼마야?")
which_tool("이어버드 재고 있어?")