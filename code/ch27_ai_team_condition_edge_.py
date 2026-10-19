# -*- coding: utf-8 -*-
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에

from langgraph.graph import StateGraph, START, END
from ch27_ai_team import (                  # 기존 노드·로더 그대로 재사용
    TeamState as BaseState,
    researcher, analyst, writer, load_competitor_text,
)

class TeamState(BaseState):     # 기존 상태를 상속해 칸 추가
    retries: int   # 재수집(루프) 횟수 — 무한루프 방지용 카운터
    verdict: str   # 검수 결과: '충분' | '부실'

max_retries = 2    # 루프 상한 — 넘으면 부실해도 writer로 강제 진행

# 교안4. 검수 노드 — 품질 평가
def check(state: TeamState) -> dict:
    """analyst 산출물의 품질을 평가하는 검수 노드."""
    analysis = state.get("analysis", "")
    # 규칙 기반 1차 필터: 너무 짧거나 핵심 키워드가 없으면 '부실'
    too_short = len(analysis) < 200
    missing_core = not any(k in analysis for k in ("강점", "약점", "기회"))
    verdict = "부실" if (too_short or missing_core) else "충분"
    print(f"  [검수] 분석 길이={len(analysis)}자, "
          f"핵심키워드={'없음' if missing_core else '있음'} → 판정: {verdict}")
    return {"verdict": verdict}

# 교안5. 라우터 — 갈림길의 방향 결정
def route_after_check(state: TeamState) -> str:
    """검수 결과에 따라 다음 노드 이름을 반환. add_conditional_edges가 이 값으로 분기."""
    if state["verdict"] == "부실" and state["retries"] < max_retries:
        return "redo"
    return "ok"

# 교안6. 재조사 노드 — 카운터 올리며 루프
def researcher_retry(state: TeamState) -> dict:
    """재수집 단계. 재시도 카운터를 올린 뒤 다시 사실을 정리한다."""
    n = state["retries"] + 1
    print(f"  [재수집] {n}회차 — 부실 판정으로 researcher 재가동")
    upd = researcher({"raw": load_competitor_text()})  # 원천부터 다시 정리
    upd["retries"] = n                                  # 카운터 갱신
    return upd

# 7. 조건부 엣지로 그래프 조립
def build_team():
    g = StateGraph(TeamState)
    g.add_node("researcher", researcher)
    g.add_node("analyst", analyst)
    g.add_node("check", check)
    g.add_node("redo", researcher_retry)   # 재수집 노드(루프 경로)
    g.add_node("writer", writer)

    g.add_edge(START, "researcher")
    g.add_edge("researcher", "analyst")
    g.add_edge("analyst", "check")         # 분석 다음엔 반드시 검수
    # 검수 후 갈림길: 라우터 반환값 → 실제 노드 매핑
    g.add_conditional_edges(
        "check",
        route_after_check,                 # 이 함수가 "redo"/"ok" 반환
        {"redo": "redo", "ok": "writer"},  # 반환값 → 갈 노드
    )
    g.add_edge("redo", "analyst")          # 재수집 후 다시 분석 → 다시 검수(루프!)
    g.add_edge("writer", END)
    return g.compile()

# 교안8. 실행과 결과
if __name__ == "__main__":
    team = build_team()
    initial = {
        "raw": load_competitor_text(),
        "analysis": "",
        "report": "",
        "retries": 0,
        "verdict": ""
    }                                      # 카운터·판정 칸 초기화
    
    final = initial
    for state in team.stream(initial, stream_mode="values"):
        final = state

    print(f"\n최종 재시도 횟수: {final['retries']}회 / 최종 판정: {final['verdict']}\n")
    print(final["report"])        