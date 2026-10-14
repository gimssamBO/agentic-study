# -*- coding: utf-8 -*-
# 실행: python code/ch24_ex_growth.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA
import pandas as pd
import matplotlib
matplotlib.use("agg")                       # 화면 없는 환경 대응
import matplotlib.pyplot as plt
import koreanize_matplotlib                  # 한글 폰트(os 무관) — import 한 줄로 끝

# reports 저장 폴더 경로 설정 (code의 상위 폴더 내 reports)
reports = pathlib.Path(__file__).resolve().parent.parent / "reports"

def category_growth():
    """각 카테고리의 첫 달 대비 마지막 달 성장률(%)을 계산해 dict로 반환."""
    df = pd.read_csv(DATA / "monthly_sales.csv").sort_values("month").reset_index(drop=True)
    first, last = df.iloc[0], df.iloc[-1]
    cats = [c for c in df.columns if c not in ("month", "total")]
    growth = {}
    for c in cats:
        if first[c] > 0:                                  # 0으로 나누기 방지
            growth[c] = round((last[c] - first[c]) / first[c] * 100, 1)
    return last, cats, growth

if __name__ == "__main__":
    last, cats, growth = category_growth()
    ranked = sorted(growth.items(), key=lambda x: x[1], reverse=True)   # 성장률 내림차순
    print("[카테고리 성장률]")
    for c, g in ranked:
        print(f"  {c}: {g:+.1f}%")
    print(f"\n성장률 1위: {ranked[0][0]} ({ranked[0][1]:+.1f}%)")
    print(f"성장률 꼴찌: {ranked[-1][0]} ({ranked[-1][1]:+.1f}%)")

    # 최신 달 카테고리별 매출 막대그래프
    reports.mkdir(exist_ok=True)
    vals = [last[c] / 10000 for c in cats]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(cats, vals, color="#4c72b0")
    ax.set_title(f"{last['month']} 카테고리별 매출")
    ax.set_ylabel("매출(만원)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    path = reports / "category_sales.png"
    plt.savefig(path, dpi=120); plt.close(fig)
    print("[차트 저장]", path)