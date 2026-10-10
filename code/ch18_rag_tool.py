# ch18_rag_tool.py  여러툴을 사용하는 에이전트
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, get_embeddings, DOCS, DATA
import pandas as pd

# 교안1. 데이터는 1회만 로드
# 데이터 1회 로드(요청마다 재로딩 금지)
orders = pd.read_csv(DATA / "orders.csv")
products = pd.read_csv(DATA / "products.csv")

# 교안2. 정책 검색 도구 만들기
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.tools.retriever import create_retriever_tool

def build_policy_tool():
    """정책 문서를 인덱싱해 RAG 검색 도구로 변환."""
    docs = []
    for f in ["환불교환정책.pdf", "멤버십정책.pdf"]:
        docs.extend(PyPDFLoader(str(DOCS / f)).load())
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50).split_documents(docs)
    retriever = FAISS.from_documents(chunks, get_embeddings()).as_retriever(
        search_kwargs={"k": 4})
    # retriever를 'policy_search' 도구로 변환 (설명이 라우팅 기준)
    return create_retriever_tool(
        retriever,
        "policy_search",
        "승승장구몰 환불/교환/멤버십 정책 문서를 검색한다. 정책·절차·규정 질문에 사용.")

# 교안4. 도구 단독 테스트
print("=== 정책 검색 도구 테스트 ===")
policy_tool = build_policy_tool()
print(policy_tool.invoke("환불 절차"))


# 교안1. 주문 상태 조회 도구
import pandas as pd
from langchain_core.tools import tool
from common import DATA

orders = pd.read_csv(DATA / "orders.csv")

@tool
def get_order_status(order_id: str) -> str:
    """주문번호(order_id)로 주문 상태/상품/날짜를 조회한다. 예: 'O000902'"""
    # 없는 주문번호여도 예외로 죽지 않고 안내 문자열을 돌려준다(결정적·안전)
    row = orders[orders["order_id"] == order_id.strip()]
    if row.empty:
        return f"주문번호 {order_id} 를 찾을 수 없습니다."
    r = row.iloc[0]
    return (f"주문 {order_id}: 상품='{r['product_name']}', 상태='{r['status']}', "
            f"주문일={r['order_date']}, 수량={r['quantity']}")


# 교안2. 재고 조회 도구

# 재고 조회 도구
products = pd.read_csv(DATA / "products.csv")

@tool
def get_stock(product_name: str) -> str:
    """상품명으로 현재 재고 수량을 조회한다. 예: '무선 이어버드'"""
    # str.contains: 정확히 일치가 아니라 '포함'으로 찾는다(고객이 일부만 말해도 매칭)
    row = products[products["product_name"].str.contains(product_name.strip(), na=False)]
    if row.empty:
        return f"'{product_name}' 상품을 찾을 수 없습니다."
    r = row.iloc[0]
    return f"'{r['product_name']}' 재고: {r['stock']}개"

# 교안4. 도구 단독 테스트
print("=== 주문 상태 조회 도구 테스트 ===")
print(get_order_status.invoke({"order_id": "o000902"}))
print(get_stock.invoke({"product_name": "이어버드"}))

# 없는 경우도 테스트
print(get_order_status.invoke({"order_id": "x9999"}))   # 안전한 안내



# 교안1. 한 에이전트에 묶기
##############################################################
# 한 에이전트에 묶기
from langchain.agents import create_agent
from common import get_chat

# RAG 도구(문서) + DB 도구 2종(주문·재고)을 '같은 목록'에

tools = [build_policy_tool(), get_order_status, get_stock]
llm = get_chat( temperature=0)
agent = create_agent(
    llm,
    tools=tools,
    system_prompt=(
        "너는 승승장구몰 CS 에이전트다. 정책은 policy_search로 검색하고, "
        "주문 상태는 get_order_status, 재고는 get_stock으로 조회해 종합해 답하라."
    ),
)

# 교안2. 복합 질문 던지기
q = "어제 받은 이어버드 환불하고 싶은데 절차랑, 내 주문 O000902 상태 알려줘"
out = agent.invoke({"messages": [{"role": "user", "content": q}]})
for m in out["messages"]:
    m.pretty_print()
print("\n[최종 답변]\n", out["messages"][-1].content)

print("\n=== 에이전트 도구 사용 내역 ===")
print('agent:', agent)


