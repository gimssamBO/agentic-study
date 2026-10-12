# -*- coding: utf-8 -*-
# 실행: python code/ch22_ex_multiquery.py
import sys, pathlib
# 1. common 모듈 참조 설정 (Path 대문자 정정)
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat
from langchain_community.tools import DuckDuckGoSearchResults

def search_one(query: str) -> str:
    """하위 질의 하나를 검색(실패 시 llm 지식 폴백)."""
    try:
        # DuckDuckGoSearchResults 클래스명 대문자 정정 및 결과를 str 형태로 추출
        results = DuckDuckGoSearchResults().invoke(query)
        return str(results)
    except Exception as e: # Exception 대문자 정정
        print(f"  [경고] 검색 실패 → llm 폴백: {e}")
        return get_chat(temperature=0.3).invoke(
            f"'{query}' 핵심 사실 3가지를 한국어로 정리하라.").content

def research_multi(topic: str, subtopics: list[str]) -> str:
    """주제를 하위 질의로 나눠 각각 검색·종합한다."""
    findings = []
    for i, sub in enumerate(subtopics):
        q = f"{topic} {sub}"
        print(f"[검색 {i}] {q} ...")                  # 진행 로그
        findings.append((sub, search_one(q)))
    blocks = "\n\n".join(f"[{s}]\n{r[:1000]}" for s, r in findings)
    llm = get_chat(temperature=0.3)
    prompt = (
        f"주제: {topic}\n아래 하위 주제별 검색 결과를 종합해 한국어 마크다운 리포트를 작성하라.\n"
        "'## 개요', '## 핵심 동향', '## 시사점' 세 섹션을 포함하고, "
        "각 하위 주제 내용을 모두 반영하라.\n\n"
        f"{blocks}"
    )
    # AIMessage 객체의 텍스트 추출 속성인 .content로 수정
    return llm.invoke(prompt).content

if __name__ == "__main__":
    topic = "무선이어버드 시장"
    subtopics = ["anc 노이즈캔슬링 트렌드", "가격대 동향", "주요 제조사 점유율"]
    print(f"[조사 시작] {topic} — {len(subtopics)}개 하위 질의")
    body = research_multi(topic, subtopics)
    print("=" * 60)
    print(body[:600], "...")