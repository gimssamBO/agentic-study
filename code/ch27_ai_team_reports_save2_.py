# -*- coding: utf-8 -*-
# 실행: python code/ch27_ai_team_save_app.py
import sys, pathlib, datetime
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에

from common import ROOT                         # 프로젝트 루트 경로 (common.py 제공)
from langgraph.graph import StateGraph, START, END
from ch27_ai_team import (                      # 기존 노드 그대로 재사용
    TeamState as BaseState,
    researcher, analyst, writer, load_competitor_text,
)

reports = ROOT / "reports"                      # 기본 저장소 폴더

##########################################################################
# 교안5. 응용 — 한 폴더로 묶기
# 한 번 실행 = 한 폴더 (선택적 개선)
run_dir = reports / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir.mkdir(parents=True, exist_ok=True)
# 이후 save_artifact가 run_dir 아래에 01_raw, 02_analysis, 03_report 저장
##########################################################################


# [교안2. 저장 함수 수정] run_dir 내부로 저장하도록 연결
def save_artifact(name: str, content: str, ext: str = "md") -> pathlib.Path:
    """산출물 한 건을 현재 실행 폴더(run_dir) 아래에 저장하고 경로를 반환한다."""
    path = run_dir / f"{name}.{ext}"
    path.write_text(content, encoding="utf-8")   # 한글 안전하게 utf-8
    print(f"  [저장] {name} → {path}")
    return path


# [교안3. 저장 래퍼 노드] 기존 노드를 감싸서 저장 호출
def researcher_save(state: BaseState) -> dict:
    """researcher 실행 → 정리된 사실(raw)을 .txt로 저장."""
    upd = researcher(state)                     # 기존 노드 그대로 실행
    save_artifact("01_raw", upd["raw"], ext="txt")  # 산출물 저장
    return upd


def analyst_save(state: BaseState) -> dict:
    """analyst 실행 → 분석 결과(analysis)를 .md로 저장."""
    upd = analyst(state)
    save_artifact("02_analysis", upd["analysis"])
    return upd


def writer_save(state: BaseState) -> dict:
    """writer 실행 → 최종 리포트(report)를 .md로 저장."""
    upd = writer(state)
    save_artifact("03_report", upd["report"])
    return upd


# [교안4. 그래프 조립]
def build_team():
    """저장 래퍼 노드로 묶은 파이프라인(흐름은 27강과 동일)."""
    g = StateGraph(BaseState)
    g.add_node("researcher", researcher_save)   # 래퍼 노드 등록
    g.add_node("analyst", analyst_save)
    g.add_node("writer", writer_save)

    g.add_edge(START, "researcher")
    g.add_edge("researcher", "analyst")
    g.add_edge("analyst", "writer")
    g.add_edge("writer", END)
    return g.compile()


if __name__ == "__main__":
    team = build_team()
    initial = {"raw": load_competitor_text(), "analysis": "", "report": ""}
    print(f"이번 실행 산출물 저장 위치: {run_dir}")
    final = initial
    for state in team.stream(initial, stream_mode="values"):
        final = state
        
    print("\n" + "=" * 60)
    print(final["report"])