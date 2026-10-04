import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_genai_client, GEMINI_MODEL, DATA
import pandas as pd

client = get_genai_client()

def ask(question:str) -> str:
  resp = client.models.generate_content(model=GEMINI_MODEL, contents=question)
  return resp.text

def compare(order_id:str) -> None:
  """LLM의 답(환각 가능)과 CSV의 실제 상태(사실)를 나란히 보여 준다."""
  # (1) LLM에게 직접 묻기 — 도구 없이
  llm_answer = ask(f"승승장구몰 주문번호 {order_id}는 지금 배송 어디까지 왔나요?")
  
  # (2) CSV에서 사실 찾기 — 도구처럼
  orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")
  row = orders[orders["order_id"] == order_id]
  fact = "주문번호 없음" if row.empty else row.iloc[0]["status"]
  
  print("=" * 60)
  print(f"[LLM 답(도구 없음)] {llm_answer}")
  print(f"[CSV 사실 (도구 사용)] {orders} -> {fact}")
  print("=" * 60)
  
if __name__=="__main__":
  compare("O002282") # data/orders.csv 에 실제로 있는 주문번호