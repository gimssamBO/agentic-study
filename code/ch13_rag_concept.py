# 실행: python code/ch13_rag_concept.py


import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DOCS            # DOCS = data/docs 폴더 경로

# PyPDFLoader: PDF를 페이지 단위 Document(본문+메타데이터)로 읽어 오는 로더
from langchain_community.document_loaders import PyPDFLoader

pdf_path = DOCS / "환불교환정책.pdf"
loader = PyPDFLoader(str(pdf_path))
docs = loader.load()           # 페이지 단위 Document 리스트


print("로드한 페이지 수:", len(docs))
print("첫 페이지 메타데이터:", docs[0].metadata)
print("첫 페이지 내용 일부:")
print(docs[0].page_content[:200])
print()
print('두 번째 페이지 내용 일부:')
print(docs[0].page_content[:50])


# RecursiveCharacterTextSplitter: 긴 문서를 적당한 크기 조각(청크)으로 나누는 도구
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # 한 조각 최대 500자
    chunk_overlap=50,    # 인접 조각 50자 겹침(경계에 걸친 맥락 보존)
)


# split_documents: 원본 metadata(page 등)를 각 청크에 복사해 출처 추적이 가능하다
chunks = splitter.split_documents(docs)   # docs는 05번에서 로드한 Document 리스트

print("청크 개수:", len(chunks))
print("첫 청크 길이:", len(chunks[0].page_content))
print("첫 청크 내용:")
print(chunks[0].page_content)
print("첫 청크 메타데이터:", chunks[0].metadata)



print();print();print()
# [한계] 지금은 단어가 똑같이 들어간 청크만 찾는다. "돈 돌려받기"로는 못 찾는다.
keyword = "환불"
hits = [c for c in chunks if keyword in c.page_content]
print(f"'{keyword}'을 포함한 청크: {len(hits)}개")
for i, c in enumerate(hits[:2], 1):
    print(f"\n[{i}] (page {c.metadata.get('page')})")
    print(c.page_content[:120], "...")

