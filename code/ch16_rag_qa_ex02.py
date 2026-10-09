import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DOCS, get_chat, get_embeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 문서 로드 및 인덱싱
docs = PyPDFLoader(str(DOCS / "제품매뉴얼_로봇청소기.pdf")).load()
chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)
retriever = FAISS.from_documents(chunks, get_embeddings()).as_retriever(search_kwargs={"k": 4})
llm = get_chat(temperature=0)

# 2. 프롬프트 설정
prompt = ChatPromptTemplate.from_template(
    "아래 [문서]만 근거로 답하라.\n[문서]\n{context}\n[질문] {question}\n[답변]"
)

# 3. 답변 생성 함수
def answer(q):
    docs = retriever.invoke(q)
    ctx = "\n\n".join(d.page_content for d in docs)
    return (prompt | llm | StrOutputParser()).invoke({"context": ctx, "question": q})

# 4. 정답 검증 세트 및 평가 실행
test_set = {
    "최대 흡입력은 몇 파스칼인가요?": "4000",
    "배터리 사용 시간은?": "120",
    "물탱크 용량은 몇 ml인가요?": "300",
}

passed = 0
for q, gold in test_set.items():
    result = answer(q)
    ok = gold in result.replace(",", "")
    print(f"[{'O' if ok else 'X'}] {q}\n    → {result[:60]} (정답:{gold})")
    passed += ok

print(f"\n통과: {passed}/{len(test_set)}")