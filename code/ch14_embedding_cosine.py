import numpy as np

def cosine(a, b) -> float:
    """두 벡터의 코사인 유사도(-1 ~ 1). 1에 가까울수록 의미가 비슷하다."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)   # 분모 = 각 벡터 길이의 곱
    return float(a @ b / denom) if denom else 0.0   # a @ b = 내적

print(cosine([1, 0], [0, 1]))   # 0.0 (직교)
print(cosine([1, 0], [1, 0]))   # 1.0 (같은 방향)
print(cosine([1, 0], [-1, 0]))  # -1.0 (반대 방향)
print(cosine([1, 0], [1, 1]))   # 0.707 (45도)