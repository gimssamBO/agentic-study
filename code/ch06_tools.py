# 실행: python code/ch06_tools.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL, DATA
import pandas as pd
import json

client = get_openai_client()
products  = pd.read_csv(DATA / "products.csv")    # 가격·카테고리
inventory = pd.read_csv(DATA / "inventory.csv")   # 재고·창고
orders    = pd.read_csv(DATA / "orders.csv")      # 주문·상태

def get_price(product_name: str) -> str:
    """상품명(일부만 입력해도 됨)을 받아 판매가(원)를 반환한다. 가격/얼마 질문에 사용."""
    row = products[products["product_name"].str.contains(product_name, na=False)]
    if row.empty:
        return f"'{product_name}' 가격 정보를 찾지 못했습니다."
    r = row.iloc[0]
    return f"{r['product_name']} 판매가 {int(r['price']):,}원"

def get_stock(product_name: str) -> str:
    """상품명(일부만 입력해도 됨)을 받아 현재 재고 수량과 창고를 반환한다. 재고/품절 질문에 사용."""
    row = inventory[inventory["product_name"].str.contains(product_name, na=False)]
    if row.empty:
        return f"'{product_name}' 재고 정보를 찾지 못했습니다."
    r = row.iloc[0]
    return f"{r['product_name']} 재고 {int(r['stock'])}개 ({r['warehouse']})"

def get_order_status(order_id: str) -> str:
    """주문번호(예: O000106)를 받아 배송 상태를 반환한다. 주문/배송 추적에 사용."""
    row = orders[orders["order_id"] == order_id]
    if row.empty:
        return f"주문번호 {order_id}를 찾지 못했습니다."
    r = row.iloc[0]
    return f"주문 {order_id}: {r['product_name']} {int(r['quantity'])}개, 상태={r['status']}"

def search_product(keyword: str) -> str:
    """카테고리나 키워드로 상품을 검색해 이름 목록을 반환한다. '어떤 상품 있어?' 류에 사용."""
    hit = products[products["product_name"].str.contains(keyword, na=False) |
                   products["category"].str.contains(keyword, na=False)]
    if hit.empty:
        return f"'{keyword}' 관련 상품이 없습니다."
    return "검색 결과: " + ", ".join(hit["product_name"].head(5).tolist())


# 함수 매핑 딕셔너리
TOOL_MAP = {
    "get_price": get_price,
    "get_stock": get_stock,
    "get_order_status": get_order_status,
    "search_product": search_product,
}

# OpenAI Tool 규격 스키마
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "상품명(일부만 입력해도 됨)을 받아 판매가(원)를 반환한다. 가격/얼마 질문에 사용.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock",
            "description": "상품명(일부만 입력해도 됨)을 받아 현재 재고 수량과 창고를 반환한다. 재고/품절 질문에 사용.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "주문번호(예: O000106)를 받아 배송 상태를 반환한다. 주문/배송 추적에 사용.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "조회할 주문번호 (예: O000106)",
                    },
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
                    "keyword": {
                        "type": "string",
                        "description": "검색할 카테고리명 또는 상품 키워드",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
]

def ask(question: str) -> str:
    """질문을 받아 모델이 알맞은 도구를 골라 실행하고, 최종 답변을 돌려준다."""
    messages = [{"role": "user", "content": question}]

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        tools=TOOLS,
        temperature=0,
    )
    msg = resp.choices[0].message

    # 도구 호출이 필요 없으면 바로 답변 반환
    if not msg.tool_calls:
        return msg.content

    # 도구 호출이 있는 경우 실행 후 피드백
    messages.append(msg)
    for tc in msg.tool_calls:
        func = TOOL_MAP.get(tc.function.name)
        args = json.loads(tc.function.arguments)
        result = func(**args) if func else f"도구 {tc.function.name} 없음"
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "name": tc.function.name,
            "content": json.dumps({"result": result}),
        })

    followup = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0,
    )
    return followup.choices[0].message.content

questions = [
    "슬림핏 청바지 얼마야?",            # → get_price 기대
    "이어버드 재고 있어?",             # → get_stock 기대
    "주문 O000106 배송 어디까지 왔어?", # → get_order_status 기대
    "패션의류 쪽에 어떤 상품들 있어?",  # → search_product 기대
]
for q in questions:
    print("Q:", q)
    print("A:", ask(q))
    print("-" * 50)

# # 실행: python code/ch06_tools.py
# import sys, pathlib
# sys.path.append(str(pathlib.Path(__file__).resolve().parent))
# from common import get_genai_client, GEMINI_MODEL, DATA
# from google.genai import types
# import pandas as pd

# client = get_genai_client()
# products  = pd.read_csv(DATA / "products.csv")    # 가격·카테고리
# inventory = pd.read_csv(DATA / "inventory.csv")   # 재고·창고
# orders    = pd.read_csv(DATA / "orders.csv")      # 주문·상태


# def get_price(product_name: str) -> str:
#     """상품명(일부만 입력해도 됨)을 받아 판매가(원)를 반환한다. 가격/얼마 질문에 사용."""
#     row = products[products["product_name"].str.contains(product_name, na=False)]
#     if row.empty:
#         return f"'{product_name}' 가격 정보를 찾지 못했습니다."
#     r = row.iloc[0]
#     return f"{r['product_name']} 판매가 {int(r['price']):,}원"

# def get_stock(product_name: str) -> str:
#     """상품명(일부만 입력해도 됨)을 받아 현재 재고 수량과 창고를 반환한다. 재고/품절 질문에 사용."""
#     row = inventory[inventory["product_name"].str.contains(product_name, na=False)]
#     if row.empty:
#         return f"'{product_name}' 재고 정보를 찾지 못했습니다."
#     r = row.iloc[0]
#     return f"{r['product_name']} 재고 {int(r['stock'])}개 ({r['warehouse']})"

# def get_order_status(order_id: str) -> str:
#     """주문번호(예: O000106)를 받아 배송 상태를 반환한다. 주문/배송 추적에 사용."""
#     row = orders[orders["order_id"] == order_id]
#     if row.empty:
#         return f"주문번호 {order_id}를 찾지 못했습니다."
#     r = row.iloc[0]
#     return f"주문 {order_id}: {r['product_name']} {int(r['quantity'])}개, 상태={r['status']}"

# def search_product(keyword: str) -> str:
#     """카테고리나 키워드로 상품을 검색해 이름 목록을 반환한다. '어떤 상품 있어?' 류에 사용."""
#     hit = products[products["product_name"].str.contains(keyword, na=False) |
#                    products["category"].str.contains(keyword, na=False)]
#     if hit.empty:
#         return f"'{keyword}' 관련 상품이 없습니다."
#     return "검색 결과: " + ", ".join(hit["product_name"].head(5).tolist())


# # 도구 4개를 한 리스트로 묶어 모델에 한꺼번에 등록
# TOOLS = [get_price, get_stock, get_order_status, search_product]

# def ask(question: str) -> str:
#     """질문을 받아 모델이 알맞은 도구를 골라 실행하고(자동), 최종 답변을 돌려준다."""
#     resp = client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=question,
#         config=types.GenerateContentConfig(tools=TOOLS, temperature=0),
#     )
#     return resp.text

# questions = [
#     "슬림핏 청바지 얼마야?",            # → get_price 기대
#     "이어버드 재고 있어?",             # → get_stock 기대
#     "주문 O000106 배송 어디까지 왔어?", # → get_order_status 기대
#     "패션의류 쪽에 어떤 상품들 있어?",  # → search_product 기대
# ]
# for q in questions:
#     print("Q:", q)
#     print("A:", ask(q))
#     print("-" * 50)