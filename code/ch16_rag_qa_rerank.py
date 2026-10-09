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

# 추가 요청된 폴백 프롬프트
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


# =====================================================================
# Rerank 관련 코드 추가 파트
# =====================================================================

def get_retriever(k=4):
    """지정한 k값으로 retriever 반환."""
    vs = FAISS.load_local('./data/faiss_index2', get_embeddings(), allow_dangerous_deserialization=True)
    return vs.as_retriever(search_kwargs={"k": k})

def _parse_score(text: str) -> int:
    """점수 파싱 보조 함수"""
    import re
    match = re.search(r'\d+', str(text))
    return int(match.group()) if match else 0

question = "환불 며칠 걸려?"
small = get_retriever(2).invoke(question)   # k=2: 적게
large = get_retriever(6).invoke(question)   # k=6: 많이
print(f"k=2: {len(small)}건 / k=6: {len(large)}건")

def rerank(question, docs, top_n=2):
    """검색된 청크들을 llm이 질문 관련도(0~10)로 채점해 상위 top_n만 재선택한다."""
    llm = get_chat(temperature=0.0)
    scored = []
    for d in docs:
        prompt = (
            "다음 [문서조각]이 [질문]에 답하는 데 얼마나 관련 있는지 0~10 정수로만 답하라.\n"
            "오직 숫자 하나만 출력하라(설명 금지).\n\n"
            f"[질문] {question}\n\n[문서조각]\n{d.page_content[:400]}\n\n[점수]"
        )
        score = _parse_score(llm.invoke(prompt).content)
        scored.append((score, d))
    scored.sort(key=lambda x: x[0], reverse=True)   # 점수 내림차순
    return scored[:top_n]                           # 상위 top_n

# Rerank 테스트 실행
top_docs = rerank(question, large, top_n=2)
print(f"Rerank 최종 상위 {len(top_docs)}개 선택 완료")
for score, doc in top_docs:
    print(f"- 점수: {score}점 | 본문: {doc.page_content[:50]}...")