# 실행: python code/ch07_agent_loop.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL, DATA
import pandas as pd
import json

client = get_openai_client()
inv = pd.read_csv(DATA / "inventory.csv")

def get_stock(product_name: str) -> str:
    """상품명(일부만 입력해도 됨)을 받아 현재 재고 수량을 반환한다."""
    row = inv[inv["product_name"].str.contains(product_name, na=False)]
    if row.empty:
        return f"'{product_name}' 재고 정보 없음"
    r = row.iloc[0]
    return f"{r['product_name']} 현재 재고 {int(r['stock'])}개"

def get_reorder_level(product_name: str) -> str:
    """상품명을 받아 재주문 기준 수량(reorder_level)을 반환한다. 재고가 이 값 이하이면 재주문이 필요하다."""
    row = inv[inv["product_name"].str.contains(product_name, na=False)]
    if row.empty:
        return f"'{product_name}' 재주문 기준 정보 없음"
    r = row.iloc[0]
    return f"{r['product_name']} 재주문 기준 {int(r['reorder_level'])}개"

# 이름 -> 함수 매핑
TOOLS = {
    "get_stock": get_stock,
    "get_reorder_level": get_reorder_level,
}

# OpenAI Tool 규격 스키마
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock",
            "description": "상품명(일부만 입력해도 됨)을 받아 현재 재고 수량을 반환한다.",
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
            "name": "get_reorder_level",
            "description": "상품명을 받아 재주문 기준 수량(reorder_level)을 반환한다. 재고가 이 값 이하이면 재주문이 필요하다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "재주문 기준을 조회할 상품명",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
]

def run_agent(question: str, max_steps: int = 6):
    """질문을 받아 도구를 반복 호출하며 목표를 끝낼 때까지 도는 ReAct 루프."""
    messages = [
        {
            "role": "system",
            "content": (
                "너는 승승장구몰 재고 관리 에이전트다. 도구로 재고와 재주문 기준을 확인하고, "
                "재고가 재주문 기준 이하이면 재주문을 권유하라. 한국어로 답하라."
            ),
        },
        {"role": "user", "content": question},
    ]

    for step in range(1, max_steps + 1):
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            temperature=0,
        )
        msg = resp.choices[0].message

        # 종료 ①: 더 부를 도구 없음 -> 최종 답
        if not msg.tool_calls:
            print(f"[STEP {step}] 최종 답변")
            return msg.content

        # 모델의 Action(도구 호출 요청)을 히스토리에 추가
        messages.append(msg)

        # 모델이 요청한 도구들을 실행(Observation) -> 히스토리에 결과 추가
        for tc in msg.tool_calls:
            func_name = tc.function.name
            args = json.loads(tc.function.arguments)
            print(f"[STEP {step}] 호출: {func_name} {args}")

            result = TOOLS[func_name](**args)
            print("          관찰:", result)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": func_name,
                "content": json.dumps({"result": result}),
            })

    print("[종료] 최대 스텝 도달 — 안전장치 작동")  # 종료 ②: max_steps 초과
    return None

# answer = run_agent("스마트워치 재고를 확인하고, 재주문이 필요하면 알려줘.")
answer = run_agent("이어버드 재고 확인하고 재주문 필요한지 알려줘.")
print(answer)

# Gemini
# # 실행: python code/ch07_agent_loop.py
# import sys, pathlib
# sys.path.append(str(pathlib.Path(__file__).resolve().parent))
# from common import get_genai_client, GEMINI_MODEL, DATA
# from google.genai import types
# import pandas as pd

# client = get_genai_client()
# inv = pd.read_csv(DATA / "inventory.csv")

# def get_stock(product_name: str) -> str:
#     """상품명(일부만 입력해도 됨)을 받아 현재 재고 수량을 반환한다."""
#     row = inv[inv["product_name"].str.contains(product_name, na=False)]
#     if row.empty:
#         return f"'{product_name}' 재고 정보 없음"
#     r = row.iloc[0]
#     return f"{r['product_name']} 현재 재고 {int(r['stock'])}개"

# def get_reorder_level(product_name: str) -> str:
#     """상품명을 받아 재주문 기준 수량(reorder_level)을 반환한다. 재고가 이 값 이하이면 재주문이 필요하다."""
#     row = inv[inv["product_name"].str.contains(product_name, na=False)]
#     if row.empty:
#         return f"'{product_name}' 재주문 기준 정보 없음"
#     r = row.iloc[0]
#     return f"{r['product_name']} 재주문 기준 {int(r['reorder_level'])}개"

# # 이름 → 함수 매핑 (모델이 고른 이름으로 진짜 함수를 찾기 위함, 5강 복습)
# TOOLS = {"get_stock": get_stock, "get_reorder_level": get_reorder_level}



# # 반복문으로 처리하는 도구
# def run_agent(question: str, max_steps: int = 6):
#     """질문을 받아 도구를 반복 호출하며 목표를 끝낼 때까지 도는 ReAct 루프."""
#     config = types.GenerateContentConfig(
#         tools=list(TOOLS.values()),
#         # 자동 실행을 꺼서 '결정 → 우리가 실행 → 결과 전달'을 직접 돌린다
#         automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
#         system_instruction=(
#             "너는 승승장구몰 재고 관리 에이전트다. 도구로 재고와 재주문 기준을 확인하고, "
#             "재고가 재주문 기준 이하이면 재주문을 권유하라. 한국어로 답하라."
#         ),
#         temperature=0,
#     )
#     # 대화 기록(누적): 모델 호출마다 관찰 결과를 덧붙인다 → 모델이 '방금 본 결과'를 근거로 판단
#     history = [types.Content(role="user", parts=[types.Part(text=question)])]

#     for step in range(1, max_steps + 1):
#         resp = client.models.generate_content(
#             model=GEMINI_MODEL, contents=history, config=config)

#         if not resp.function_calls:                 # 종료 ①: 더 부를 도구 없음 → 최종 답
#             print(f"[STEP {step}] 최종 답변")
#             return resp.text

#         # 모델이 부른 도구(Action)를 history에 기록
#         history.append(resp.candidates[0].content)

#         # 부른 도구를 우리가 실행(Observation) → history에 결과 추가
#         for fc in resp.function_calls:
#             print(f"[STEP {step}] 호출:", fc.name, dict(fc.args))
#             result = TOOLS[fc.name](**dict(fc.args))   # 우리가 실행
#             print("           관찰:", result)
#             history.append(types.Content(role="user", parts=[
#                 types.Part.from_function_response(name=fc.name, response={"result": result})
#             ]))

#     print("[종료] 최대 스텝 도달 — 안전장치 작동")   # 종료 ②: max_steps 초과
#     return None


# run_agent("스마트워치 재고를 확인하고, 재주문이 필요하면 알려줘.")