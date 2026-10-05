import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DOCS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

docs = PyPDFLoader(str(DOCS / "환불교환정책.pdf")).load()

print(f"{'chunk_size':>12}{'청크 수':>10}{'평균 길이':>12}")
print("-" * 36)
for size in [200, 500, 1000]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=size // 10)
    chunks = splitter.split_documents(docs)
    avg = sum(len(c.page_content) for c in chunks) / len(chunks)
    print(f"{size:>12}{len(chunks):>10}{avg:>12.0f}")

print("\n[결론] 정책 문서는 조항이 짧으므로, 한 조항이 한 청크에 담기는")
print("       300~500자가 조항 단위 검색에 적합하다.")