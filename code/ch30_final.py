
#############################################################
# 1. 시작부 + 29강 자산 재사용
# -*- coding: utf-8 -*-
# 실행: python code/ch30_final.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat, get_embeddings, DATA, DOCS
from ch29_deploy import load_config, setup_logging              # 29강 자산(설정·로깅) 재사용

import pandas as pd
from langchain_core.tools import tool

cfg = load_config()          # 29강 설정 로드(모델·온도·RAG 파라미터)
logger = setup_logging(cfg)  # 29강 구조적 로깅

orders = pd.read_csv(DATA / "orders.csv")        # 주문 데이터
inventory = pd.read_csv(DATA / "inventory.csv")  # 재고 데이터
faq = pd.read_csv(DATA / "faq.csv")              # FAQ 데이터


##################################################
# 2. 주문 조회 도구 (R2)
@tool
def get_order_status(order_id: str) -> str:
    """[R2] 주문번호(예: O000050)로 주문 상태/상품/금액을 조회한다.

    @tool docstring 은 LLM이 읽는 도구 설명서다. LLM은 주문 관련 질문이 오면 이 도구를 고른다.
    """
    hit = orders[orders["order_id"] == order_id.strip().upper()]
    if hit.empty:
        return f"주문번호 {order_id} 를 찾을 수 없습니다."
    r = hit.iloc[0]
    return (f"주문 {r.order_id}: {r.product_name} {r.quantity}개, "
            f"{int(r.amount):,}원, 주문일 {r.order_date}, 상태={r.status}")


####################################################
#3. 재고 조회 도구 (R3)
@tool
def get_stock(product_name: str) -> str:
    """[R3] 상품명(일부)으로 재고 수량을 조회한다."""
    hit = inventory[inventory["product_name"].str.contains(product_name, na=False)]
    if hit.empty:
        return f"'{product_name}' 상품 재고 정보를 찾을 수 없습니다."
    return "\n".join(f"{r.product_name}: 재고 {r.stock}개({r.warehouse}창고)"
                     for r in hit.head(3).itertuples())



#############################################
#4. FAQ 검색 도구 (R4)
@tool
def search_faq(keyword: str) -> str:
    """[R4] 키워드로 FAQ에서 관련 답변을 찾는다."""
    hit = faq[faq["question"].str.contains(keyword, na=False)]
    if hit.empty:
        hit = faq[faq["answer"].str.contains(keyword, na=False)]   # 질문에 없으면 답변에서도
    if hit.empty:
        return "관련 FAQ를 찾지 못했습니다."
    return "\n".join(f"Q.{r.question}\nA.{r.answer}" for r in hit.head(2).itertuples())



#####################################################
# 6. 도구 단위로 테스트

# # @tool 로 만든 함수는 .invoke({"인자명": 값}) 로 직접 호출
# print(get_order_status.invoke({"order_id": "O000050"}))
# # 주문 O000050: 자기계발 다이어리 2개, 36,000원, 주문일 2025-10-29, 상태=배송완료

# print(get_stock.invoke({"product_name": "다이어리"}))
# print(search_faq.invoke({"keyword": "무료배송"}))


##################################
# 3. 정책 도구 빌더
def build_policy_tool():
    """정책/멤버십 PDF를 임베딩→FAISS→retriever→도구로 만든다."""
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_core.tools.retriever import create_retriever_tool

    logger.info("정책 문서 인덱싱 시작(RAG)")
    docs = []
    for name in ["환불교환정책.pdf", "멤버십정책.pdf"]:
        docs += PyPDFLoader(str(DOCS / name)).load()     # ① PDF들을 페이지 문서로 로드
    splitter = RecursiveCharacterTextSplitter(           # ② 긴 문서를 검색 단위로 분할
        chunk_size=cfg["rag"]["chunk_size"], chunk_overlap=cfg["rag"]["chunk_overlap"])
    chunks = splitter.split_documents(docs)
    vs = FAISS.from_documents(chunks, get_embeddings())  # ③④ 임베딩 → FAISS 색인
    retriever = vs.as_retriever(search_kwargs={"k": cfg["rag"]["top_k"]})  # ⑤ 상위 k개 검색기
    logger.info(f"정책 문서 인덱싱 완료(청크 {len(chunks)}개)")
    return create_retriever_tool(                        # 검색기를 '도구'로 래핑
        retriever, "policy_search",
        "환불/교환/멤버십 등 승승장구몰 사내 정책 문서를 검색한다.")  # ← LLM이 읽는 도구 설명


#################################################
# 1. 시스템 프롬프트 — 에이전트의 역할 규칙

SYSTEM_PROMPT = (
    "너는 승승장구몰의 통합 CS 상담원이다. 친절한 한국어로 답하라.\n"
    "- 주문 상태는 get_order_status, 재고는 get_stock, 자주 묻는 질문은 search_faq,\n"
    "  환불/교환/멤버십 정책은 policy_search 도구를 사용하라.\n"
    "- 정책 질문은 반드시 policy_search 결과(문서 근거)로만 답하고, 모르면 모른다고 하라.\n"
    "- 이전 대화 맥락(예: '아까 그 정책')을 기억해 이어서 답하라."
)

##################################
# 2. 에이전트 빌더 — 통합의 핵심
_agent = None   # 모듈 캐시 (PDF 인덱싱이 비싸서 한 번만 빌드)


def build_agent():
    """설정+도구+RAG+메모리를 결합한 단일 에이전트를 만든다(30강 통합의 핵심)."""
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import InMemorySaver

    llm = get_chat(provider=cfg["llm"]["provider"], temperature=cfg["llm"]["temperature"])
    # 도구 4종 결합: 주문/재고/FAQ 조회 + 정책 RAG 검색
    tools = [get_order_status, get_stock, search_faq, build_policy_tool()]
    agent = create_agent(
        llm, tools=tools, system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver())     # InMemorySaver = 단기 메모리(thread_id 별 대화 기록)
    logger.info(f"에이전트 구성 완료(도구 {len(tools)}개)")
    return agent


############################################
# 4. 단일 진입점 answer (28강 설계)
def answer(message: str, thread_id: str = "demo") -> str:
    """외부 단일 진입점(28강 설계). 같은 thread_id = 같은 대화로 묶인다."""
    global _agent
    if _agent is None:
        _agent = build_agent()
    # config 의 thread_id 로 대화 세션을 구분 → 같은 id면 이전 대화를 이어 기억
    config = {"configurable": {"thread_id": thread_id}}
    result = _agent.invoke({"messages": [{"role": "user", "content": message}]}, config)
    return result["messages"][-1].content



#########################################
# 1. 데모 시나리오 — 세 능력을 한 번에
def main():
    tid = "user-1001"   # 한 사람의 대화 세션(같은 id로 호출해야 맥락이 이어짐)
    turns = [
        "환불 절차 알려줘",          # 1) RAG: 정책 문서 근거로 답
        "내 주문 O000050은?",        # 2) 도구: 주문 조회
        "아까 그 정책 다시 알려줘",     # 3) 메모리: '아까 그 정책'=환불을 기억해 이어 답
    ]
    for i, q in enumerate(turns, 1):
        print("=" * 60)
        print(f"[턴 {i}] 고객:", q)
        print("상담원:", answer(q, thread_id=tid))   # 같은 tid → 같은 대화 세션


if __name__ == "__main__":
    main()