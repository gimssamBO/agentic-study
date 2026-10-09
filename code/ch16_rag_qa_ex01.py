import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DOCS, get_chat, get_embeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 인덱싱
docs = PyPDFLoader(str(DOCS / "환불교환정책.pdf")).load()
chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)
retriever = FAISS.from_documents(chunks, get_embeddings()).as_retriever(search_kwargs={"k": 4})
llm = get_chat(temperature=0)

# 2. 프롬프트 및 문서 포맷팅
prompt = ChatPromptTemplate.from_template(
    "아래 [문서]만 근거로 한국어로 정확히 답하라. 없으면 '찾을 수 없습니다'.\n\n"
    "[문서]\n{context}\n\n[질문] {question}\n[답변]"
)

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

# 3. 답변 생성 함수
def answer(question: str) -> dict:
    docs = retriever.invoke(question)
    text = (prompt | llm | StrOutputParser()).invoke(
        {"context": format_docs(docs), "question": question}
    )
    uniq, seen = [], set()
    for d in docs:
        src = d.metadata.get("source", "?").split("/")[-1]
        if src not in seen:
            seen.add(src)
            uniq.append(src)
    return {"answer": text, "sources": uniq}

# 4. 실행 테스트
if __name__ == "__main__":
    res = answer("제주 지역 반품 배송비는?")
    print("답변:", res["answer"])
    print("출처:", res["sources"])