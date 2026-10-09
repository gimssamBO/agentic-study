import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA, DOCS, get_embeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 저장 디렉터리 및 임베딩 객체 설정
index_dir = str(DATA / "faiss_index")
emb = get_embeddings()

def chunk_pdf(filename):
    """PDF 파일을 로드하여 500자 단위 청크로 나누는 헬퍼 함수"""
    docs = PyPDFLoader(str(DOCS / filename)).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_documents(docs)

# 1단계: 환불정책으로 최초 인덱싱 + 저장
print("=== 1단계: 환불교환정책 인덱스 생성 ===")
base_chunks = chunk_pdf("환불교환정책.pdf")
vs = FAISS.from_documents(base_chunks, emb)  # 환불 청크만 임베딩
vs.save_local(index_dir)
print("최초 인덱스 저장 완료\n")

# 증분 전 검색 테스트 (환불정책만 존재)
q = "vip 등급 조건은?"
before = vs.similarity_search(q, k=2)
print(f"질문: '{q}' [증분 전 검색 결과]")
for d in before:
    print(" -", d.page_content.replace("\n", " ")[:60], "...")
print("-" * 60)

# 2단계: 나중에 멤버십정책만 증분 추가 (서버 재시작 가정)
print("\n=== 2단계: 멤버십정책 증분 추가 ===")
vs2 = FAISS.load_local(index_dir, emb, allow_dangerous_deserialization=True)  # 기존 로드
new_chunks = chunk_pdf("멤버십정책.pdf")
vs2.add_documents(new_chunks)  # 새 청크만 임베딩해 덧붙임 (기존은 재계산 X!)
vs2.save_local(index_dir)      # 갱신된 인덱스 재저장
print("증분 저장 완료\n")

# 증분 후 검색 테스트 (멤버십 추가됨)
after = vs2.similarity_search(q, k=2)
print(f"질문: '{q}' [증분 후 검색 결과]")
for d in after:
    print(" -", d.page_content.replace("\n", " ")[:60], "...")
print("-" * 60)


# 멤버십을 추가한 뒤에도 환불 지식은 그대로 검색되는지 확인
q_refund = "환불은 며칠 걸리나요?"
keep = vs2.similarity_search(q_refund, k=2)
print(f"\n질문: '{q_refund}' [기존 지식 보존 여부]")
print("환불 관련 검색:", len(keep), "건")
for d in keep:
    print(" -", d.page_content.replace("\n", " ")[:60], "...")