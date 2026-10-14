import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "code"))
from common import get_chat, DATA

import matplotlib
matplotlib.use("agg")   # [왜] 화면 없는 서버/배치에서도 png 저장이 되도록 비대화형 백엔드
import matplotlib.pyplot as plt
import koreanize_matplotlib   # 한글 폰트 설정(os 무관) — import 한 줄로 끝

from ch24_business import load_facts, write_report, save_report   # 집계·서술·저장 재사용

reports_dir = pathlib.Path(__file__).resolve().parents[1] / "reports"

def make_category_chart(facts: dict) -> pathlib.Path:
    """facts['by_category'] 로 카테고리별 매출 막대그래프를 그려 png 로 저장한다."""
    reports_dir.mkdir(exist_ok=True)
    cats = list(facts["by_category"].keys())                    # 카테고리명
    vals = [v / 10000 for v in facts["by_category"].values()]   # 만원 단위로 환산(가독성)

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(cats, vals, color="#4c72b0")
    ax.bar(cats[0], vals[0], color="#dd8452")     # 1위 카테고리만 강조 색(by_category는 내림차순)
    ax.set_title(f"승승장구몰 {facts['month']} 카테고리별 매출")
    ax.set_ylabel("매출(만원)")
    ax.set_xlabel("카테고리")
    plt.xticks(rotation=30, ha="right")           # 카테고리명이 길어 비스듬히
    for b, v in zip(bars, vals):                  # 막대 위에 값 라벨
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.0f}",
                ha="center", va="bottom", fontsize=9)
    plt.tight_layout()

    path = reports_dir / f"chart_{facts['month']}.png"
    plt.savefig(path, dpi=120)   # [경고] plt.show() 금지 — 배치에서는 저장만 한다
    plt.close(fig)               # 메모리 누수 방지(반복 생성 대비)
    return path

def write_report_with_chart(facts: dict, body: str, chart_path: pathlib.Path) -> str:
    """리포트 본문 맨 위에 차트 이미지 링크를 삽입한다.

    [왜 상대경로] .md 와 png 가 같은 reports/ 폴더에 있으므로 파일명만 적으면
    마크다운 뷰어가 바로 이미지를 띄운다. (절대경로는 다른 pc에서 깨진다)
    """
    img_md = f"![{facts['month']} 매출차트]({chart_path.name})\n\n"
    return img_md + body

if __name__ == "__main__":
    print("[1] 핵심 수치 집계 (코드)")
    facts = load_facts()
    print(f"  1위 : {facts['top_category']} {facts['top_value']:,}원")

    print("[2] 카테고리별 매출 차트 생성 (png 저장)")
    chart_path = make_category_chart(facts)
    print(f"  저장됨 : {chart_path}")

    print("[3] llm 서술 + 차트 링크 삽입 → .md 저장")
    body = write_report(facts)                                      # llm 서술 재사용
    body_with_img = write_report_with_chart(facts, body, chart_path)
    md_path = save_report(facts, body_with_img)                     # 저장 로직 재사용
    print(f"  저장됨 : {md_path}")