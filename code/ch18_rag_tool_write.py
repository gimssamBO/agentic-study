import pathlib
import sys
import pandas as pd

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA, DOCS, get_chat, get_embeddings
from langchain.agents import create_agent
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import create_retriever_tool, tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

# =====================================================================
# 1. 데이터 로드 (원본 보호 설정)
# =====================================================================
_orders_원본 = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")
orders = _orders_원본.copy()  # [핵심] 쓰기는 '복사본'에만 수행 (원본 보존)

products = pd.read_csv(DATA / "products.csv", encoding="utf-8-sig")

_대기중_취소 = {}  # 보류 중인 취소 요청 전역 저장소


# =====================================================================
# 2. 도구(Tools) 정의
# =====================================================================

# [도구 1] 정책 검색 RAG 도구
def build_policy_tool():
    """정책 문서를 인덱싱해 RAG 검색 도구로 변환."""
    docs = []
    for f in ["환불교환정책.pdf", "멤버십정책.pdf"]:
        docs.extend(PyPDFLoader(str(DOCS / f)).load())
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50
    ).split_documents(docs)
    retriever = FAISS.from_documents(chunks, get_embeddings()).as_retriever(
        search_kwargs={"k": 4}
    )
    return create_retriever_tool(
        retriever,
        "policy_search",
        "승승장구몰 환불/교환/멤버십 정책 문서를 검색한다. 정책·절차·규정 질문에 사용.",
    )


# [도구 2] 주문 상태 조회 도구
@tool
def get_order_status(order_id: str) -> str:
    """주문번호(order_id)로 주문 상태/상품/날짜를 조회한다. 예: 'O000902'"""
    row = orders[orders["order_id"] == order_id.strip()]
    if row.empty:
        return f"주문번호 {order_id} 를 찾을 수 없습니다."
    r = row.iloc[0]
    return (
        f"주문 {order_id}: 상품='{r['product_name']}', 상태='{r['status']}', "
        f"주문일={r['order_date']}, 수량={r['quantity']}"
    )


# [도구 3] 재고 조회 도구
@tool
def get_stock(product_name: str) -> str:
    """상품명으로 현재 재고 수량을 조회한다. 예: '무선 이어버드'"""
    row = products[
        products["product_name"].str.contains(product_name.strip(), na=False)
    ]
    if row.empty:
        return f"'{product_name}' 상품을 찾을 수 없습니다."
    r = row.iloc[0]
    return f"'{r['product_name']}' 재고: {r['stock']}개"

# 교안4. 안전장치 ② — 2단계 확인 절차
# [도구 4] 주문 취소 1단계: 요청 보류
@tool
def request_cancel_order(order_id: str) -> str:
    """[1단계] 취소를 '요청'만 한다(아직 변경 안 함). 확인이 필요하다."""
    row = orders[orders["order_id"] == order_id.strip()]
    if row.empty:
        return f"주문번호 {order_id}를 찾을 수 없습니다."

    cur = row.iloc[0]["status"]
    if cur == "취소":
        return f"주문 {order_id}는 이미 취소된 상태입니다."

    _대기중_취소[order_id] = cur
    return (
        f"주문 {order_id}(현재 상태: {cur}) 취소를 요청했습니다. "
        f"정말 취소하시겠습니까? 확정하려면 confirm_cancel_order를 호출하세요."
    )
    
# 교안3. 안전장치 ① — 복사본에만 쓰기
# [도구 5] 주문 취소 2단계: 최종 확정
@tool
def confirm_cancel_order(order_id: str) -> str:
    """[2단계] 1단계 요청을 확정해 상태를 '취소'로 변경한다."""
    if order_id not in _대기중_취소:  # 1단계 요청이 없으면 취소 막음
        return "먼저 request_cancel_order로 요청하세요."

    orders.loc[orders["order_id"] == order_id, "status"] = "취소"
    del _대기중_취소[order_id]
    return f"주문 {order_id} 취소 완료(복사본에만 반영)."


# =====================================================================
# 3. 에이전트 조립 및 실행
# =====================================================================
policy_tool = build_policy_tool()
tools = [
    policy_tool,
    get_order_status,
    get_stock,
    request_cancel_order,
    confirm_cancel_order,
]

llm = get_chat(temperature=0)


# 교안5. 시스템 프롬프트로 강제
system_prompt = (
    "너는 승승장구몰 CS 에이전트다. 정책은 policy_search로 검색하고, "
    "주문 상태는 get_order_status, 재고는 get_stock으로 조회해 답하라.\n"
    "주문 취소는 반드시 request_cancel_order로 먼저 확인을 받고, "
    "사용자가 동의하면 confirm_cancel_order로 확정하라. 함부로 확정하지 마라."
)

agent = create_agent(
    llm,
    tools=tools,
    system_prompt=system_prompt,
)


# =====================================================================
# 4. 종합 대화 테스트
# =====================================================================
if __name__ == "__main__":
    print("=== [1] 복합 질문 및 취소 1단계 요청 테스트 ===")
    q1 = "O000902 주문 상태 확인해주고, 취소하고 싶은데 절차가 어떻게 돼?"
    out1 = agent.invoke({"messages": [{"role": "user", "content": q1}]})
    print("\n[에이전트 답변 1]\n", out1["messages"][-1].content)

    print("\n=== [2] 사용자 동의 후 취소 2단계 확정 테스트 ===")
    out2 = agent.invoke({
        "messages": [
            {"role": "user", "content": q1},
            {"role": "assistant", "content": out1["messages"][-1].content},
            {"role": "user", "content": "네, O000902 주문 정말로 취소 확정해 주세요."},
        ]
    })
    print("\n[에이전트 답변 2]\n", out2["messages"][-1].content)

    print("\n=== [3] 원본 vs 복사본 상태 비교 ===")
    print("메모리(orders) 상태:", orders[orders["order_id"] == "O000902"]["status"].values)
    print("원본 파일(_orders_원본) 상태:", _orders_원본[_orders_원본["order_id"] == "O000902"]["status"].values)