import sys, pathlib

# 1. common 모듈 참조를 위한 경로 추가 (Path 대문자 정정)
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# 2. 필요한 함수 및 대문자 경로 상수(DATA, DOCS) 임포트
from common import DATA, DOCS, get_embeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# FAISS 인덱스 저장 경로 설정 (DATA 상수를 상위 디렉터리로 활용)
index_dir = str(DATA / "faiss_index" / "membership")

if __name__ == "__main__":
    # 3. PDF 로드 및 청킹 (PyPDFLoader, RecursiveCharacterTextSplitter 대문자 정정)
    loaded_docs = PyPDFLoader(str(DOCS / "멤버십정책.pdf")).load()
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50
    ).split_documents(loaded_docs)

    print(f"페이지 {len(loaded_docs)}장 → 청크 {len(chunks)}개 변환 완료")

    # 4. OpenAI 임베딩 및 FAISS 인덱스 생성
    emb = get_embeddings()
    vs = FAISS.from_documents(chunks, emb)

    # 5. 로컬 디렉터리에 인덱스 및 메타데이터 저장
    vs.save_local(index_dir)
    print(f"인덱스 저장 완료 → {index_dir}")
    print("저장된 파일: index.faiss (벡터 데이터), index.pkl (직렬화된 텍스트/메타데이터)")