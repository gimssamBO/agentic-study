import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

llm = get_chat(provider="openai")

# 데이터 로드 (한글 깨짐 방지 utf-8-sig 적용)
orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")
orders["month"] = pd.to_datetime(orders["order_date"]).dt.strftime("%Y-%m")
faq = pd.read_csv(DATA / "faq.csv", encoding="utf-8-sig")

@tool
def lookup_faq(keyword: str) -> str:
    """FAQ에서 키워드로 검색한다.
    주의: '환불 정책' 같은 문장 대신 '환불', '배송' 등 단일 키워드 위주로 입력할 것.
    """
    # 1. 전달받은 키워드의 공백 제거
    clean_keyword = keyword.replace(" ", "")
    
    # 2. 질문 데이터 공백 제거 후 검색하여 검색 적중률 향상
    hit = faq[faq["question"].str.replace(" ", "").str.contains(clean_keyword, na=False)]
    
    # 3. 만약 2단어 이상 전달되어 검색 실패 시, 첫 번째 단어로 2차 검색
    if hit.empty and " " in keyword:
        first_word = keyword.split()[0]
        hit = faq[faq["question"].str.contains(first_word, na=False)]

    if hit.empty:
        return f"[조회실패] '{keyword}' 관련 FAQ가 없습니다."
    
    return "\n".join(f"Q: {r.question}\nA: {r.answer}" for r in hit.itertuples())

@tool
def run_pandas(expr: str) -> str:
    """주문 데이터 분석 도구. 
    반드시 'orders' (또는 'df') 데이터프레임 변수를 사용하세요.
    주요 컬럼: month, status, amount, quantity
    """
    try:
        # df와 orders를 모두 컨텍스트에 전달하여 변수명 오류 방지
        return str(eval(expr, {"__builtins__": {}}, {"orders": orders, "df": orders, "pd": pd}))
    except Exception as e:
        return f"실행 오류: {e}"

agent = create_agent(
    llm, 
    tools=[lookup_faq, run_pandas],
    system_prompt="너는 운영 비서다. FAQ와 데이터 도구를 골라 쓰고 한국어로 답하라."
)

q = "환불 정책 알려주고, 이번 달(2026-05) 환불 건수도 알려줘."

# 단일 문자열 q를 전달하여 스트리밍 호출
for step in agent.stream({"messages": [{"role": "user", "content": q}]}, stream_mode="values"):
    step["messages"][-1].pretty_print()