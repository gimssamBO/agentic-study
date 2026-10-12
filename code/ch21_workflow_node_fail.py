import sys, pathlib
import csv
from typing import TypedDict
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, DATA

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

# 교안2. 상태에 error 필드 추가
class TicketState(TypedDict):
    content: str    # 티켓 원문 (입력)
    category: str   # 분류 노드가 채움
    priority: str   # 우선순위 노드가 채움
    team: str       # 배정 노드가 채움
    error: str      # 오류 메시지(비어 있으면 정상)

llm = get_chat(temperature=0)
CATEGORIES = ["결제", "배송", "환불", "교환", "회원", "기술지원", "기타"]

# 교안3.검증 — LLM 출력을 믿지 마라
def classify_node(state: TicketState) -> dict:
    """[견고화] 입력값을 검증하고, LLM 출력도 검증하여 예외 발생 시에도 멈추지 않는다."""
    content = state.get("content", "").strip()

    # 1. 입력값이 비어있는 경우 사전 검증 (LLM 호출 전 차단)
    if not content:
        return {"category": "기타", "error": f"분류값 미허용('{state.get('content', '')}') → 기타 보정"}

    msg = [
        SystemMessage(f"다음 CS 티켓을 {CATEGORIES} 중 하나로만 분류하라. 카테고리 단어만 출력."),
        HumanMessage(content),
    ]

    try:
        out = llm.invoke(msg).content.strip()

        # 2. LLM 출력 검증 → 허용 목록 안에 있을 때만 정상 채택
        if out in CATEGORIES:
            return {"category": out, "error": ""}
        for c in CATEGORIES:  # 문장 속에 카테고리가 섞인 경우 구제
            if c in out:
                return {"category": c, "error": ""}

        # 3. 검증 실패: 허용 밖 값 → '기타'로 보정하고 사유 기록
        return {"category": "기타", "error": f"분류값 미허용('{out[:20]}') → 기타 보정"}
# 교안4. 예외도 잡는다
    except Exception as e:
        # 예외가 나도 '기타'로 보정하고 사유 기록 → 파이프라인 계속
        return {"category": "기타", "error": f"분류 예외: {e}"}


URGENT_WORDS = ["결제", "오류", "안 돼", "파손", "안와", "안 와"]
HIGH_WORDS = ["환불", "교환", "튕"]

# [노드 2] 우선순위 노드 (규칙)
def priority_node(state: TicketState) -> dict:
    text = state["content"]
    if state["category"] == "결제" or any(w in text for w in URGENT_WORDS):
        priority = "긴급"
    elif state["category"] in ("환불", "교환") or any(w in text for w in HIGH_WORDS):
        priority = "높음"
    else:
        priority = "보통"
    return {"priority": priority}

# [노드 3] 배정 노드 (규칙)
TEAM_MAP = {
    "결제": "결제지원팀", "환불": "정산팀", "교환": "물류팀",
    "배송": "물류팀", "회원": "회원관리팀", "기술지원": "기술지원팀",
}

def assign_node(state: TicketState) -> dict:
    team = TEAM_MAP.get(state["category"], "일반상담팀")
    return {"team": team}

# 그래프 조립
def build_workflow():
    g = StateGraph(TicketState)
    g.add_node("classify", classify_node)
    g.add_node("priority", priority_node)
    g.add_node("assign", assign_node)

    g.add_edge(START, "classify")
    g.add_edge("classify", "priority")
    g.add_edge("priority", "assign")
    g.add_edge("assign", END)
    return g.compile()

# 교안5. 죽지 않음을 시연
# 실행 및 테스트
if __name__ == "__main__":
    workflow = build_workflow()

    with open(DATA / "support_tickets.csv", encoding="utf-8-sig") as f:
        tickets = list(csv.DictReader(f))

    # 의도적으로 깨진 입력을 끼워 넣어 테스트
    tickets.append({"ticket_id": "tkbad", "content": ""})

    for t in tickets:
        result = workflow.invoke({"content": t["content"], "error": ""})
        flag = result.get("error") if result.get("error") else "정상"
        print(f"{t['ticket_id']:<7} {result['category']:<7} {result['priority']:<7} {result['team']:<10} {flag}")