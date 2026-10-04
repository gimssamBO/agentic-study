# OpenAI
# 실행: python code/ch05_function_calling.py
import sys, pathlib, json
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL, DATA
import pandas as pd

client = get_openai_client()
rates = pd.read_csv(DATA / "exchange_rates.csv")   # 환율 (currency, krw_per_unit)
inv = pd.read_csv(DATA / "inventory.csv")          # 재고 (product_name, stock, warehouse)

# 1. 로컬 파이썬 함수 정의
def get_exchange_rate(currency: str) -> str:
    row = rates[rates["currency"].str.upper() == currency.upper()]
    if row.empty:
        return f"{currency} 환율 정보가 없습니다."
    krw = float(row.iloc[0]["krw_per_unit"])
    return f"1 {currency.upper()} = {krw:,.2f} KRW"

def get_stock(product_name: str) -> str:
    row = inv[inv["product_name"].str.contains(product_name, na=False)]
    if row.empty:
        return f"'{product_name}' 재고 정보를 찾지 못했습니다."
    r = row.iloc[0]
    return f"{r['product_name']} 재고 {int(r['stock'])}개 ({r['warehouse']})"

print(get_stock("이어버드"))
print(get_exchange_rate("USD"))

# 2. OpenAI API용 Tool 스키마 정의
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "특정 외화(USD, EUR, JPY 등)의 환율을 조회하거나 가격 환산 시 호출. '달러'는 'USD' 등 표준 통화 코드로 변환 필요.",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "description": "환율을 조회할 3자리 통화 코드 (예: 'USD', 'EUR', 'JPY')",
                    }
                },
                "required": ["currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock",
            "description": "상품명(일부 키워드 가능)을 받아 현재 재고 수량과 보관 창고를 반환한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "조회할 상품명 키워드 (예: '이어버드')",
                    }
                },
                "required": ["product_name"],
            },
        },
    },
]

# 함수 이름 매핑용 딕셔너리
available_functions = {
    "get_exchange_rate": get_exchange_rate,
    "get_stock": get_stock,
}

# 3. 질문 및 도구 실행 루프
question = "이어버드 재고 있어? 그리고 가격을 달러로 환산하려면 환율이 얼마야?"
messages = [{"role": "user", "content": question}]

resp = client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=messages,
    tools=tools,
    tool_choice="auto",
    temperature=0,
)

response_message = resp.choices[0].message
messages.append(response_message)

# 모델이 도구 호출을 요구했을 경우 실행 후 최종 응답 생성
if response_message.tool_calls:
    for tool_call in response_message.tool_calls:
        func_name = tool_call.function.name
        func_to_call = available_functions[func_name]
        func_args = json.loads(tool_call.function.arguments)
        
        func_response = func_to_call(**func_args)
        
        messages.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": func_name,
            "content": str(func_response),
        })

    final_resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0,
    )
    print(final_resp.choices[0].message.content)
else:
    print(response_message.content)

# # Gemini
# # 실행: python code/ch05_function_calling.py
# import sys, pathlib
# sys.path.append(str(pathlib.Path(__file__).resolve().parent))
# from common import get_genai_client, GEMINI_MODEL, DATA
# from google.genai import types
# import pandas as pd

# client = get_genai_client()
# rates = pd.read_csv(DATA / "exchange_rates.csv")   # 환율 (currency, krw_per_unit)
# inv = pd.read_csv(DATA / "inventory.csv")          # 재고 (product_name, stock, warehouse)

# # [중요] 함수의 독스트링과 타입힌트가 모델에게 주는 '사용 설명서'다(모델은 본문을 못 본다).
# def get_exchange_rate(currency: str) -> str:
#     # """통화 코드(USD, EUR, JPY 등)를 받아 1단위당 원화(KRW) 환율을 반환한다. """

#     """사용자가 특정 외화(USD, EUR, JPY 등)의 환율을 물어보거나, 가격 환산을 위해 환율이 필요할 때 호출합니다.
#         질문에 '달러'만 언급되어 있다면 'USD'처럼 표준 통화 코드로 변환하여 인자(currency)로 전달해야 합니다.
        
#         반환 형식은 모델이 자연스러운 답변을 생성할 수 있도록 '1 [통화]당 [원화]원'의 정보를 포함합니다.
        
#         Args:
#             currency (str): 환율을 조회할 3자리 통화 코드 (예: 'USD', 'EUR', 'JPY')
            
#         Returns:
#             str: 해당 외화 1단위당 원화(KRW) 환율 정보 메시지 """
#     row = rates[rates["currency"].str.upper() == currency.upper()]
#     if row.empty:
#         return f"{currency} 환율 정보가 없습니다."
#     krw = float(row.iloc[0]["krw_per_unit"])
#     return f"1 {currency.upper()} = {krw:,.2f} KRW"

# def get_stock(product_name: str) -> str:
#     """상품명(일부만 입력해도 됨)을 받아 현재 재고 수량을 반환한다."""
    
#     row = inv[inv["product_name"].str.contains(product_name, na=False)]
#     if row.empty:
#         return f"'{product_name}' 재고 정보를 찾지 못했습니다."
#     r = row.iloc[0]
#     return f"{r['product_name']} 재고 {int(r['stock'])}개 ({r['warehouse']})"

# print(get_stock("이어버드"))          # 승승 무선 블루투스 이어버드 SE 재고 225개 (...)
# print(get_exchange_rate("USD"))      # 1 USD = 1,385.50 KRW

# from common import get_genai_client, GEMINI_MODEL
# from google.genai import types

# #client = get_genai_client()
# # (get_stock, get_exchange_rate 는 04번에서 만든 함수)

# question = "이어버드 재고 있어? 그리고 가격을 달러로 환산하려면 환율이 얼마야?"

# resp = client.models.generate_content(
#     model=GEMINI_MODEL,
#     contents=question,
#     config=types.GenerateContentConfig(
#         tools=[get_stock, get_exchange_rate],   # ← 파이썬 함수를 그대로 도구로!
#         temperature=0,
#     ),
# )
# print(resp.text)  # 어떤 이어버드를 찾으시는지 알려주시겠어요? 그리고 어떤 통화의 환율을 알려드릴까요?

