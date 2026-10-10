import pathlib
import sys

# 1. pathlib.path -> pathlib.Path 교정 및 DOCS 대문자 상수 수용
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DOCS, get_chat, get_embeddings

# 2. 클래스 및 모듈명 대소문자(PascalCase) 교정
from langchain.agents import create_agent
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import create_retriever_tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 핸드북 인덱싱 (docs 경로 상수 사용 및 PyPDFLoader, RecursiveCharacterTextSplitter, FAISS 교정)
pdf_docs = PyPDFLoader(str(DOCS / "직원핸드북.pdf")).load()
chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(pdf_docs)
retriever = FAISS.from_documents(chunks, get_embeddings()).as_retriever(search_kwargs={"k": 4})

# retriever를 도구로 (create_retriever_tool 표준 위치 적용)
handbook_tool = create_retriever_tool(
    retriever,
    name="employee_handbook_search",
    description="승승장구몰 직원핸드북(인사·복지·휴가 규정)을 검색한다. 연차·휴가·근무 규정 질문에 사용."
)

# create_agent 호출 (요청하신 구문/구조 100% 유지)
agent = create_agent(
    get_chat(temperature=0),
    tools=[handbook_tool],
    system_prompt="너는 인사 담당자다. 규정은 반드시 도구로 검색해 답하라."
)

# 실행 및 메시지 출력 (none -> None 오타 교정)
out = agent.invoke({"messages": [{"role": "user", "content": "연차 며칠이야?"}]})

for m in out["messages"]:
    m.pretty_print()

print("\n검색 사용?", any(getattr(m, "tool_calls", None) for m in out["messages"]))