import pathlib
import sys

# 1. pathlib.path -> pathlib.Path 교정
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver  # inmemorysaver -> InMemorySaver (파스칼케이스 교정)

# 2. 체크포인터(단기기억)가 포함된 에이전트 생성
agent = create_agent(
    get_chat(temperature=0.3),
    tools=[],
    system_prompt="너는 친절한 상담원이다. 한국어 존댓말로 답하라.",
    checkpointer=InMemorySaver(),  # 인메모리 대화 저장소
)

# 3. 동일 대화 세션을 식별하기 위한 thread_id 설정
cfg = {"configurable": {"thread_id": "u1"}}

# 1턴: 이름 정보 전달
agent.invoke({"messages": [{"role": "user", "content": "내 이름은 지표야."}]}, cfg)

# 2턴: 동일 thread_id로 이전 대화 내용 질문 (단기기억 작동)
out = agent.invoke({"messages": [{"role": "user", "content": "내 이름 뭐야?"}]}, cfg)

# 4. 답변 추출 (m.text 대신 표준 속성인 m.content 사용)
answer = out["messages"][-1].content

print("봇:", answer)
print("'지표' 포함?", "지표" in answer)