# -*- coding: utf-8 -*-
# 실행: python code/ch22_ex_competitor.py
import sys, pathlib
# 1. common 모듈 참조 설정 (Path 대문자 정정 및 상위 디렉터리 접근)
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, DATA
import pandas as pd

def make_competitor_report(csv_path: pathlib.Path) -> str:
    """경쟁사 csv를 표로 만들어 llm에게 리포트를 작성시킨다(검색 불필요)."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")     # 엑셀 bom 대비
    table = df.to_markdown(index=False)                  # 데이터프레임 → 마크다운 표 (index=False 대문자)
    llm = get_chat(temperature=0.3)
    prompt = (
        "너는 승승장구몰의 시장 조사 애널리스트다. 아래 경쟁사 표를 근거로 "
        "한국어 마크다운 리포트를 작성하라. "
        "'## 개요', '## 경쟁사별 강약점', '## 시사점' 세 섹션을 정확히 이 머리말로 포함하라. "
        "표에 있는 모든 경쟁사를 빠짐없이 언급하라.\n\n"
        f"{table}"
    )
    # LangChain AIMessage 속성에 맞게 .content로 추출
    return llm.invoke(prompt).content

if __name__ == "__main__":
    body = make_competitor_report(DATA / "competitor_data.csv")
    out = pathlib.Path(__file__).resolve().parent.parent / "reports"
    out.mkdir(exist_ok=True)                             # exist_ok=True 대문자
    path = out / "competitor_report.md"
    path.write_text("# 경쟁사 분석 리포트\n\n" + body, encoding="utf-8")
    print(body[:500], "...")
    print("[저장 완료]", path)