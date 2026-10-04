##########################
# 1. 시작부 & 공유 상태


# -*- coding: utf-8 -*-
# 실행: python code/ch27_ai_team.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat, DATA

import pandas as pd
from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
# StateGraph: 노드(에이전트)들을 엣지로 이어 정해진 순서로 흐르게 하는 상태머신.
from langgraph.graph import StateGraph, START, END


class TeamState(TypedDict):
    """팀이 공유하는 상태. 각 노드가 자기 칸을 채워 다음 노드로 넘긴다."""
    raw: str        # Researcher 산출물(정리된 사실)
    analysis: str   # Analyst 산출물(강약점 분석)
    report: str     # Writer 산출물(최종 리포트)



#######################
# 2. 입력 데이터 → 텍스트
def load_competitor_text() -> str:
    """경쟁사 CSV를 읽어 LLM에 넣을 한 덩어리 텍스트로 만든다."""
    df = pd.read_csv(DATA / "competitor_data.csv")
    lines = [
        f"- {r.company}: 주력={r.main_category}, 평점={r.rating}, "
        f"강점={r.strength}, 약점={r.weakness}"
        for r in df.itertuples()
    ]
    return "승승장구몰 경쟁사 현황:\n" + "\n".join(lines)



##################################
# 3. 노드 = 에이전트 (세 역할 함수)

# 각 노드는 'state를 받아 → 바꿀 칸만 dict로 반환'한다. LangGraph가 그 칸을 병합한다.
llm = get_chat(temperature=0.2)   # 사실 정리·분석 위주라 낮은 온도


def researcher(state: TeamState) -> dict:
    """원천 데이터를 해석 없이 사실 위주로 정리한다(1단계)."""
    out = llm.invoke([
        SystemMessage("너는 리서처다. 주어진 데이터를 해석 없이 '사실'만 항목별로 깔끔히 정리하라."),
        HumanMessage(state["raw"]),    # 최초엔 원천 텍스트가 들어 있음
    ]).content
    return {"raw": out}                # 정리된 사실로 raw 칸 갱신 → 다음 노드가 사용


def analyst(state: TeamState) -> dict:
    """정리된 사실로 강점·약점·기회를 분석한다(2단계)."""
    out = llm.invoke([
        SystemMessage("너는 시장 분석가다. 경쟁사별 강점/약점과 승승장구몰의 기회를 분석하라."),
        HumanMessage(f"[정리된 사실]\n{state['raw']}"),   # 앞 노드가 채운 raw 를 입력으로
    ]).content
    return {"analysis": out}            # analysis 칸 채우기


def writer(state: TeamState) -> dict:
    """분석 결과를 임원 보고용 마크다운 리포트로 작성한다(3단계)."""
    out = llm.invoke([
        SystemMessage("너는 보고서 작성자다. 분석 내용을 임원 보고용 마크다운 리포트로 작성하라. "
                      "제목, 요약, 경쟁사별 정리, 결론(전략 제언) 순으로."),
        HumanMessage(f"[분석 결과]\n{state['analysis']}"),  # 앞 노드의 analysis 를 입력으로
    ]).content
    return {"report": out}              # report 칸 채우기 = 최종 산출물



####################################
# 1. 그래프 조립
def build_team():
    """세 에이전트를 노드로 등록하고 순서대로 엣지를 이어 팀(그래프)을 컴파일한다."""
    g = StateGraph(TeamState)              # State 모양으로 그래프 시작
    g.add_node("researcher", researcher)   # 노드 = 에이전트 등록
    g.add_node("analyst", analyst)
    g.add_node("writer", writer)

    g.add_edge(START, "researcher")     # 시작 → 리서처
    g.add_edge("researcher", "analyst") # 리서처 → 분석가
    g.add_edge("analyst", "writer")     # 분석가 → 작성자
    g.add_edge("writer", END)           # 작성자 → 끝
    return g.compile()                  # 실행 가능한 그래프로 컴파일



######################################
# 2. 실행 — stream으로 진행 보기

def main():
    team = build_team()
    # 초기 상태: raw 에 원천 텍스트를 넣고, 나머지 칸은 빈 문자열로 시작
    initial = {"raw": load_competitor_text(), "analysis": "", "report": ""}

    print("AI 팀 가동: Researcher → Analyst → Writer\n")
    final = initial
    for state in team.stream(initial, stream_mode="values"):
        final = state                  # 매번 최신 누적 상태를 잡아둠(마지막이 최종 결과)
        done = [k for k in ("analysis", "report") if state.get(k)]
        print(f"  [진행] 누적 상태: {', '.join(done) if done else '시작'}")

    print("\n" + "=" * 60)
    print(final["report"])


if __name__ == "__main__":
    main()