import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DOCS, get_chat, get_embeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 교안1. 인덱싱 — 두 문서 통합 retriever
def build_retriever():
    """정책 문서 2개를 통합 인덱싱한 retriever 반환."""
    docs = []
    for f in ["환불교환정책.pdf", "멤버십정책.pdf"]:
        docs.extend(PyPDFLoader(str(DOCS / f)).load())   # 두 문서를 한 인덱스로
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50).split_documents(docs)
    vs = FAISS.from_documents(chunks, get_embeddings())
    # as_retriever: 벡터스토어를 'k개를 찾아 주는 검색 객체'로 변환
    vs.save_local('./data/faiss_index2')
    return vs.as_retriever(search_kwargs={"k": 4})

# 교안2. retriever란?
retriever = build_retriever()
docs = retriever.invoke("환불 며칠 걸려?")   # 질문 → 관련 청크 4개

# 교안3. 프롬프트와 format_docs
PROMPT = ChatPromptTemplate.from_template(
    "너는 승승장구몰 CS 상담원이다.\n"
    "아래 [문서] 내용만 근거로 한국어로 정확히 답하라.\n"
    "문서에 없는 내용은 추측하지 말고 '제공된 문서에서 찾을 수 없습니다'라고 답하라.\n\n"
    "[문서]\n{context}\n\n[질문] {question}\n\n[답변]"
)

# 추가 요청된 폴백 프롬프트 (ChatPromptTemplate 대소문자 교정)
prompt_with_fallback = ChatPromptTemplate.from_template(
    "너는 승승장구몰 cs 상담원이다.\n"
    "아래 [문서] 내용만 근거로 답하라.\n"
    "문서에 없으면 '해당 내용은 확인이 어렵습니다. 고객센터(1588-0000)로 문의해 주세요'라고 답하라.\n\n"
    "[문서]\n{context}\n\n[질문] {question}\n\n[답변]"
)

def format_docs(docs):
    """검색된 Document들의 본문을 한 덩어리 문자열(context)로 합친다."""
    return "\n\n".join(d.page_content for d in docs)

# 교안4. LCEL 체인 조립
llm = get_chat(temperature=0)   # temperature=0: 같은 질문에 일관된 답(재현성)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | PROMPT
    | llm
    | StrOutputParser()
)
print(rag_chain.invoke("환불 며칠 걸려?"))


# 교안1. 서비스 객체는 1회만 생성
# 서비스 객체는 1회만 생성해 재사용
_retriever = None
_llm = None

def _ensure():
    """retriever·llm을 최초 1회만 생성(지연 초기화). 이후는 재사용."""
    global _retriever, _llm
    if _retriever is None:
        _retriever = build_retriever()
        _llm = get_chat(temperature=0)

# 교안2. answer 함수
def answer(question: str) -> dict:
    """질문 -> {answer, sources}. FastAPI/Flask 핸들러에서 그대로 return 가능."""
    _ensure()
    docs = _retriever.invoke(question)   # ① 검색: 근거 청크 확보 (docs 보관!)
    context = format_docs(docs)          # ② 조립: 청크를 context 문자열로
    # ③ 생성: 프롬프트 | LLM | 파서를 LCEL로 한 번에 실행
    text = (PROMPT | _llm | StrOutputParser()).invoke(
        {"context": context, "question": question}
    )
    # ④ 출처 추출 + 중복 제거 (04번)
    uniq, seen = [], set()
    for d in docs:
        src = d.metadata.get("source", "?").split("/")[-1]
        page = d.metadata.get("page")
        key = (src, page)
        if key not in seen:
            seen.add(key)
            uniq.append({"source": src, "page": page})
    return {"answer": text, "sources": uniq}

# 교안3. 실행
res = answer("VIP 등급 조건은?")
print("답변:", res["answer"])
print("출처:")
for s in res["sources"]:
    print(f"  - {s['source']} p.{s['page']}")


# 테스트 케이스 실행
test_cases = [
    ("환불 며칠 걸려?", "3일"),           # 문서에 있음 → "3일" 포함해야
    ("당일 새벽배송 되나요?", "찾을 수 없"),  # 문서에 없음 → "찾을 수 없" 포함해야
]
passed = sum(1 for q, expected in test_cases if expected in answer(q)["answer"])
print(f"통과: {passed}/{len(test_cases)}")