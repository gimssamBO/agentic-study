# -*- coding: utf-8 -*-
# 실행: python code/ch30_final_error_case.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

from common import get_chat
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

# CS 통합 에이전트 4대 도구 정의
@tool
def get_order_status(order_id: str) -> str:
    """[r2] 주문번호로 주문 상태를 조회한다. (orders.csv 기반)"""
    orders = {"o123456": "배송 중", "o654321": "배송 완료"}
    return orders.get(order_id, f"주문번호 {order_id}를 찾을 수 없습니다.")

@tool
def get_stock(product_name: str) -> str:
    """[r3] 상품명으로 재고 수량을 조회한다. (inventory.csv 기반)"""
    inventory = {"로봇청소기": "15개", "무선이어폰": "3개"}
    return inventory.get(product_name, f"'{product_name}' 상품 재고 정보를 찾을 수 없습니다.")

@tool
def search_faq(keyword: str) -> str:
    """[r4] 키워드로 FAQ 답변을 조회한다. (faq.csv 기반)"""
    faqs = {"환불": "구매 후 7일 이내 가능합니다.", "교환": "상품 하자 시 무료 교환됩니다."}
    return faqs.get(keyword, "관련 FAQ를 찾지 못했습니다.")

@tool
def policy_search(query: str) -> str:
    """[r1] 정책/멤버십 문서를 검색한다. (PDF RAG 기반)"""
    policies = {"무료배송": "3만원 이상 구매 시 무료배송입니다."}
    return policies.get(query, "해당 정책 문서를 찾지 못했습니다.")

# 에이전트 및 메모리 저장소 생성 (LangGraph 표준)
tools = [get_order_status, get_stock, search_faq, policy_search]
llm = get_chat(temperature=0.0)

system_prompt = (
    "너는 승승장구몰 통합 CS 상담원이다.\n"
    "1. 도구 실행 결과가 '찾을 수 없다'면 절대로 지어내지 말고 없는 정보라고 안내하라.\n"
    "2. 지시어나 맥락이 불명확한 경우 정확히 무엇인지 질문하라."
)

# 단기 기억 세션 관리자 (In-Memory Checkpointer)
memory = MemorySaver()

# LangGraph 기반 에이전트 구축 (ImportError 및 버전 문제 완벽 해결)
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_prompt,
    checkpointer=memory
)

def answer(message: str, thread_id: str = "demo") -> str:
    """외부 노출 단일 진입점: thread_id로 대화 세션을 구분한다."""
    config = {"configurable": {"thread_id": thread_id}}
    
    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )
    
    # 마지막 AI 응답 메시지 출력
    return result["messages"][-1].content

# ==================================================================
# 2. 에러 시나리오 4가지
# ==================================================================
scenarios = [
    ("주문 o999999 상태 알려줘",
     "기대: 존재하지 않는 주문 → '찾을 수 없음' 안내"),
    ("'로봇청쇼기' 재고 있어?",
     "기대: 오타/미존재 상품 → 재고 정보 없음 안내"),
    ("승승장구몰 우주배송 정책이 어떻게 돼?",
     "기대: 정책 문서에 근거 없음 → 모른다/확인 불가 안내"),
    ("아까 그거 다시 알려줘",
     "기대: 가리킬 직전 맥락 없음 → 무엇인지 명확화 요청"),
]

# ==================================================================
# 3. 1차 방어선 — 도구 단위 점검
# ==================================================================
def check_tools_directly() -> None:
    """도구 단위 direct 실행 검증"""
    print("  없는 주문:", get_order_status.invoke({"order_id": "o999999"}))
    print("  오타 상품:", get_stock.invoke({"product_name": "로봇청쇼기"}))
    print("  엉뚱 faq:", search_faq.invoke({"keyword": "우주배송"}))

# ==================================================================
# 4. 2차 방어선 — 에이전트의 정직함
# ==================================================================
if __name__ == "__main__":
    print("=== [1단계] 도구 직접 검증 ===")
    check_tools_directly()
    print()

    print("=== [2단계] 에이전트 엣지 케이스 테스트 ===")
    tid = "edge-test-1"
    for i, (q, expect) in enumerate(scenarios, 1):
        print(f"[턴 {i}] 고객:", q)
        print(f"  ⤷ {expect}")
        print("상담원:", answer(q, thread_id=tid))
        print()