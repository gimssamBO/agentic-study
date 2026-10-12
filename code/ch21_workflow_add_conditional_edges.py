import sys, pathlib
import csv
from typing import TypedDict

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, DATA

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

# 상태 스키마 (분기 결과 출력을 위한 route, action 필드 포함)
class TicketState(TypedDict):
    content: str    # 티켓 원문 (입력)
    category: str   # 분류 노드가 채움
    priority: str   # 우선순위 노드가 채움
    team: str       # 배정 노드가 채움
    route: str      # 라우터 경로
    action: str     # 처리 조치 내용

llm = get_chat(temperature=0)
CATEGORIES = ["결제", "배송", "환불", "교환", "회원", "기술지원", "기타"]

def classify_node(state: TicketState) -> dict:
    """[노드1] 티켓 내용을 카테고리로 분류한다. (LLM)"""
    msg = [
        SystemMessage(f"다음 CS 티켓을 {CATEGORIES} 중 하나로만 분류하라. 카테고리 단어만 출력."),
        HumanMessage(state["content"]),
    ]
    out = llm.invoke(msg).content.strip()
    category = next((c for c in CATEGORIES if c in out), "기타")  # 목록에 없으면 '기타' 폴백
    return {"category": category}   # 채운 필드만 반환 → 상태에 자동 병합


URGENT_WORDS = ["결제", "오류", "안 돼", "파손", "안와", "안 와"]
HIGH_WORDS = ["환불", "교환", "튕"]

def priority_node(state: TicketState) -> dict:
    """[노드2] 카테고리/키워드로 우선순위를 정한다. (규칙)"""
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
    """[노드3] 카테고리에 맞는 담당팀을 배정한다. (규칙)"""
    team = TEAM_MAP.get(state["category"], "일반상담팀")  # 없으면 일반상담팀
    return {"team": team}

# =========================================================================
# 조건부 분기 노드 및 라우터 정의

# 교안2. add_conditional_edges — 갈림길
def route_by_priority(state: TicketState) -> str:
    """우선순위를 보고 다음 노드 이름을 반환하는 라우터 함수."""
    return "escalate" if state["priority"] == "긴급" else "assign"

# 교안3. 분기 노드 만들기
def escalate_node(state: TicketState) -> dict:
    """[긴급 분기] 즉시 상위팀으로 에스컬레이션한다."""
    return {
        "team": "긴급대응팀",
        "route": "긴급에스컬",
        "action": "sla 30분 내 즉시 에스컬레이션(담당자 호출)",
    }

def assign_route_node(state: TicketState) -> dict:
    """[일반 분기] 카테고리에 맞는 담당팀으로 일반 배정한다."""
    upd = assign_node(state)          # 기존 배정 규칙 재사용
    upd["route"] = "일반배정"
    upd["action"] = f"{upd['team']} 일반 배정(sla 24시간)"
    return upd

# =========================================================================
# 교안4. 조건부 엣지 연결
# 그래프 조립
def build_workflow():
    g = StateGraph(TicketState)
    g.add_node("classify", classify_node)
    g.add_node("priority", priority_node)
    g.add_node("escalate", escalate_node)
    g.add_node("assign", assign_route_node)

    g.add_edge(START, "classify")
    g.add_edge("classify", "priority")

    # 선형 엣지 대신 조건부 분기: priority 다음은 라우터 함수가 정한다
    g.add_conditional_edges(
        "priority",                                       # 이 노드 다음에
        route_by_priority,                                # 라우터 함수가 다음을 정함
        {"escalate": "escalate", "assign": "assign"},     # 반환값 → 실제 노드 매핑
    )
    g.add_edge("escalate", END)
    g.add_edge("assign", END)
    return g.compile()

# =========================================================================
# 실행 및 결과 출력

if __name__ == "__main__":
    workflow = build_workflow()

    with open(DATA / "support_tickets.csv", encoding="utf-8-sig") as f:
        tickets = list(csv.DictReader(f))

    for t in tickets:
        result = workflow.invoke({"content": t["content"]})
        print(f"{t['ticket_id']}  {result['priority']}   {result['route']}   {result['team']}   {result['action']}")