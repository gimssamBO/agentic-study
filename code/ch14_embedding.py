import sys, pathlib
import pandas as pd
import numpy as np

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA, get_embeddings

# 1. OpenAI 임베딩 객체 로드 (text-embedding-3-small)
emb = get_embeddings()  # OpenAIEmbeddings (text-embedding-3-small)

# 단일 문장 벡터 변환
v = emb.embed_query("환불은 며칠 걸려요?")

print("벡터 차원:", len(v))       # 512 (또는 기본 1536)
print("앞 5개 값:", [round(x, 4) for x in v[:5]])

# 2. FAQ 데이터 로드
df = pd.read_csv(DATA / "faq.csv")
questions = df["question"].tolist()   # FAQ 질문 리스트

# 여러 문장을 한 번에 변환 (API 요청 수 및 토큰 비용 절감)
doc_vectors = emb.embed_documents(questions)
print("임베딩한 FAQ 수:", len(doc_vectors))       # 10
print("벡터 차원:", len(doc_vectors[0]))          # 512 (또는 기본 1536)

# 3. 유사도 검색 테스트
user_q = "돈 언제 돌려받아요?"   # '환불'이라는 단어가 직접 들어있지 않은 유의어 질문
q_vec = emb.embed_query(user_q)

def cosine(a, b) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denom) if denom else 0.0

# 코사인 유사도 계산 및 가장 가까운 FAQ 매칭
scores = [cosine(q_vec, dv) for dv in doc_vectors]
best = int(np.argmax(scores))

print(f"\n질문: {user_q}")
print(f"가장 비슷한 FAQ (유사도 {scores[best]:.3f}):")
print("  Q:", df.iloc[best]["question"])
print("  A:", df.iloc[best]["answer"])