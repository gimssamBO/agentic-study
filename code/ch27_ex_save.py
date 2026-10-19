# -*- coding: utf-8 -*-
# code/ch27_ex_save.py (문제 1의 ch27_ex_review.py 에 저장 추가)
# 실행: python code/ch27_ex_save.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, ROOT

from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from ch27_ai_team import (
    TeamState as BaseState, researcher, analyst, writer, load_competitor_text,
)
from ch27_ex_review import reviewer, finalize, TeamState   # 문제1 재사용

output = ROOT / "output"

def save(name: str, content: str) -> None:
    """output/ 아래에 산출물을 저장한다(폴더 자동 생성)."""
    output.mkdir(parents=True, exist_ok=True)
    (output / name).write_text(content, encoding="utf-8")
    print(f"  [저장] {name} ({len(content)}자)")

# 각 노드를 감싸 결과를 저장하는 래퍼
def researcher_s(state): 
    upd = researcher(state); save("27_research.md", upd["raw"]); return upd

def analyst_s(state):
    upd = analyst(state); save("27_analysis.md", upd["analysis"]); return upd

def writer_s(state):
    upd = writer(state); save("27_report.md", upd["report"]); return upd

def finalize_s(state):
    upd = finalize(state); save("27_final.md", upd["final"]); return upd

def build_team():
    g = StateGraph(TeamState)
    g.add_node("researcher", researcher_s)
    g.add_node("analyst", analyst_s)
    g.add_node("writer", writer_s)
    g.add_node("reviewer", reviewer)        # 코멘트는 별도 저장 안 함(원하면 추가)
    g.add_node("finalize", finalize_s)
    
    g.add_edge(START, "researcher")
    g.add_edge("researcher", "analyst")
    g.add_edge("analyst", "writer")
    g.add_edge("writer", "reviewer")
    g.add_edge("reviewer", "finalize")
    g.add_edge("finalize", END)
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
    for state in team.stream(initial, stream_mode="values"):
        pass
    print(f"\n완료 — {output} 폴더를 확인하세요.")