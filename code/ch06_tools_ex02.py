import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL, DATA
import pandas as pd

client = get_openai_client()
products = pd.read_csv(DATA / "products.csv")

def make_get_price(doc: str):
    """독스트링(description)만 다른 get_price 도구 스키마 딕셔너리를 반환한다."""
    return {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": doc,
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "가격을 조회할 상품명",
                    },
                },
                "required": ["product_name"],
            },
        },
    }

# get_stock 스키마 정의
STOCK_TOOL = {
    "type": "function",
    "function": {
        "name": "get_stock",
        "description": "상품명을 받아 현재 재고 수량과 창고를 반환한다. 재고/품절 질문에 사용.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "재고를 조회할 상품명",
                },
            },
            "required": ["product_name"],
        },
    },
}

def which_tool(question: str, tools: list):
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": question}],
        tools=tools,
        temperature=0,
    )
    calls = resp.choices[0].message.tool_calls or []
    picked = calls[0].function.name if calls else "(도구 미선택)"
    print(f"  → 모델 선택: {picked}")

# 64번째 줄 테스트 영역
good_price = make_get_price("상품명을 받아 판매가(원)를 반환한다. 가격/얼마 질문에 사용.")
poor_price = make_get_price("가격.")

print("[자세한 독스트링]")
which_tool("슬림핏 청바지 얼마야?", [good_price, STOCK_TOOL])

print("[망가진 독스트링]")
which_tool("슬림핏 청바지 얼마야?", [poor_price, STOCK_TOOL])