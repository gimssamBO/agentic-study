import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_embeddings

emb = get_embeddings()  # OpenAIEmbeddings (text-embedding-3-small)

v1 = emb.embed_query("환불")
v2 = emb.embed_query("돈 돌려받기")
v3 = emb.embed_query("로봇청소기")

# (다음 절에서 코사인 유사도로 비교하지만, 미리 감만)
# v1, v2는 비슷한 숫자 패턴, v3는 다른 패턴일 것
print("환불 앞 3개     :", [round(x, 4) for x in v1[:3]])
print("돈돌려받기 앞 3개:", [round(x, 4) for x in v2[:3]])   # v1과 비슷
print("로봇청소기 앞 3개:", [round(x, 4) for x in v3[:3]])   # v1과 다름