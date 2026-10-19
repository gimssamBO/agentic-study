# -*- coding: utf-8 -*-
# 실행: python code/ch28_design.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import DATA, DOCS

from dataclasses import dataclass

# [왜 설계 먼저] 30강에서 RAG+도구+메모리를 한꺼번에 구현하기 전에, 이 파일로
#   '무엇을 만들지'를 코드 스켈레톤(시그니처+TODO)으로 못 박는다. 함수 이름·시그니처를
#   먼저 합의해두면 구현 단계에서 설계가 흔들리지 않는다('살아있는 설계 문서').

@dataclass
class AgentSpec:
    """통합 CS 에이전트의 설계 명세(요약). dataclass 로 설정값을 한눈에 본다."""
    name: str = "승승장구몰 통합 CS 에이전트"
    tools: tuple = ("get_order_status", "get_stock", "search_faq", "policy_search")
    use_rag: bool = True          # 정책/멤버십 PDF 검색에 RAG 사용
    use_memory: bool = True       # 단기 기억(thread 별 대화 세션)
    use_multi_agent: bool = False # [왜 단일] 도구가 4개뿐이라 역할 분리 불필요 → 단일로 시작


#############################
# 2. 도구 시그니처 (구현은 30강 TODO)
def get_order_status(order_id: str) -> str:
    """[r2] 주문번호로 주문 상태를 반환. (30강: orders.csv 조회)"""
    raise NotImplementedError("30강에서 구현")  # TODO


def get_stock(product_name: str) -> str:
    """[r3] 상품명으로 재고 수량을 반환. (30강: inventory.csv 조회)"""
    raise NotImplementedError("30강에서 구현")  # TODO


def search_faq(keyword: str) -> str:
    """[r4] 키워드로 faq 답변을 반환. (30강: faq.csv 조회)"""
    raise NotImplementedError("30강에서 구현")  # TODO


def policy_search(query: str) -> str:
    """[r1] 정책/멤버십 문서를 rag로 검색. (30강: faiss retriever)"""
    raise NotImplementedError("30강에서 구현")  # TODO


###############################################################
# 3. 에이전트 빌더 & 진입 함수 시그니처
def build_agent():
    """설정+도구+rag+메모리를 결합해 create_agent를 만든다. (30강)"""
    # TODO(30강): config 로드 → llm → tools=[...] → checkpointer=inmemorysaver()
    #   [설계 의도] inmemorysaver(단기 메모리) + thread_id 로 대화 세션을 구분한다.
    raise NotImplementedError("30강에서 구현")


def answer(message: str, thread_id: str = "demo") -> str:
    """외부에 노출되는 단일 진입점. thread_id로 대화 세션을 구분한다.

    [왜 단일 진입점] fastapi 같은 외부 호출은 이 함수 하나만 부르면 되게 만든다(29강 운영 계약).
    같은 thread_id = 같은 대화로 묶여 '아까 그 정책' 같은 맥락이 이어진다.
    """
    # TODO(30강): agent.invoke({"messages":[...]}, {"configurable":{"thread_id":...}})
    raise NotImplementedError("30강에서 구현")

###############################################################
# 4. 설계 요약 출력 — 살아있는 문서
def print_design():
    spec = AgentSpec()
    print("=" * 60)
    print(f"[설계] {spec.name}")
    print("=" * 60)
    print("요구사항:")
    print("  r1 정책 안내(rag) / r2 주문상태 / r3 재고 / r4 faq / r5 대화기억")
    print(f"\n도구 목록: {', '.join(spec.tools)}")
    print(f"rag 사용 : {spec.use_rag}  (대상: 정책/멤버십 pdf @ {DOCS})")
    print(f"메모리   : {spec.use_memory} (단기, thread_id 별)")
    print(f"멀티에이전트: {spec.use_multi_agent} (도구 4개 → 단일 에이전트로 시작)")
    print("\n데이터 흐름:")
    print("  사용자 → answer(message, thread_id) → create_agent")
    print("         → [도구/rag 선택 실행] → [inmemorysaver 기록] → 답변")
    print(f"\n데이터 소스: {DATA}")
    print("운영 계약 : post /chat {thread_id, message} (fastapi, 29강)")

if __name__ == "__main__":
    print_design()