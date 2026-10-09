# 교안3. 코드 — 청킹 + 청크별 임베딩
import sys, pathlib
import numpy as np

sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# 1. 대소문자 정정 및 모듈 import
from common import get_embeddings, DOCS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 코사인 유사도 함수 정의
def cosine(a, b) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denom) if denom else 0.0

# ① 긴 문서 로드 (DOCS 경로 정정)
pdf_docs = PyPDFLoader(str(DOCS / "직원핸드북.pdf")).load()
full_text = "\n".join(d.page_content for d in pdf_docs)
print(f"전체 길이: {len(full_text):,}자")  # 매우 김!

# ② 청킹
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(pdf_docs)
chunk_texts = [c.page_content for c in chunks]

# ③ 청크별 임베딩 (OpenAI 배치 임베딩)
emb = get_embeddings()
chunk_vectors = emb.embed_documents(chunk_texts)  # 청크들을 한 번에 벡터화
store = list(zip(chunk_texts, chunk_vectors))     # (텍스트, 벡터) 쌍 보관
print(f"청크 {len(store)}개 벡터 보관\n")

# 교안4. 청크 검색
# ④ 청크 검색
user_q = "연차 휴가는 며칠까지 쓸 수 있나요?"
q_vec = emb.embed_query(user_q)

# 질문 벡터와 모든 청크 벡터의 유사도 계산
scores = [cosine(q_vec, v) for _, v in store]
order = np.argsort(scores)[::-1][:3]  # 상위 3개 인덱스

print(f"질문: {user_q}")
print("--- 검색 결과 Top 3 ---")
for rank, idx in enumerate(order, 1):
    text = chunk_texts[idx].replace("\n", " ")
    print(f"  {rank}. (유사도 {scores[idx]:.3f}) {text[:90]} ...")