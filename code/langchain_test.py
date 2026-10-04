from pydantic import BaseModel, Field

class Plan(BaseModel):
    """목표를 실행 가능한 하위 작업으로 분해한 결과."""
    goal: str = Field(description="원래 목표")
    steps: list[str] = Field(description="순서대로 실행할 하위 작업 목록(4~7개)")



from common import get_chat

# llm = get_chat(provider="gemini")
llm = get_chat(provider="openai")

# LLM 응답을 Plan 스키마에 맞춰 강제로 받아낸다
planner = llm.with_structured_output(Plan)
result = planner.invoke("가을 패딩 출시를 4~7단계로 분해하라")

print(type(result))      # <class 'Plan'>  ← dict가 아니라 Plan 객체!
print(result.goal)       # "가을 패딩 출시"
print(result.steps)      # ["시장조사", "콘셉트확정", ...]   