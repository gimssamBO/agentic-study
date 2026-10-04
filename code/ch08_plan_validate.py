# 실행: python code/ch08_plan_validate.py
from typing import List
from pydantic import BaseModel
from common import get_chat

# 1. LLM 모델 초기화 (OpenAI 사용)
llm = get_chat(provider="openai")

# 2. 계획의 적합 범위 (하위 작업 개수 기준)
MIN_STEPS, MAX_STEPS = 2, 8

# 3. 계획의 구조를 정의하는 스키마
class Plan(BaseModel):
    goal: str
    steps: List[str]

def make_plan(goal: str) -> Plan:
    """목표를 받아 실행 순서대로 하위 작업 목록으로 분해한 계획을 만든다."""
    planner = llm.with_structured_output(Plan)
    prompt = (
        "너는 승승장구몰의 프로젝트 매니저다. 아래 목표를 실행 순서대로 "
        f"{MIN_STEPS}~{MAX_STEPS}개의 구체적 하위 작업으로 분해하라.\n"
        f"목표: {goal}"
    )
    return planner.invoke(prompt)

def validate_plan(plan: Plan):
    """계획의 적합성을 판정한다. (적합여부 bool, 사유 str)를 돌려준다."""
    n = len(plan.steps)
    if n < MIN_STEPS:
        return False, f"단계가 {n}개뿐입니다 — 목표 분해가 부족합니다(최소 {MIN_STEPS}개)."
    if n > MAX_STEPS:
        return False, f"단계가 {n}개로 너무 많습니다 — 과분해입니다(최대 {MAX_STEPS}개)."
    if any(not s.strip() for s in plan.steps):
        return False, "빈 단계가 포함되어 있습니다 — 실행 불가능한 단계입니다."
    return True, "적합한 계획입니다."

def replan(goal: str, reason: str) -> Plan:
    """검증 실패 이유(reason)를 피드백으로 붙여 계획을 다시 세운다."""
    planner = llm.with_structured_output(Plan)
    prompt = (
        "너는 승승장구몰의 프로젝트 매니저다. 이전 계획이 다음 이유로 부적합 판정을 받았다.\n"
        f"부적합 사유: {reason}\n"
        f"이 점을 반드시 고쳐, 목표를 실행 순서대로 {MIN_STEPS}~{MAX_STEPS}개의 "
        f"구체적 하위 작업으로 다시 분해하라.\n목표: {goal}"
    )
    return planner.invoke(prompt)

def plan_with_validation(goal: str, max_replan: int = 2) -> Plan:
    """계획 → 검증 → (부적합 시) 재계획을 최대 max_replan회 반복한다."""
    plan = make_plan(goal)
    for attempt in range(1, max_replan + 1):
        ok, reason = validate_plan(plan)
        print(f"[STEP {attempt}] 검증: {'적합' if ok else '부적합'} — {reason}")
        if ok:
            return plan                       # 통과 → 채택
        print(f"        → 재계획 요청(피드백: {reason})")
        plan = replan(goal, reason)           # 부적합 → 다시 짜기
    return plan

if __name__ == "__main__":
    goal = "승승장구몰 신상품 '가을 패딩' 출시"

    # --- 데모 1: 일부러 단계가 1개뿐인 나쁜 계획을 만들어 검증기가 잡는지 확인 ---
    bad_plan = Plan(goal=goal, steps=["그냥 출시한다"])
    ok, reason = validate_plan(bad_plan)
    print(f"검증: {'적합' if ok else '부적합'} — {reason}")
    # → 부적합 — 단계가 1개뿐입니다...

    if not ok:
        fixed = replan(goal, reason)   # 피드백 주고 재계획
        for i, s in enumerate(fixed.steps, 1):
            print(f"  {i}. {s}")

    # --- 데모 2: 계획→검증→재계획 전체 파이프라인 실행 ---
    print("\n--- 전체 파이프라인 실행 ---")
    final_plan = plan_with_validation(goal)
    for i, s in enumerate(final_plan.steps, 1):
        print(f"  {i}. {s}")