import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver   # 인메모리 체크포인터

# 교안1. 메모리 붙인 에이전트
def build_agent():
    """단기기억(InMemorySaver)을 붙인 상담 에이전트를 생성한다."""
    llm = get_chat( temperature=0.3)
    agent = create_agent(
        llm,
        tools=[],  # 이번 강은 '기억'에 집중 — 도구 없음
        system_prompt="너는 승승장구몰의 친절한 CS 상담원이다. 한국어 존댓말로 답하라.",
        checkpointer=InMemorySaver(),   # ← 이 한 줄로 기억 활성화!
    )
    return agent

# 교안2. 대화 함수 — config로 thread_id 전달
def chat(agent, text: str, config: dict):
    """한 번의 대화 턴. config의 thread_id로 같은 세션을 식별한다."""
    # config의 thread_id가 같으면 이전 대화가 자동으로 이어진다(직접 append 불필요)
    result = agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
    return result, result["messages"]

# 교안3. 멀티턴 대화 실행
agent = build_agent()
cfg = {"configurable": {"thread_id": "user-A"}}

# 1턴: 이름 알려주기
result, _ = chat(agent, "내 이름은 민준이야.", cfg)
print(result["messages"][-1].text)
print('-' * 30)

cfg1 = {"configurable": {"thread_id": "user-A1"}}
result, _ = chat(agent, "내 이름은 홍길동이야", cfg1)
print(result["messages"][-1].text)
print('-' * 30)

# 2턴: 같은 thread_id로 물어보기 → 기억함!
result, _ = chat(agent, "내 이름 뭐랬지?", cfg)
print(result["messages"][-1].text)
print('-' * 30)

result, _ = chat(agent, "내 이름 뭐랬지?", cfg1)
print(result["messages"][-1].text)
print('-' * 30)