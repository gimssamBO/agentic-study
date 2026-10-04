import sys, pathlib, json
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL, DATA
import pandas as pd
from collections import Counter
# (classify 함수와 FEWSHOT 은 OpenAI 버전과 동일 — 재사용)
CATEGORIES = ["배송", "환불", "교환", "결제", "상품문의", "칭찬", "불만"]

FEWSHOT = """다음 고객 문의를 아래 7개 중 정확히 하나로 분류하라.
카테고리: 배송 / 환불 / 교환 / 결제 / 상품문의 / 칭찬 / 불만
카테고리 이름 한 단어만 출력하라(다른 말 금지).

[예시]
문의: 반품하면 배송비는 누가 부담하나요?           → 환불
문의: 색상이 사진과 달라요. 다른 색으로 바꿔주세요.  → 교환
문의: 상담원분이 정말 친절하셨어요. 감사합니다.      → 칭찬
문의: 카드가 두 번 청구됐어요.                      → 결제
"""
def classify(content: str) -> str:
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": f"{FEWSHOT}\n[분류할 문의]\n문의: {content} →"}
        ],
        temperature=0,
    )
    out = resp.choices[0].message.content.strip()
    for c in CATEGORIES:
        if c in out:
            return c
    return "기타"

client = get_openai_client()

df = pd.read_csv(DATA / "cs_inquiries.csv", encoding="utf-8-sig")
df["pred"] = df["content"].apply(classify)

correct = (df["pred"] == df["category_hint"]).sum()
print(f"전체 정확도: {correct/len(df):.1%}  ({correct}/{len(df)})")

# [핵심] 틀린 케이스만 모아서 '왜 틀렸나'를 사람이 읽을 수 있게 출력
wrong = df[df["pred"] != df["category_hint"]]
print(f"틀린 케이스: {len(wrong)}건")
for i, (_, r) in enumerate(wrong.iterrows(), 1):
    print(f"[{i}] 정답={r['category_hint']} / 예측={r['pred']}")
    print(f"     내용: {r['content']}")
# [왜] 혼동쌍을 집계하면 '어느 경계가 약한가'가 한눈에 보인다
confusion = Counter(
    (r["category_hint"], r["pred"]) for _, r in wrong.iterrows()
)
print("혼동쌍 집계 (정답 → 예측, 많은 순):")
for (gold, pred), cnt in confusion.most_common():
    print(f"  {gold} → {pred} : {cnt}건")
    
# 약한 경계(환불 vs 결제, 불만 vs 상품문의)를 콕 집은 예시 추가
FEWSHOT_PLUS = FEWSHOT + """문의: 결제는 됐는데 환불은 언제 되나요?       → 환불
문의: 결제창에서 자꾸 오류가 나요.              → 결제
문의: 배송이 자꾸 늦어서 너무 불편해요.         → 불만
문의: 이 제품 방수 되나요?                      → 상품문의
"""    