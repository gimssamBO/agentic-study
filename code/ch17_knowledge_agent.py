import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, get_embeddings, DOCS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

def build_retriever():
    """환불정책+핸드북+멤버십을 하나의 인덱스로 통합."""
    files = ["환불교환정책.pdf", "직원핸드북.pdf", "멤버십정책.pdf"]
    docs = []
    for f in files:
        docs.extend(PyPDFLoader(str(DOCS / f)).load())   # 세 문서를 한 인덱스로
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50).split_documents(docs)
    vs = FAISS.from_documents(chunks, get_embeddings())
    return vs.as_retriever(search_kwargs={"k": 4})



from langchain_core.tools.retriever import create_retriever_tool

retriever = build_retriever()
# [핵심] description이 라우팅 규칙 — 에이전트는 이 설명을 읽고 "언제 검색할지" 판단
policy_tool = create_retriever_tool(
    retriever,
    name="company_policy_search",
    description="승승장구몰 환불/교환/멤버십/직원 규정 사내 문서를 검색한다. "
                "정책·규정·등급·반품·휴가 등 회사 규정 관련 질문에 사용하라.",
)



from langchain.agents import create_agent

llm = get_chat( temperature=0)
agent = create_agent(
    llm,
    tools=[policy_tool],
    system_prompt="너는 승승장구몰의 친절한 상담원이다. 회사 규정은 반드시 도구로 검색해 답하라.",
)


def ask(q):
    out = agent.invoke({"messages": [{"role": "user", "content": q}]})
    msgs = out["messages"]
    # tool_calls가 하나라도 있으면 = 검색 도구를 호출했다는 뜻
    used = any(getattr(m, "tool_calls", None) for m in msgs)
    return msgs[-1].content, used   # (최종 답변, 도구 사용 여부)


# 일상 질문 — 검색하지 않음 =>pdf에서 검색하지 않음
ans, used = ask("안녕하세요! 오늘 기분 어때요?")
print("답변:", ans)
print("검색 도구 사용?", used)

# 정책 질문 — 검색함 => pdf 에서 검색함
ans, used = ask("단순 변심으로 반품하면 배송비는 누가 부담하나요?")
print("답변:", ans)
print("검색 도구 사용?", used)



