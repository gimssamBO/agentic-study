import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_embeddings

emb = get_embeddings()   # GoogleGenerativeAIEmbeddings (gemini-embedding-001, 768차원)
v = emb.embed_query("환불은 며칠 걸려요?")   # 문장 한 개 → 벡터


print("벡터 차원:", len(v))     # 768
print("앞 5개 값:", v[:5])

import pandas as pd
from common import DATA
import numpy as np

df = pd.read_csv(DATA / "faq.csv")
questions = df["question"].tolist()   # FAQ 질문 10개

# 여러 문장을 '한 번에' 변환 → 요청 수·비용 절감 (백엔드 기본기)
doc_vectors = emb.embed_documents(questions)
print("임베딩한 FAQ 수:", len(doc_vectors))      # 10
print("벡터 차원:", len(doc_vectors[0]))          # 768


user_q = "돈 언제 돌려받아요?"   # '환불'이라는 단어가 전혀 없다!
q_vec = emb.embed_query(user_q)   # 질문 한 개는 embed_query로

def cosine(a, b) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denom) if denom else 0.0

# 질문 벡터 vs 각 FAQ 벡터의 코사인 유사도를 모두 계산
scores = [cosine(q_vec, dv) for dv in doc_vectors]
best = int(np.argmax(scores))   # 유사도가 가장 높은 FAQ의 인덱스

print(f"질문: {user_q}")
print(f"가장 비슷한 FAQ(유사도 {scores[best]:.3f}):")
print("  Q:", df.iloc[best]["question"])
print("  A:", df.iloc[best]["answer"])