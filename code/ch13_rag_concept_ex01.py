import sys, pathlib
import warnings

# DeprecationWarning 경고 차단
warnings.filterwarnings("ignore", category=DeprecationWarning)

# pathlib.Path 대소문자 정정
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# DOCS 경로 변수 및 PyPDFLoader 대소문자 정정
from common import DOCS
from langchain_community.document_loaders import PyPDFLoader

def chunk_text(text: str, size: int = 500, overlap: int = 50):
    """글자 수 기준으로 자르되 overlap만큼 겹치게 청크 리스트를 반환한다."""
    chunks = []
    start = 0
    # &lt; 문자를 파이썬 부등호 < 로 수정
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap      # 다음 시작점을 overlap만큼 뒤로 (겹침 발생)
    return chunks

if __name__ == "__main__":
    # DOCS 경로와 PyPDFLoader 사용으로 정정
    pdf_docs = PyPDFLoader(str(DOCS / "직원핸드북.pdf")).load()
    full_text = "\n".join(d.page_content for d in pdf_docs)

    chunks = chunk_text(full_text, size=500, overlap=50)
    print(f"전체 글자 수: {len(full_text)}")
    print(f"청크 개수: {len(chunks)}")

    # &gt;= 문자를 파이썬 부등호 >= 로 수정
    if len(chunks) >= 2:
        tail = chunks[0][-50:]            # 첫 청크 끝 50자
        head = chunks[1][:50]             # 둘째 청크 시작 50자
        print(f"겹침 일치: {tail == head}")   # True 면 성공