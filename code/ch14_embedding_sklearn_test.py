import sys, pathlib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA, get_embeddings

# 1. OpenAI 임베딩 로드 및 FAQ 데이터 준비
emb = get_embeddings()
df = pd.read_csv(DATA / "faq.csv")
questions = df["question"].tolist()

# 2. 전체 FAQ 문장 및 사용자 질문 임베딩 생성
doc_vectors = emb.embed_documents(questions)
user_q = "돈 언제 돌려받아요?"
q_vec = emb.embed_query(user_q)

# 3. 질문 1개 vs 전체 FAQ 유사도 행렬 계산 (scikit-learn)
sims = cosine_similarity([q_vec], doc_vectors)[0]

# 4. 유사도 내림차순 정렬 후 상위 3개 인덱스 추출
top_k = sims.argsort()[::-1][:3]

# 5. 결과 출력
print(f"질문: {user_q}\n")
print("Top-3 유사 FAQ:")
for rank, idx in enumerate(top_k, 1):
    print(f"  {rank}. ({sims[idx]:.3f}) {df.iloc[idx]['question']}")