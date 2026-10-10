import pathlib
import sys

# 1. pathlib.path -> pathlib.Path 및 DOCS 대문자 상수 교정
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DOCS, get_chat, get_embeddings

# 2. 모듈 및 클래스명 대소문자(PascalCase) 교정
from langchain.agents import create_agent
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import create_retriever_tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 핸드북 인덱싱 (docs 상수와 변수명 충돌 방지를 위해 loaded_docs 사용)
loaded_docs = PyPDFLoader(str(DOCS / "직원핸드북.pdf")).load()
chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(loaded_docs)
vs = FAISS.from_documents(chunks, get_embeddings())   # 1회 생성, 공유

def make_agent(description):
    tool = create_retriever_tool(vs.as_retriever(search_kwargs={"k": 4}),
                                 name="search_tool", description=description)
    return create_agent(get_chat(temperature=0), tools=[tool],
                        system_prompt="너는 승승장구몰 상담원이다.")

def used_search(agent, q):
    out = agent.invoke({"messages": [{"role": "user", "content": q}]})
    # none -> None 오타 교정
    return any(getattr(m, "tool_calls", None) for m in out["messages"])

q = "연차 휴가 며칠이야?"
print(f"[모호한 description 'search'] 검색함? {used_search(make_agent('search'), q)}")
print(f"[명확한 description] 검색함? {used_search(make_agent('승승장구몰 직원 인사·복지·휴가 규정을 검색한다. 휴가·근무 규정 질문에 사용.'), q)}")