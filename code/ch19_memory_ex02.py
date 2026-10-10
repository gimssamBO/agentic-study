import pathlib
import sys

# 1. pathlib.path -> pathlib.Path 교정
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver  # inmemorysaver -> InMemorySaver 파스칼케이스 교정

# 2. 인메모리 체크포인터(단기기억)가 연결된 에이전트 생성
agent = create_agent(
    get_chat(temperature=0.3),
    tools=[],
    system_prompt="너는 친절한 상담원이다. 한국어 존댓말로 답하라.",
    checkpointer=InMemorySaver(),  # 세션별 대화 기록을 격리 저장하는 체크포인터
)

# =====================================================================
# 세션 1 (u1): 사용자 정보 등록 및 기억 확인
# =====================================================================
cfg1 = {"configurable": {"thread_id": "u1"}}

# 1-1턴: 세션 u1에 이름 저장
agent.invoke({"messages": [{"role": "user", "content": "내 이름은 지표야."}]}, cfg1)

# 1-2턴: 세션 u1에서 이름 질문 (기억 확인)
out1 = agent.invoke({"messages": [{"role": "user", "content": "내 이름 뭐야?"}]}, cfg1)
ans1 = out1["messages"][-1].content  # text -> content 속성 교정
print("[u1] 봇:", ans1)


# =====================================================================
# 세션 2 (u2): 다른 thread_id로 접속 시 격리 여부 확인
# =====================================================================
cfg2 = {"configurable": {"thread_id": "u2"}}

# 2-1턴: 세션 u2에서 이름 질문 (u1의 정보를 모르는지 테스트)
out2 = agent.invoke({"messages": [{"role": "user", "content": "내 이름 뭐야?"}]}, cfg2)
ans2 = out2["messages"][-1].content  # text -> content 속성 교정
print("[u2] 봇:", ans2)


# =====================================================================
# 세션 간 메모리 격리 결과 검증
# =====================================================================
print("\n[격리 확인]")
print("  u1은 '지표' 앎:", "지표" in ans1)
print("  u2는 '지표' 모름:", "지표" not in ans2)