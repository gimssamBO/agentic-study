# -*- coding: utf-8 -*-
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA
from ch24_business import write_report, save_report
import pandas as pd

def load_facts_for(month: str) -> dict:
    """지정한 달의 facts를 계산한다. 없는 달이면 ValueError를 던진다."""
    df = pd.read_csv(DATA / "monthly_sales.csv").sort_values("month").reset_index(drop=True)
    if month not in df["month"].values:                        # 존재 확인
        available = ", ".join(df["month"].astype(str))
        raise ValueError(f"'{month}' 데이터가 없습니다. 사용 가능한 달: {available}")
    idx = df.index[df["month"] == month][0]
    if idx == 0:
        raise ValueError(f"'{month}'은 첫 달이라 전월 대비를 계산할 수 없습니다.")
    cur, prev = df.iloc[idx], df.iloc[idx - 1]                 # 지정 달과 그 전월
    cats = [c for c in df.columns if c not in ("month", "total")]
    cur_cats = cur[cats].sort_values(ascending=False)
    growth = (cur["total"] - prev["total"]) / prev["total"] * 100
    return {
        "month": cur["month"], "prev_month": prev["month"],
        "total": int(cur["total"]), "prev_total": int(prev["total"]),
        "growth_pct": round(growth, 1),
        "top_category": cur_cats.index[0], "top_value": int(cur_cats.iloc[0]),
        "second_category": cur_cats.index[1], "second_value": int(cur_cats.iloc[1]),
        "by_category": {k: int(v) for k, v in cur_cats.items()},
    }

def generate_monthly_report(month: str = None) -> pathlib.Path:
    """특정 달 리포트 생성(month=None이면 최신 달). 없는 달이면 친절한 메시지."""
    try:
        if month is None:
            from ch24_business import load_facts
            facts = load_facts()
        else:
            facts = load_facts_for(month)
    except ValueError as e:
        print(f"[안내] {e}")                  # 친절한 예외 메시지
        return None
    body = write_report(facts)
    return save_report(facts, body)

if __name__ == "__main__":
    print("[1] 존재하는 달 (2026-03)")
    p = generate_monthly_report("2026-03")
    print("  결과:", "저장됨 →", p if p else "생성 실패")

    print("\n[2] 없는 달 (1999-01)")
    p = generate_monthly_report("1999-01")
    print("  결과:", "저장됨 →", p if p else "생성 실패(예상된 동작)")