import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from pydantic import BaseModel, Field
from common import get_chat

llm = get_chat(provider="openai")

# 단계 하나를 표현하는 중첩 모델
class Step(BaseModel):
    작업: str = Field(description="수행할 하위 작업")
    예상_담당팀: str = Field(description="이 작업을 맡을 예상 담당팀")

class Plan(BaseModel):
    goal: str = Field(description="원래 목표")
    steps: list[Step] = Field(description="작업과 담당팀을 담은 단계 목록(4~7개)")

def make_plan(goal: str) -> Plan:
    planner = llm.with_structured_output(Plan)
    prompt = (
        "너는 승승장구몰의 프로젝트 매니저다. 다음 목표를 실행 순서대로 "
        "4~7개의 구체적 하위 작업으로 분해하고, 각 단계의 예상 담당팀도 함께 정하라.\n"
        f"목표: {goal}"
    )
    return planner.invoke(prompt)

if __name__ == "__main__":
    plan = make_plan("가을 패딩 출시")
    print("목표:", plan.goal)
    for i, s in enumerate(plan.steps, 1):
        print(f"  {i}. {s.작업} (담당: {s.예상_담당팀})")