import sys, pathlib
import numpy as np

# 1. common.py 모듈을 불러올 수 있도록 현재 디렉터리를 모듈 경로에 추가
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# 2. common.py에서 OpenAI 임베딩 함수(get_embeddings) 및 경로(DATA) 임포트
from common import DATA, get_embeddings

# 3. OpenAI 임베딩 객체 초기화 (text-embedding-3-small)
emb = get_embeddings()


def cosine(a, b) -> float:
    """두 벡터 간의 코사인 유사도를 계산합니다."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denom) if denom else 0.0


# 4. 검증용 비교 문장 정의
# - 비슷한 의미 쌍 (긍정 평가)
pos1 = "배송도 빠르고 품질도 좋아서 만족합니다."
pos2 = "제품이 튼튼하고 배송이 신속해서 좋았어요."
# - 의미적으로 무관한 문장 (불만 사항)
neg = "사용 설명서가 영어로만 되어 있어 불편합니다."

# 5. 3개 문장을 단 1번의 OpenAI API 호출로 일괄 임베딩 (embed_documents)
v_pos1, v_pos2, v_neg = emb.embed_documents([pos1, pos2, neg])

# 6. 코사인 유사도 측정
sim_similar = cosine(v_pos1, v_pos2)     # 비슷한 의미 쌍 (긍정-긍정)
sim_unrelated = cosine(v_pos1, v_neg)    # 무관한 내용 쌍 (긍정-불만)

# 7. 결과 출력
print(f"비슷한 쌍 (긍정-긍정)  유사도: {sim_similar:.3f}")
print(f"무관한 쌍 (긍정-불만)  유사도: {sim_unrelated:.3f}")
print(f"→ 비슷한 쌍이 {'더 높음 ✓' if sim_similar > sim_unrelated else '낮음 ✗'}")