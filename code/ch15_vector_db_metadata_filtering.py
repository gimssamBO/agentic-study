import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_embeddings, get_chat, DOCS, DATA
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

chroma_dir = str(DATA / "chroma_db")

# 교안2. metadata에 출처 보존
def load_and_chunk(filenames):
    """각 청크 metadata에 source(파일명)를 보존한다."""
    chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    for name in filenames:
        docs = PyPDFLoader(str(DOCS / name)).load()
        parts = splitter.split_documents(docs)
        # pypdfloader의 source는 전체 경로 → 필터 키로 쓰기 좋게 '파일명'으로 정규화
        for d in parts:
            d.metadata["source"] = name   # 예: "멤버십정책.pdf"
        chunks.extend(parts)
    return chunks

# 교안3. Chroma로 인덱싱
chunks = load_and_chunk(["환불교환정책.pdf", "멤버십정책.pdf", "직원핸드북.pdf"])
vs = Chroma.from_documents(chunks, get_embeddings(), persist_directory=chroma_dir)

# 교안4. 필터로 범위 좁히기
def search_in_doc(vs, query, source=None, k=3):
    """source 지정 시 해당 문서 안에서만, 미지정 시 전체에서 검색한다."""
    flt = {"source": source} if source else None
    return vs.similarity_search(query, k=k, filter=flt)

# ① 필터 없이 전체 검색 — 엉뚱한 문서가 섞일 수 있음
search_in_doc(vs, "vip 등급 혜택은?")
# ② 멤버십정책.pdf 안에서만 — 정확히 그 문서 청크만 후보
search_in_doc(vs, "vip 등급 혜택은?", source="멤버십정책.pdf")

# 교안5. 필터를 라우팅처럼 활용
# "연차 휴가" 질문 → 직원핸드북에서만
search_in_doc(vs, "연차 휴가는 며칠인가요?", source="직원핸드북.pdf")
# "환불" 질문 → 환불정책에서만
search_in_doc(vs, "환불 며칠 걸려요?", source="환불교환정책.pdf")

# 시안6. 필터 + LLM 답변
# docs = search_in_doc(vs, "vip 등급 혜택은?", source="멤버십정책.pdf", k=3)
docs = search_in_doc(vs, "연차 휴가는 며칠인가요?", source="직원핸드북.pdf", k=3)
context = "\n\n".join(d.page_content for d in docs)
llm = get_chat(temperature=0.0)
answer = llm.invoke(
    # f"아래 [문서]만 근거로 한국어로 답하라.\n\n[문서]\n{context}\n\n[질문] vip 등급 혜택은?"
    f"아래 [문서]만 근거로 한국어로 답하라.\n\n[문서]\n{context}\n\n[질문] 연차 휴가는 며칠인가요?"
).content
print(answer)