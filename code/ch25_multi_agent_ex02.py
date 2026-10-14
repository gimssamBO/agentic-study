# -*- coding: utf-8 -*-
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from ch25_multi_agent_ex01 import route_rule3      # 문제 1의 3-way 규칙 라우터 재사용

# (질문, 기대 route) — 각 에이전트당 2개씩 6개
testset = [
    ("전자기기 추천해줘", "sales"),
    ("선물용 좋은 거 골라줘", "sales"),
    ("환불 며칠 이내에 해야 해?", "policy"),
    ("무료배송 기준이 뭐야?", "policy"),
    ("경쟁사랑 비교해줘", "competitor"),
    ("타사 대비 우리 강점이 뭐야?", "competitor"),
]

def evaluate():
    correct = 0
    wrong = []
    for q, gold in testset:
        pred = route_rule3(q)
        if pred == gold:
            correct += 1
        else:
            wrong.append((q, gold, pred))
    n = len(testset)
    print(f"정확도: {correct}/{n} ({correct/n*100:.0f}%)")
    if wrong:
        print("\n[오분류]")
        for q, gold, pred in wrong:
            print(f"  '{q}' → 기대 {gold}, 실제 {pred}")
    else:
        print("모두 정확히 분류됨 ✅")

if __name__ == "__main__":
    evaluate()