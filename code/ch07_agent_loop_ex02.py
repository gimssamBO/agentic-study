# 실행: python code/ch07_agent_loop.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL, DATA
import pandas as pd
import json

client = get_openai_client()
inv = pd.read_csv(DATA / "inventory.csv", encoding="utf-8-sig")


def get_warehouse_total(product_name: str) -> str:
    """상품명을 받아 모든 창고의 재고(stock) 합계를 반환한다. 여러 창고에 흩어진 총재고가 궁금할 때 사용."""
    hit = inv[inv["product_name"].str.contains(product_name, na=False)]
    if hit.empty:
        return f"'{product_name}' 재고 정보 없음"
    total = int(hit["stock"].sum())
    name = hit.iloc[0]["product_name"]
    return f"{name} 전 창고 재고 합계 {total}개 (창고 {len(hit)}곳)"


def get_reorder_level(product_name: str) -> str:
    """상품명을 받아 재주문 기준 수량을 반환한다. 재고가 이 값 이하이면 재주문이 필요하다."""
    row = inv[inv["product_name"].str.contains(product_name, na=False)]
    if row.empty:
        return f"'{product_name}' 재주문 기준 정보 없음"
    return f"{row.iloc[0]['product_name']} 재주문 기준 {int(row.iloc[0]['reorder_level'])}개"


# 이름 -> 함수 매핑
TOOLS = {
    "get_warehouse_total": get_warehouse_total,
    "get_reorder_level": get_reorder_level,
}

# OpenAI Tool 규격 스키마
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_warehouse_total",
            "description": "상품명을 받아 모든 창고의 재고(stock) 합계를 반환한다. 여러 창고에 흩어진 총재고가 궁금할 때 사용.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "총재고를 조회할 상품명",
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
            "description": "상품명을 받아 재주문 기준 수량을 반환한다. 재고가 이 값 이하이면 재주문이 필요하다.",
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


answer = run_agent("스마트워치의 전 창고 재고 합계를 구하고, 재주문 기준과 비교해 재주문이 필요한지 알려줘.")
print(answer)