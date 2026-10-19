# -*- coding: utf-8 -*-
# code/ch27_ex_review.py
# 실행: python code/ch27_ex_review.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat

from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

# 기존 노드·로더 재사용
from ch27_ai_team import (
    TeamState as BaseState,
    researcher, analyst, writer, load_competitor_text,
)

llm = get_chat(temperature=0.2)

class TeamState(BaseState):     # 기존 상태에 칸 2개 추가
    review: str    # reviewer 코멘트
    final: str     # 코멘트 반영 최종본

def reviewer(state: TeamState) -> dict:
    """report의 사실성·가독성을 평가해 개선 코멘트를 review에 저장."""
    out = llm.invoke([
        SystemMessage("너는 보고서 검토자다. 주어진 리포트의 사실성·가독성·구성을 평가하고, "
                      "개선할 점을 3가지 이내로 구체적으로 지적하라. 다시 쓰지는 마라."),
        HumanMessage(f"[검토할 리포트]\n{state['report']}"),
    ]).content
    print("  [reviewer] 검토 코멘트 작성 완료")
    return {"review": out}

def finalize(state: TeamState) -> dict:
    """검토 코멘트를 반영해 최종본을 final에 작성."""
    out = llm.invoke([
        SystemMessage("너는 보고서 작성자다. 아래 [리포트]를 [검토 의견]에 따라 개선한 "
                      "최종본을 마크다운으로 작성하라."),
        HumanMessage(f"[리포트]\n{state['report']}\n\n[검토 의견]\n{state['review']}"),
    ]).content
    print("  [finalize] 코멘트 반영 최종본 작성 완료")
    return {"final": out}

def build_team():
    g = StateGraph(TeamState)
    g.add_node("researcher", researcher)
    g.add_node("analyst", analyst)
    g.add_node("writer", writer)
    g.add_node("reviewer", reviewer)       # 추가
    g.add_node("finalize", finalize)       # 추가

    g.add_edge(START, "researcher")
    g.add_edge("researcher", "analyst")
    g.add_edge("analyst", "writer")
    g.add_edge("writer", "reviewer")       # writer → reviewer
    g.add_edge("reviewer", "finalize")     # reviewer → finalize
    g.add_edge("finalize", END)            # finalize → 끝
    return g.compile()

if __name__ == "__main__":
    team = build_team()
    initial = {
        "raw": load_competitor_text(),
        "analysis": "",
        "report": "",
        "review": "",
        "final": ""
    }
    final = initial
    for state in team.stream(initial, stream_mode="values"):
        final = state

    print("\n===== 검토 코멘트 =====")
    print(final["review"])
    print("\n===== 최종본 =====")
    print(final["final"])