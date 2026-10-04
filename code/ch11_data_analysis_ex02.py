import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

llm = get_chat(provider="openai")
orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")

@tool
def run_pandas(expr: str) -> str:
    """주문 데이터 분석. orders(컬럼: category, amount, status...), pd 사용 가능."""
    try:
        return str(eval(expr, {"__builtins__": {}}, {"orders": orders, "pd": pd}))
    except Exception as e:
        return f"실행 오류: {e}"

# 규칙 있는 에이전트 vs 없는 에이전트
agent = create_agent(llm, tools=[run_pandas],
    system_prompt="너는 데이터 분석가다. 매출 집계 시 status가 '취소','환불'인 행은 제외하라.")
agent_no_rule = create_agent(llm, tools=[run_pandas],
    system_prompt="너는 데이터 분석가다.")   # 규칙 없음

q = "카테고리별 총매출을 알려줘."
print("[규칙 있음]", agent.invoke({"messages": [{"role": "user", "content": q}]})["messages"][-1].content)
print("[규칙 없음]", agent_no_rule.invoke({"messages": [{"role": "user", "content": q}]})["messages"][-1].content)

# pandas로 직접 차이 검증 (취소/환불 금액 합)
diff = orders[orders["status"].isin(["취소", "환불"])]["amount"].sum()
print(f"\n[검증] 취소/환불 금액 합계 = {int(diff):,}원 (이만큼 차이나야 함)")