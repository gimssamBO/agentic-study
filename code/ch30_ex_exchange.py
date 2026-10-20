# -*- coding: utf-8 -*-
# 실행: python code/ch30_ex_exchange.py
import sys, pathlib, random, string
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

from common import get_chat, DATA, DOCS
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver


# ==================================================================
# 1. 기존 기본 도구 정의
# ==================================================================
@tool
def get_order_status(order_id: str) -> str:
    """[r2] 주문번호로 주문 상태를 조회한다."""
    orders = {"o000050": "배송 완료", "o123456": "배송 중"}
    return orders.get(order_id, f"주문번호 {order_id}를 찾을 수 없습니다.")


@tool
def get_stock(product_name: str) -> str:
    """[r3] 상품명으로 재고 수량을 조회한다."""
    inventory = {"로봇청소기": "15개", "무선이어폰": "3개"}
    return inventory.get(product_name, f"'{product_name}' 상품 재고 정보를 찾을 수 없습니다.")


@tool
def search_faq(keyword: str) -> str:
    """[r4] 키워드로 FAQ 답변을 조회한다."""
    faqs = {"환불": "구매 후 7일 이내 가능합니다.", "교환": "상품 하자 시 무료 교환됩니다."}
    return faqs.get(keyword, "관련 FAQ를 찾지 못했습니다.")


@tool
def policy_search(query: str) -> str:
    """[r1] 정책/멤버십 문서를 검색한다. (PDF RAG)"""
    policies = {"교환": "상품 수령 후 7일 이내 불량 발생 시 무료 교환 가능합니다."}
    return policies.get(query, "해당 정책 문서를 찾지 못했습니다.")


# ==================================================================
# 2. [추가] 교환 접수 도구 정의
# ==================================================================
@tool
def request_exchange(order_id: str, reason: str) -> str:
    """[추가] 주문에 대한 교환을 접수하고 접수번호를 반환한다.

    order_id: 교환할 주문번호, reason: 교환 사유.
    """
    # 접수번호 생성 (ex- + 영숫자 6자리)
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    ticket = f"ex-{suffix}"
    # (실무에선 여기서 DB에 교환 접수 기록을 INSERT)
    return (f"교환 접수가 완료되었습니다. 접수번호: {ticket}\n"
            f"주문 {order_id} / 사유: {reason}\n"
            f"영업일 기준 1~2일 내 담당자가 연락드립니다.")


# ==================================================================
# 3. 에이전트 빌더 및 실행 진입점
# ==================================================================
system_prompt = (
    "너는 승승장구몰의 통합 CS 상담원이다. 친절한 한국어로 답하라.\n"
    "- 주문 상태는 get_order_status, 재고는 get_stock, 자주 묻는 질문은 search_faq,\n"
    "  환불/교환/멤버십 정책은 policy_search 도구를 사용하라.\n"
    "- 고객이 '교환하고 싶다/교환 신청'을 요청하면 request_exchange 도구로 접수하라.\n"
    "- 정책 질문은 반드시 policy_search 결과로만 답하고, 모르면 모른다고 하라.\n"
    "- 이전 대화 맥락을 기억해 이어서 답하라."
)

memory = MemorySaver()

def build_agent():
    """설정+도구+시스템 프롬프트+메모리를 결합해 LangGraph 에이전트를 생성한다."""
    llm = get_chat(temperature=0.0)
    tools = [
        get_order_status, 
        get_stock, 
        search_faq, 
        policy_search, 
        request_exchange  # ← 교환 도구 추가
    ]
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        checkpointer=memory
    )
    return agent


# 전역 에이전트 인스턴스 생성
agent = build_agent()


def answer(message: str, thread_id: str = "demo") -> str:
    """외부 노출 단일 진입점. thread_id로 대화 세션을 구분한다."""
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )
    return result["messages"][-1].content


# ==================================================================
# 4. 교환 접수 테스트 실행
# ==================================================================
if __name__ == "__main__":
    print("=== [교환 접수 테스트] ===")
    response = answer("주문 o000050 불량이라 교환하고 싶어. 화면이 안 켜져.", thread_id="ex-1")
    print("상담원 응답:\n", response)