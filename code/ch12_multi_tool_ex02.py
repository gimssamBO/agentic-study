import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

llm = get_chat(provider="openai")
products = pd.read_csv(DATA / "products.csv", encoding="utf-8-sig")
orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")

@tool
def get_price(product_name: str) -> str:
    """상품명으로 판매가와 product_id를 조회한다."""
    hit = products[products["product_name"].str.contains(product_name, na=False)]
    if hit.empty:
        return f"[조회실패] '{product_name}' 없음"
    r = hit.iloc[0]
    return f"{r['product_name']}(id={r['product_id']}) 가격 {int(r['price']):,}원"

@tool
def total_quantity(product_id: str) -> str:
    """product_id의 총 판매수량(quantity 합계)을 계산한다."""
    qty = int(orders[orders["product_id"] == product_id]["quantity"].sum())
    return f"{product_id} 총 판매수량 {qty}개"

agent = create_agent(llm, tools=[get_price, total_quantity],
    system_prompt="너는 운영 비서다. 앞 도구 결과(product_id)를 다음 도구에 이어 써라.")

q = "이어버드 가격 조회하고, 그 상품의 총 판매수량도 알려줘."
for step in agent.stream({"messages": [{"role": "user", "content": q}]}, stream_mode="values"):
    msg = step["messages"][-1]
    # 도구 호출 로그 출력
    if getattr(msg, "tool_calls", None):
        for tc in msg.tool_calls:
            print(f"🔧 도구 호출: {tc['name']}({tc['args']})")