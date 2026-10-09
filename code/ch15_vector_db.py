# 교안1. 여러 PDF 로드 → 청킹
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_embeddings, DOCS, DATA
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_and_chunk(filenames):
    """여러 PDF를 로드·청킹해 청크 리스트 반환."""
    docs = []
    for name in filenames:
        path = DOCS / name
        if not path.exists():
            raise SystemExit(f"[파일 없음] {path}")
        docs.extend(PyPDFLoader(str(path)).load())   # 여러 PDF를 한 리스트로 합침
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)          # 13강과 동일한 청킹
    print(f"문서 페이지: {len(docs)} / 청크: {len(chunks)}")
    return chunks

# 교안2. FAISS 인덱스 만들기
from langchain_community.vectorstores import FAISS

emb = get_embeddings()
chunks = load_and_chunk(["제품매뉴얼_로봇청소기.pdf", "제품매뉴얼_스마트워치.pdf"])

# 청크 임베딩 + FAISS 인덱스 적재 (여기서 임베딩 API 비용 발생!)
vs = FAISS.from_documents(chunks, emb)

# 교안3. similarity_search로 검색

query = "로봇청소기 물걸레 되나요?"
results = vs.similarity_search(query, k=3)   # 가장 가까운 청크 3개

print(f"[검색] {query}")
for i, d in enumerate(results, 1):
    src = d.metadata.get("source", "?").split("/")[-1]
    print(f"\n[{i}] (출처: {src} p.{d.metadata.get('page')})")
    print(d.page_content[:150], "...")

# ===============================================================
# 교안1. 인덱스 저장 — save_local
from common import DATA
INDEX_DIR = str(DATA / "faiss_index")   # 인덱스를 저장할 폴더

# [왜] 매 요청마다 PDF를 다시 임베딩하면 비용·지연이 폭발한다.
#      비싼 계산은 미리 해서 파일로 저장해 둔다.
vs.save_local(INDEX_DIR)
print("인덱스 저장 완료 →", INDEX_DIR)

# 교안2. 인덱스 재로드 — load_local
vs2 = FAISS.load_local(
    INDEX_DIR, emb,
    allow_dangerous_deserialization=True,   # pickle 역직렬화 허용
)
print("재로드 후 검색:", len(vs2.similarity_search("배터리 충전", k=2)), "건")

# 교안3. allow_dangerous_deserialization 주의
allow_dangerous_deserialization=True   # pickle 역직렬화 허용

# 교안4. 인덱싱과 서비스 분리 실습
# === build_index.py (배치 — 한 번만) ===
chunks = load_and_chunk(["제품매뉴얼_로봇청소기.pdf", "제품매뉴얼_스마트워치.pdf"])
vs = FAISS.from_documents(chunks, emb)   # 임베딩 (비쌈)
vs.save_local("faiss_index")             # 저장
# → 끝. 다시 실행할 필요 없음 (문서 바뀌기 전까지)