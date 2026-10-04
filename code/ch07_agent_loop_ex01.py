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

# 실습 추가
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

    # 이미 실행한 (도구명, 인자) 조합을 기억하는 집합 — 중복 호출 탐지용
    seen_calls = set()

    for step in range(1, max_steps + 1):
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            temperature=0,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return msg.content              # 정상 종료

        messages.append(msg)

        for tc in msg.tool_calls:
            func_name = tc.function.name
            args = json.loads(tc.function.arguments)

            # 호출 서명 만들기: args를 정렬된 튜플로 → dict 순서와 무관하게 같은 호출을 같은 키로
            signature = (func_name, tuple(sorted(args.items())))

            if signature in seen_calls:
                # 같은 도구를 같은 인자로 또 부름 → 진전 없는 반복 → 강제 종료
                print("  [경고] 동일한 도구·인자 반복 호출 감지 → 무한루프 방지 강제 종료")
                return None
            seen_calls.add(signature)        # 처음 보는 호출이면 기록

            result = TOOLS[func_name](**args)
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