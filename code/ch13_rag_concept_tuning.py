import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# 1. 대소문자 정확히 표기하여 import
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from common import DOCS  # 경로 변수명 확인 (보통 대문자 DOCS 사용)

# 2. PyPDFLoader 인스턴스화 (대소문자 수정)
# DOCS 경로 내 환불교환정책.pdf 로드
loader = PyPDFLoader(str(DOCS / "환불교환정책.pdf"))
docs = loader.load()

keyword = "환불"   # 검색 명중률 비교용 키워드

# 비교할 (chunk_size, chunk_overlap) 설정값 조합
configs = [(300, 0), (500, 50), (1000, 100)]

print(f"{'설정(size,overlap)':<22}{'청크수':>8}{'평균길이':>10}{'키워드포함':>12}")
print("-" * 55)

for size, overlap in configs:
    # 3. RecursiveCharacterTextSplitter 생성 (대소문자 수정)
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    chunks = splitter.split_documents(docs)
    
    n = len(chunks)
    avg_len = sum(len(c.page_content) for c in chunks) / n if n else 0
    hits = sum(1 for c in chunks if keyword in c.page_content)
    
    print(f"({size:<4}, {overlap:<3}){'':<10}{n:>8}{avg_len:>10.0f}{hits:>12}")