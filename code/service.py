
from langchain_community.vectorstores import FAISS
from common import get_embeddings, DOCS, DATA

emb = get_embeddings('openai')

# === service.py (서버 — 기동 시 1회 로드, 요청마다 검색) ===
vs = FAISS.load_local(str(DATA / "faiss_index"), emb, allow_dangerous_deserialization=True)  # 1회
def search(question):
    return vs.similarity_search(question, k=3)   # 요청마다 (빠름, 공짜)

query = '로봇청소기에는 물걸레가 있습니까?'
results = search(query)
print(f'[검색]  {query}')

for i, d in enumerate(results, 1):
    src = d.metadata.get("source", "?").split("/")[-1]
    print(f"\n[{i}] (출처: {src} p.{d.metadata.get('page')})")
    print(d.page_content[:150], "...")
    


