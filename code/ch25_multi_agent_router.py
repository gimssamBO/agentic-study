# -*- coding: utf-8 -*-
import sys, pathlib
# 1. code/ 디렉터리 모듈 참조 설정
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "code"))
from common import get_chat, DATA
from ch25_multi_agent import route_rule, route_llm, build_agents   # 두 라우터 재사용

# [핵심] 라우팅은 '정답이 있는 분류 문제' → 정답 라벨을 붙이면 정확도를 잴 수 있다.
testset = [
    ("환불은 며칠 안에 신청해야 해?", "policy"),     # 키워드 '환불' → 규칙도 맞춤
    ("무료배송 기준이 어떻게 돼?", "policy"),          # '무료배송'
    ("포인트 적립은 언제 돼?", "policy"),              # '적립/포인트'
    ("교환하려면 어떻게 해?", "policy"),               # '교환'
    ("전자기기 추천 좀 해줘", "sales"),                # 명확한 추천
    ("패션의류 인기상품 뭐 있어?", "sales"),           # 명확한 추천
    ("선물용으로 좋은 거 골라줘", "sales"),             # 키워드 없음 → 규칙은 sales(기본)로 맞음
    ("가성비 좋은 거 없을까?", "sales"),               # 애매 — 규칙은 sales(기본)로 우연히 맞음
    ("주문한 거 무를 수 있어?", "policy"),             # '취소' 동의어 → 규칙이 놓치기 쉬움
    ("이거 며칠이면 받아볼 수 있어?", "policy"),       # 배송 의미지만 '배송' 단어 없음 → 규칙 한계
]

def evaluate():
    """두 라우터를 같은 질문셋에 돌려 정확도와 llm 호출 횟수를 집계한다."""
    llm, _, _ = build_agents()   # route_llm 에 넘길 분류용 llm

    rule_correct = llm_correct = 0
    rule_calls = 0   # 규칙 라우터의 llm 호출 횟수(항상 0이어야 함)
    llm_calls = 0    # llm 라우터의 호출 횟수(질문당 1회)

    print(f"  {'질문':<26} | 정답  | 규칙   | llm")
    print("  " + "-" * 56)
    for q, gold in testset:
        r = route_rule(q)            # llm 호출 없음 → rule_calls 증가 안 함
        l = route_llm(llm, q)        # 질문당 llm 1회
        llm_calls += 1

        rule_ok, llm_ok = (r == gold), (l == gold)
        rule_correct += rule_ok
        llm_correct += llm_ok

        mark = lambda ok: "o" if ok else "x"
        qshort = (q[:24] + "…") if len(q) > 25 else q
        print(f"  {qshort:<26} | {gold:<6}| {r:<5}{mark(rule_ok)} | {l:<5}{mark(llm_ok)}")

    n = len(testset)
    print(f"\n  규칙 라우터 : 정확도 {rule_correct}/{n} ({rule_correct/n*100:.0f}%), "
          f"llm 호출 {rule_calls}회 (빠름·공짜)")
    print(f"  llm  라우터 : 정확도 {llm_correct}/{n} ({llm_correct/n*100:.0f}%), "
          f"llm 호출 {llm_calls}회 (정확하지만 비용)")


if __name__ == "__main__":
    evaluate()