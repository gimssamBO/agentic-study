# 실행: python code/ch12_multi_tool.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

llm = get_chat(provider="openai")

# 데이터는 모듈 로드 시 1회만 읽는다 (도구 호출마다 read_csv 하면 느려진다)
orders = pd.read_csv(DATA / "orders.csv")
inventory = pd.read_csv(DATA / "inventory.csv")
orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["month"] = orders["order_date"].dt.strftime("%Y-%m")

# 도구 ① — 주문 상태 조회
@tool
def get_order_status(customer_id: str) -> str:
    """고객 ID(예: 'C0001')의 가장 최근 주문 1건의 상태를 조회한다.
    상품명, product_id, 주문일, 상태('배송완료'/'배송중'/'결제완료'/'취소'/'환불')를 반환한다."""
    df = orders[orders["customer_id"] == customer_id]   # 해당 고객의 주문만 필터
    if df.empty:
        return f"{customer_id} 고객의 주문 내역이 없습니다."
    latest = df.sort_values("order_date").iloc[-1]      # 가장 최근 1건
    return (
        f"최근 주문: {latest['product_name']}(product_id={latest['product_id']}), "
        f"주문일 {latest['order_date'].date()}, 상태 '{latest['status']}'"
    )

# 도구 ② — 재고 조회
@tool
def get_stock(product_id: str) -> str:
    """product_id(예: 'P0001')의 현재 재고 수량, 창고, 재주문 기준을 조회한다."""
    # [연쇄] 앞 도구가 돌려준 product_id를 이 도구의 입력으로 이어 쓰는 것이 멀티툴의 핵심
    df = inventory[inventory["product_id"] == product_id]
    if df.empty:
        return f"{product_id} 의 재고 정보가 없습니다."
    r = df.iloc[0]
    # 재고가 재주문기준 이하면 경고 문구를 덧붙인다
    warn = " (재주문 필요!)" if int(r["stock"]) <= int(r["reorder_level"]) else ""
    return f"{r['product_name']}({product_id}) 재고 {r['stock']}개, 창고 {r['warehouse']}{warn}"


# 도구 ③ — 매출 분석
@tool
def run_pandas(expr: str) -> str:
    """주문 데이터(orders)로 매출 등을 분석하는 pandas 식을 실행한다.
    사용 가능: orders(컬럼: month, category, amount, status 등), pd.
    매출 집계 시 status가 '취소','환불'인 건은 제외한다.
    예: "orders[(orders['status']=='배송완료')&(orders['month']=='2026-05')]['amount'].sum()" """
    try:
        result = eval(expr, {"__builtins__": {}}, {"orders": orders, "pd": pd})
    except Exception as e:
        return f"실행 오류: {e}"
    return str(result)

# 1. 도구 목록으로 묶기
# 에이전트에게 쥐여 줄 도구 목록. LLM은 각 docstring을 보고 무엇을 쓸지 라우팅한다.
TOOLS = [get_order_status, get_stock, run_pandas]

# 2. 시스템 프롬프트 — 라우팅·연쇄 규칙
SYSTEM = (
    "너는 승승장구몰의 운영 비서다. 필요한 도구를 골라 순서대로 사용해 답하라.\n"
    "여러 정보가 필요하면 도구를 여러 번 호출해도 된다. 앞 도구 결과(product_id 등)를\n"
    "다음 도구의 입력으로 이어 써라. 매출 집계 시 취소/환불은 제외하고,\n"
    "답은 한국어로 항목별로 정리한다."
)

# 3. 에이전트 생성
agent = create_agent(llm, tools=TOOLS, system_prompt=SYSTEM)

# 4. 간단 실행
# q = "C0001 고객의 최근 주문 상태를 알려줘."
q = (
    "C0001 고객의 최근 주문 상태와, 그 상품의 재고, "
    "그리고 2026-05월 전체 매출을 알려줘."
)
result = agent.invoke({"messages": [{"role": "user", "content": q}]})
print(result["messages"][-1].content)
