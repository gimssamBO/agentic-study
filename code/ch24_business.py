# -*- coding: utf-8 -*-
# 실행: python code/ch24_business.py
import sys, pathlib, datetime
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat, DATA

import pandas as pd

# [핵심 원칙] 계산은 코드(pandas), 서술은 LLM.
#   [왜 분리] 숫자 계산을 LLM에게 맡기면 틀리거나 지어낼 수 있다(환각).
#   정확해야 하는 집계는 코드로 확정하고, LLM에는 '확정된 수치의 서술'만 맡긴다.



def load_facts() -> dict:
    """monthly_sales.csv에서 최신 달의 핵심 수치를 코드로 정확히 계산해 dict로 반환한다."""
    df = pd.read_csv(DATA / "monthly_sales.csv")
    df = df.sort_values("month").reset_index(drop=True)  # 월 오름차순 정렬
    cur, prev = df.iloc[-1], df.iloc[-2]          # 최신 달, 전월

    cat_cols = [c for c in df.columns if c not in ("month", "total")]   # 카테고리 컬럼만
    cur_cats = cur[cat_cols].sort_values(ascending=False)   # 카테고리별 매출 내림차순

    growth = (cur["total"] - prev["total"]) / prev["total"] * 100   # 전월 대비 증감률(%)
    return {
        "month": cur["month"],
        "prev_month": prev["month"],
        "total": int(cur["total"]),
        "prev_total": int(prev["total"]),
        "growth_pct": round(growth, 1),
        "top_category": cur_cats.index[0],
        "top_value": int(cur_cats.iloc[0]),
        "second_category": cur_cats.index[1],
        "second_value": int(cur_cats.iloc[1]),
        "by_category": {k: int(v) for k, v in cur_cats.items()},
    }


#if __name__ == "__main__":
#    facts = load_facts()
#    print("[집계된 핵심 수치]")
#    print(f"  대상 월 : {facts['month']}")
#    print(f"  총매출  : {facts['total']:,}원 (전월 대비 {facts['growth_pct']}%)")
#    print(f"  1위     : {facts['top_category']} {facts['top_value']:,}원")
#    print(f"  2위     : {facts['second_category']} {facts['second_value']:,}원")



def write_report(facts: dict) -> str:
    """집계된 수치(facts)를 근거로 LLM이 경영진 보고용 마크다운 리포트를 작성한다.

    [왜 facts만 사용] 프롬프트에 '확정 수치'를 박아 넣고 새 숫자 금지를 지시해,
    LLM이 통계를 지어내지 못하게(환각 방지) 막는다.
    """
    llm = get_chat(temperature=0.3)   # 서술의 자연스러움 위해 약간 높임
    cat_lines = "\n".join(f"- {k}: {v:,}원" for k, v in facts["by_category"].items())
    prompt = (
        "너는 승승장구몰의 경영기획 담당자다. 아래 '확정 수치'만 근거로 "
        "경영진 보고용 한국어 월간 매출 요약 리포트를 마크다운으로 작성하라. "
        "숫자를 새로 지어내지 말고 주어진 수치만 사용하라. "
        "섹션: '## 총평 / ## 카테고리 분석 / ## 다음 달 제언'.\n\n"
        f"[확정 수치]\n"
        f"- 대상 월: {facts['month']} (전월: {facts['prev_month']})\n"
        f"- 총매출: {facts['total']:,}원 (전월 {facts['prev_total']:,}원, "
        f"증감 {facts['growth_pct']}%)\n"
        f"- 최대 카테고리: {facts['top_category']} {facts['top_value']:,}원\n"
        f"- 2위 카테고리: {facts['second_category']} {facts['second_value']:,}원\n"
        f"[카테고리별 매출]\n{cat_lines}\n"
    )
    return llm.invoke(prompt).content    


#if __name__ == "__main__":
#    facts = load_facts()
#    print("[LLM 리포트 생성 중...]")
#    body = write_report(facts)
#    print("=" * 60)
#    print(body)
#    print("=" * 60)



def save_report(facts: dict, body: str) -> pathlib.Path:
    """리포트를 reports/ 폴더에 월별 파일명으로 저장하고 경로를 반환한다."""
    out_dir = pathlib.Path(__file__).resolve().parent.parent / "reports"
    out_dir.mkdir(exist_ok=True)        # reports/ 폴더가 없으면 생성
    path = out_dir / f"monthly_sales_{facts['month']}.md"
    header = (f"# {facts['month']} 월간 매출 보고서\n\n"
              f"> 생성일: {datetime.date.today().isoformat()} (자동 생성)\n\n")
    path.write_text(header + body, encoding="utf-8")
    return path    



def generate_monthly_report() -> pathlib.Path:
    """집계 → 서술 → 저장 전체 파이프라인. 배치/엔드포인트에서 이 함수 하나만 호출하면 된다.

    [왜 단일 진입점] 매월 1일 자동 실행 같은 배치는 이 함수 하나만 부르면 끝나도록
    파이프라인을 한 함수로 묶어 운영을 단순화한다.
    """
    facts = load_facts()            # 1) 코드로 정확히 집계
    body = write_report(facts)      # 2) LLM이 서술
    return save_report(facts, body) # 3) .md 저장



if __name__ == "__main__":
    facts = load_facts()
    print("[집계된 핵심 수치]")
    print(f"  대상 월 : {facts['month']}")
    print(f"  총매출  : {facts['total']:,}원 (전월 대비 {facts['growth_pct']}%)")
    print(f"  1위     : {facts['top_category']} {facts['top_value']:,}원")

    print("\n[LLM 리포트 생성 중...]")
    body = write_report(facts)
    path = save_report(facts, body)

    print("=" * 60)
    print(body)
    print("=" * 60)
    print("[저장 완료]", path)