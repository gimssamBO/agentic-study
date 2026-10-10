import pathlib
import sys
import pandas as pd

# 1. 경로 설정 및 대문자 경로 상수 사용
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA, DOCS, get_chat, get_embeddings

# 2. 필수 라이브러리 모듈 임포트
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import create_retriever_tool, tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 최신 LangChain 표준 임포트 (경고 문구 해결)
from langchain.agents import create_agent

# 3. 데이터 로드 및 month 컬럼 추가 (%y-%m 형태: 예 '26-05')
orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")
orders["month"] = pd.to_datetime(orders["order_date"]).dt.strftime("%y-%m")

# 4. RAG 도구 (멤버십 정책 문서 인덱싱)
policy_docs = PyPDFLoader(str(DOCS / "멤버십정책.pdf")).load()
chunks = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50
).split_documents(policy_docs)
retriever = FAISS.from_documents(chunks, get_embeddings()).as_retriever(
    search_kwargs={"k": 4}
)
policy_tool = create_retriever_tool(
    retriever,
    "policy_search",
    "멤버십 등급·적립률 등 정책 문서 검색. 정책 질문에 사용.",
)

# 5. Pandas 코드 실행 도구 (안전성 강화 및 예시 명시)
@tool
def run_pandas(expr: str) -> str:
    """주문 데이터 분석 도구.
    사용 가능 변수: orders (컬럼: month, status, amount, order_date ...), pd
    예시 표현식: orders[(orders['month']=='26-05') & (~orders['status'].isin(['취소', '환불']))]['amount'].sum()
    """
    try:
        # 따옴표나 공백 정제 후 eval 실행
        clean_expr = expr.strip().strip("`").strip()
        result = eval(clean_expr, {"__builtins__": {}}, {"orders": orders, "pd": pd})
        return str(result)
    except Exception as e:
        return f"실행 오류: {e}. 올바른 파이썬 pandas 표현식만 입력하세요."

# 6. 에이전트 생성 (create_agent 적용 및 시스템 프롬프트 구체화)
llm = get_chat(temperature=0)
prompt_text = (
    "너는 승승장구몰 CS 에이전트다.\n"
    "1. 멤버십 등급 및 적립률 정보는 반드시 policy_search 도구로 검색하라.\n"
    "2. 매출 계산은 run_pandas 도구를 사용하되, month 컬럼 형식은 '26-05'와 같은 '%y-%m' 형태임을 명심하라.\n"
    "3. 두 결과를 종합하여 정확한 최종 금액과 함께 한글로 답하라."
)

agent = create_agent(
    model=llm,
    tools=[policy_tool, run_pandas],
    system_prompt=prompt_text
)

# 7. 질의 실행
if __name__ == "__main__":
    q = "VIP 적립률이 얼마고, 그걸 2026-05 총매출(취소/환불 제외)에 적용하면 적립금은?"
    print("에이전트 실행 중...")
    out = agent.invoke({"messages": [{"role": "user", "content": q}]})

    # 8. 최종 답변 출력
    print("\n=== 최종 답변 ===")
    print(out["messages"][-1].content)