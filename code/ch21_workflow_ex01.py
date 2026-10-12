import csv, pathlib, sys
from typing import TypedDict

# 1. common 모듈 참조 설정
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA, get_chat
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

# 기본 상태 스키마
class BaseTicketState(TypedDict):
    content: str
    category: str
    priority: str
    team: str

# alert 필드가 추가된 상태 스키마
class TicketState(BaseTicketState):
    alert: str

llm = get_chat(temperature=0)
CATEGORIES = ["결제", "배송", "환불", "교환", "회원", "기술지원", "기타"]

def classify_node(state: TicketState) -> dict:
    msg = [
        SystemMessage(f"다음 CS 티켓을 {CATEGORIES} 중 하나로만 분류하라. 카테고리 단어만 출력."),
        HumanMessage(state["content"]),
    ]
    out = llm.invoke(msg).content.strip()
    category = next((c for c in CATEGORIES if c in out), "기타")
    return {"category": category}

URGENT_WORDS = ["결제", "오류", "안 돼", "파손", "안와", "안 와"]
HIGH_WORDS = ["환불", "교환", "튕"]

def priority_node(state: TicketState) -> dict:
    text = state["content"]
    if state["category"] == "결제" or any(w in text for w in URGENT_WORDS):
        priority = "긴급"
    elif state["category"] in ("환불", "교환") or any(w in text for w in HIGH_WORDS):
        priority = "높음"
    else:
        priority = "보통"
    return {"priority": priority}

TEAM_MAP = {
    "결제": "결제지원팀", "환불": "정산팀", "교환": "물류팀",
    "배송": "물류팀", "회원": "회원관리팀", "기술지원": "기술지원팀",
}

def assign_node(state: TicketState) -> dict:
    team = TEAM_MAP.get(state["category"], "일반상담팀")
    return {"team": team}

# ---------------------------------------------------------
# 추가된 노드 및 라우터 정의

def notify_node(state: TicketState) -> dict:
    """긴급 티켓에 즉시 알림 플래그를 세팅한다."""
    return {"alert": "즉시알림"}

def route(state: TicketState) -> str:
    """긴급이면 notify를 거치고, 아니면 바로 assign으로."""
    return "notify" if state["priority"] == "긴급" else "assign"

# 그래프 조립
g = StateGraph(TicketState)
g.add_node("classify", classify_node)
g.add_node("priority", priority_node)
g.add_node("notify", notify_node)
g.add_node("assign", assign_node)

g.add_edge(START, "classify")
g.add_edge("classify", "priority")
g.add_conditional_edges("priority", route, {"notify": "notify", "assign": "assign"})
g.add_edge("notify", "assign")     # 알림 후 배정으로 합류
g.add_edge("assign", END)

workflow = g.compile()

# 실행 및 결과 출력
if __name__ == "__main__":
    with open(DATA / "support_tickets.csv", encoding="utf-8-sig") as f:
        tickets = list(csv.DictReader(f))

    print(f"{'티켓':<7}{'우선순위':<7}{'알림':<8}{'담당팀'}")
    print("-" * 35)
    for t in tickets:
        r = workflow.invoke({"content": t["content"]})
        print(f"{t['ticket_id']:<7}{r['priority']:<7}{r.get('alert', '-'):<8}{r['team']}")