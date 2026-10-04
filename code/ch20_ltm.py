import json, shutil
from common import DATA

SRC = DATA / "user_profiles.json"        # 원본(읽기 전용)
STORE = DATA / "user_profiles_rw.json"   # 실제 읽고/쓰는 복사본(영속 저장소)

def _load() -> dict:
    """저장소(JSON)를 읽어 dict로 반환. 없으면 원본을 복사해 초기화."""
    if not STORE.exists():
        shutil.copy(SRC, STORE)              # 최초 실행 시 원본 복사
    with open(STORE, encoding="utf-8") as f:  # 한글이라 인코딩 명시
        return json.load(f)

def _save(data: dict) -> None:
    """dict를 저장소(JSON)에 영속 저장."""
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


from langchain_core.tools import tool

@tool
def get_profile(customer_id: str) -> str:
    """고객ID(예: C0001)로 저장된 프로필(이름/선호카테고리/멤버십/관심사/비고)을 조회한다."""
    data = _load()
    p = data.get(customer_id)
    if not p:
        return f"{customer_id} 프로필이 없습니다."   # 없어도 안전한 메시지
    return json.dumps(p, ensure_ascii=False)       



@tool
def update_profile(customer_id: str, field: str, value: str) -> str:
    """고객 프로필의 한 필드를 갱신해 영속 저장한다.
    field 예: '비고', '관심사', 'membership'."""
    # [장기기억의 핵심] 이 도구가 파일에 '쓰기' 때문에 세션·재시작을 넘어 정보가 남는다
    data = _load()
    if customer_id not in data:
        data[customer_id] = {"name": "", "선호카테고리": [], "membership": "",
                             "관심사": "", "비고": ""}
    data[customer_id][field] = value
    _save(data)                          # ← 여기서 파일에 영속 저장!
    return f"{customer_id}의 '{field}'을(를) '{value}'(으)로 저장했습니다."


# print(get_profile.invoke({"customer_id": "C0001"}))   # 기존 프로필 조회
# print(update_profile.invoke({"customer_id": "C0001", "field": "비고", "value": "무향 선호"}))
# print(get_profile.invoke({"customer_id": "C0001"}))   # 변경 확인


from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from common import get_chat

def build_agent():
    llm = get_chat( temperature=0)
    agent = create_agent(
        llm,
        tools=[get_profile, update_profile],   # 장기 기억 (파일)
        system_prompt=(
            "너는 승승장구몰 상담원이다. 한국어 존댓말로 답하라. "
            "고객이 자신의 선호/특이사항(알레르기 등)을 말하면 update_profile로 저장하라. "
            "추천이나 응대 전에는 get_profile로 고객 정보를 먼저 확인하라."
        ),
        checkpointer=InMemorySaver(),   # 단기 기억 (세션 맥락)
    )
    return agent

def say(agent, text, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    out = agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
    return out["messages"][-1].content



agent = build_agent()
print(say(agent, "저 C0001 임도현인데요, 선크림 알레르기 있어요. 기억해 주세요.", "sess-1"))


# 새 에이전트 = 단기 기억 완전히 비워짐 (재시작 시뮬레이션)
agent2 = build_agent()
print(say(agent2, "C0001 고객에게 화장품 추천할 때 주의할 점 있어?", "sess-2"))