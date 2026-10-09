import sys, pathlib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# 1. 스크립트 실행 위치와 관계없이 common.py를 불러올 수 있도록 모듈 검색 경로에 현재 폴더 추가
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# 2. common.py에서 OpenAI 임베딩 로드 함수(get_embeddings) 및 데이터 경로(DATA) 임포트
from common import DATA, get_embeddings

# 3. OpenAI 임베딩 객체 초기화 (text-embedding-3-small)
emb = get_embeddings()


def most_similar(query: str, docs: list[str], k: int = 3):
    """
    사용자 질의(query)와 문서 리스트(docs)를 OpenAI로 임베딩한 후,
    코사인 유사도가 가장 높은 상위 k개의 (유사도 점수, 문서) 튜플 리스트를 반환합니다.
    """
    # 3-1. 사용자 질의 단일 문장을 1차원 벡터로 변환 (embed_query)
    q_vec = emb.embed_query(query)

    # 3-2. 전체 문서 리스트를 한 번의 API 호출로 일괄 배치 임베딩 (embed_documents)
    doc_vecs = emb.embed_documents(docs)

    # 3-3. 질문 벡터([q_vec])와 문서 벡터들(doc_vecs) 간의 코사인 유사도 행렬 계산
    sims = cosine_similarity([q_vec], doc_vecs)[0]

    # 3-4. 유사도가 높은 순서대로 상위 k개의 인덱스 추출
    top_k = sims.argsort()[::-1][:k]

    # 3-5. (유사도 점수, 해당 문서 텍스트) 형태로 결과 구성하여 반환
    return [(float(sims[i]), docs[i]) for i in top_k]


if __name__ == "__main__":
    # 4. FAQ 데이터셋 읽어오기 (DATA 상수의 경로 활용)
    df = pd.read_csv(DATA / "faq.csv", encoding="utf-8-sig")
    questions = df["question"].tolist()

    # 5. 임베딩 기반 유사도 검색 수행
    user_query = "배송 얼마나 걸려요?"
    results = most_similar(user_query, questions, k=3)

    # 6. 검색 결과 출력
    print(f"질의: {user_query}\n")
    print("Top-3 유사 FAQ 질문:")
    for rank, (score, q) in enumerate(results, 1):
        print(f"  {rank}. ({score:.3f}) {q}")