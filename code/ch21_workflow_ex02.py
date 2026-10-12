import sys, pathlib, csv
from typing import TypedDict

# 1. common 모듈 참조 설정
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, DATA

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

# 외부 의존 변수/함수 직접 정의
CATEGORIES = ["결제", "배송", "환불", "교환", "회원", "기술지원", "기타"]
TEAM_MAP = {
    "결제": "결제지원팀", "환불": "정산팀", "교환": "물류팀",
    "배송": "물류팀", "회원": "회원관리팀", "기술지원": "기술지원팀",
}

URGENT_WORDS = ["결제", "오류", "안 돼", "파손", "안와", "안 와"]
HIGH_WORDS = ["환불", "교환", "튕"]

def priority_node(state: dict) -> dict:
    text = state["content"]
    if state["category"] == "결제" or any(w in text for w in URGENT_WORDS):
        priority = "긴급"
    elif state["category"] in ("환불", "교환") or any(w in text for w in HIGH_WORDS):
        priority = "높음"
    else:
        priority = "보통"
    return {"priority": priority}

llm = get_chat(temperature=0)

class TicketState(TypedDict):
    content: str; category: str; priority: str; team: str; error: str

def classify_node(state) -> dict:
    try:
        # 검증용: 일부러 예외 던지기 (특정 내용에서)
        if "force_error" in state["content"]:
            raise ValueError("강제 예외 (테스트)")
        out = llm.invoke([SystemMessage(f"{CATEGORIES} 중 하나로 분류. 단어만."),
                          HumanMessage(state["content"])]).content.strip()
        cat = next((c for c in CATEGORIES if c in out), "기타")
        return {"category": cat, "error": ""}
    except Exception as e:
        return {"category": "기타", "error": f"분류 실패: {e}"}

def assign_node(state) -> dict:
    # error가 있으면 검토필요로 덮어씀
    if state.get("error"):
        return {"team": "검토필요"}
    return {"team": TEAM_MAP.get(state["category"], "일반상담팀")}

g = StateGraph(TicketState)
for name, fn in [("classify", classify_node), ("priority", priority_node), ("assign", assign_node)]:
    g.add_node(name, fn)
g.add_edge(START, "classify"); g.add_edge("classify", "priority")
g.add_edge("priority", "assign"); g.add_edge("assign", END)
workflow = g.compile()

tests = [{"ticket_id": "t1", "content": "결제가 안 돼요"},
         {"ticket_id": "t2", "content": "force_error 테스트 티켓"}]   # 예외 유발
for t in tests:
    r = workflow.invoke({"content": t["content"], "error": ""})
    print(f"{t['ticket_id']}: 팀={r['team']}, 오류={r.get('error') or '없음'}")