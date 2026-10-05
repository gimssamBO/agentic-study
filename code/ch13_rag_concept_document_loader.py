import sys, pathlib
# 현재 디렉토리를 모듈 검색 경로에 추가하여 common 참조 가능하게 처리
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA

# 교안 2. CSVLoader — 한 행 = 한 Document
from langchain_community.document_loaders import CSVLoader

try:
    loader = CSVLoader(file_path=str(DATA / "faq.csv"), encoding="utf-8-sig")
    csv_docs = loader.load()
    # faq.csv의 각 행(faq_id, question, answer)이 Document 객체 하나가 됨
except Exception as e:
    print("CSVLoader 사용 불가:", e)
    csv_docs = []

# 교안 3. TextLoader — 일반 텍스트
from langchain_community.document_loaders import TextLoader
try:
    # 경로가 DATA 내부인지 확인 후 적절히 지정
    text_docs = TextLoader(str(DATA / "notice.txt"), encoding="utf-8").load()
except Exception as e:
    print("TextLoader 사용 불가:", e)
    text_docs = []

# 시안 4. MarkdownHeaderTextSplitter — 마크다운
from langchain_text_splitters import MarkdownHeaderTextSplitter

markdown = (
    "# 환불 정책\n구매 후 7일 이내 단순 변심 환불이 가능합니다.\n"
    "# 교환 정책\n상품 불량 시 무상 교환해 드립니다."
)
# 마크다운 헤더 기반 스플리터 초기화
splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "섹션")])
md_docs = splitter.split_text(markdown)
# "# 환불 정책" 섹션과 "# 교환 정책" 섹션이 각각 Document로 분할됨


# 시안 5. 핵심 — 모두 같은 Document 구조
def show_docs(title, docs):
    print(f"\n=== {title} ===")
    if not docs:
        print("문서가 비어있습니다.")
        return
    for d in docs[:2]:
        print("page_content:", d.page_content[:80].replace("\n", " "))
        print("metadata    :", d.metadata)


# 출력 테스트 (PDF, CSV, 텍스트, 마크다운 모두 page_content + metadata 구조를 가짐)
show_docs("CSV 문서", csv_docs)
show_docs("텍스트 문서", text_docs)
show_docs("마크다운 문서", md_docs)