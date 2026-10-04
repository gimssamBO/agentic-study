import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, DATA
import csv
from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

class TicketState(TypedDict):
    # 모든 노드가 공유하는 상태. 각 노드는 일부 필드만 채워 dict로 반환하면 자동 병합
    content: str    # 티켓 원문 (입력)
    category: str   # 분류 노드가 채움
    priority: str   # 우선순위 노드가 채움
    team: str       # 배정 노드가 채움



llm = get_chat(temperature=0)
CATEGORIES = ["결제", "배송", "환불", "교환", "회원", "기술지원", "기타"]

def classify_node(state: TicketState) -> dict:
    """[노드1] 티켓 내용을 카테고리로 분류한다. (LLM)"""
    msg = [
        SystemMessage(f"다음 CS 티켓을 {CATEGORIES} 중 하나로만 분류하라. 카테고리 단어만 출력."),
        HumanMessage(state["content"]),
    ]
    out = llm.invoke(msg).text.strip()
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


from langgraph.graph import StateGraph, START, END

def build_workflow():
    g = StateGraph(TicketState)              # 상태 스키마로 그래프 생성
    g.add_node("classify", classify_node)    # 노드 등록(이름 → 함수)
    g.add_node("priority", priority_node)
    g.add_node("assign", assign_node)
    # 엣지로 실행 순서를 '고정'한다. 결정적 흐름: 분류 → 우선순위 → 배정
    g.add_edge(START, "classify")
    g.add_edge("classify", "priority")
    g.add_edge("priority", "assign")
    g.add_edge("assign", END)
    return g.compile()                       # 실행 가능한 워크플로우로 컴파일



workflow = build_workflow()
# result = workflow.invoke({"content": "결제가 안 돼요. 계속 오류가 납니다."})
# print(result)

with open(DATA / "support_tickets.csv", encoding="utf-8-sig") as f:
    tickets = list(csv.DictReader(f))

print(f"{'티켓':<7}{'분류':<7}{'우선순위':<7}{'담당팀':<10}내용")
print("-" * 70)
for t in tickets:
    result = workflow.invoke({"content": t["content"]})   # 한 티켓 처리
    print(f"{t['ticket_id']:<7}{result['category']:<7}"
          f"{result['priority']:<7}{result['team']:<10}{t['content'][:20]}")