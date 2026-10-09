import sys, pathlib

# 1. common 모듈 참조 경로 설정 (Path 대문자 정정)
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# 2. 대문자 경로 상수 DATA 및 OpenAI 임베딩 함수 임포트
from common import DATA, get_embeddings
from langchain_community.vectorstores import FAISS

# 저장된 FAISS 인덱스 경로 설정
index_dir = str(DATA / "faiss_index" / "membership")

if __name__ == "__main__":
    emb = get_embeddings()

    # 저장된 인덱스 로드 (FAISS 클래스명 및 True 대문자 정정)
    vs = FAISS.load_local(
        index_dir,
        emb,
        allow_dangerous_deserialization=True,  # 로컬에 저장된 신뢰할 수 있는 pkl 파일 로드 허용
    )
    print("인덱스 로드 완료 (재임베딩 없이 빠른 로딩)")

    # 검색 수행
    query = "vip 적립률"
    results = vs.similarity_search(query, k=2)

    print(f"\n[검색] {query}")
    for i, d in enumerate(results, 1):
        clean_text = d.page_content.replace("\n", " ")
        print(f"[{i}] {clean_text[:80]} ...")