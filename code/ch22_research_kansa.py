# -*- coding: utf-8 -*-
# 실행: python code/ch22_research.py
import sys, pathlib, datetime
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "code"))
from common import get_chat

from pydantic import BaseModel, Field
from langchain_community.tools import DuckDuckGoSearchResults

# DuckDuckGoSearchResults: 키가 필요 없는 무료 웹 검색 도구(ddgs 패키지 기반).
#   [왜 검색 도구] LLM은 학습 시점 이후의 '최신 정보'를 모른다(지식 컷오프).
#   웹 검색으로 실시간 사실을 끌어와 답을 '사실에 근거(grounding)'시킨다.
from langchain_community.tools import DuckDuckGoSearchResults
from langchain.agents import create_agent   # LLM+도구를 묶어 스스로 도구를 쓰는 에이전트 생성


def build_research_agent():
    """웹 검색 도구를 붙인 리서치 에이전트를 만들어 반환한다.

    create_agent 에 검색 도구를 넘기면, 에이전트가 스스로
    '검색 → 결과 수집 → 요약'을 반복해 리포트를 만든다.
    """
    llm = get_chat(temperature=0.3)   # [왜 0.3] 사실 수집이지만 리포트 서술력도 필요해 약간 높임
    search = DuckDuckGoSearchResults()  # 검색 도구 인스턴스(키 불필요)
    agent = create_agent(
        llm,
        tools=[search],                 # 이 도구를 언제 쓸지는 LLM이 스스로 판단
        system_prompt=(                 # 역할·출력형식을 고정하는 시스템 프롬프트
            "너는 승승장구몰의 시장 조사 애널리스트다. "
            "주어진 주제를 웹에서 검색해 핵심 사실을 수집하고, "
            "한국어 마크다운 리포트로 정리하라. "
            "리포트는 '## 개요 / ## 핵심 동향 / ## 시사점' 섹션을 포함한다."
        ),
    )
    return agent


def research(topic: str) -> str:
    """주제를 조사해 마크다운 리포트 본문(문자열)을 반환한다.

    [왜 try/except] 검색은 외부 네트워크에 의존한다. 단절·rate limit 으로
    실패할 수 있으므로, 실패해도 서비스가 죽지 않도록 폴백 분기를 둔다.
    """
    try:
        agent = build_research_agent()
        # 에이전트 호출: messages 에 사용자 요청을 담아 보낸다(검색→요약은 내부에서 자동).
        result = agent.invoke({"messages": [{"role": "user",
                              "content": f"'{topic}' 주제로 시장 동향 리포트를 작성해줘."}]})
        return result["messages"][-1].text   # 마지막 메시지 = 최종 리포트 본문
    except Exception as e:
        # 네트워크/검색 실패 → 검색 없이 LLM 지식만으로 임시 리포트(폴백)
        print(f"[경고] 웹 검색 실패 → 오프라인 폴백 사용: {e}")
        llm = get_chat(temperature=0.3)
        prompt = (f"'{topic}'에 대해 아는 범위에서 한국어 마크다운 리포트를 작성하라. "
                  "본문에 '## 개요', '## 핵심 동향', '## 시사점' 세 섹션을 정확히 이 머리말로 포함하라"
                  "(머리말을 중복해서 붙이지 말 것). "
                  "맨 위에 최신 정보가 아닐 수 있다는 주의문구 한 줄을 넣어라.")
        return llm.invoke(prompt).text    


def save_report(topic: str, body: str) -> pathlib.Path:
    """리포트 본문을 헤더와 함께 reports/ 폴더에 .md로 저장하고 경로를 반환한다.

    [왜 research/save 분리] 재사용·테스트를 쉽게 하려는 모듈화.
    배치는 research→save 만 호출하면 되고, API는 research() 결과를 바로 응답할 수 있다.
    """
    out_dir = pathlib.Path(__file__).resolve().parent.parent / "reports"
    out_dir.mkdir(exist_ok=True)        # reports/ 폴더가 없으면 생성
    today = datetime.date.today().isoformat()
    path = out_dir / f"research_{today}.md"
    header = f"# 시장 조사 리포트 — {topic}\n\n> 생성일: {today} (자동 생성)\n\n"
    path.write_text(header + body, encoding="utf-8")   # 한글 깨짐 방지 위해 utf-8 명시
    return path


class SubQueries(BaseModel):
    """[왜 구조화] LLM이 자유 텍스트로 질의를 내면 파싱이 흔들린다.
    Pydantic으로 '리스트'를 강제해 안정적으로 하위 질의를 받는다."""
    queries: list[str] = Field(description="원주제를 조사하기 위한 3~4개의 구체적 하위 검색 질의")


def split_topic(topic: str) -> list[str]:
    """큰 주제를 3~4개의 하위 질의로 분해한다(구조화 출력)."""
    llm = get_chat(temperature=0.2)
    structured = llm.with_structured_output(SubQueries)
    prompt = (
        f"너는 승승장구몰의 시장 조사 애널리스트다. 주제 '{topic}'를 깊이 조사하기 위해 "
        "서로 겹치지 않는 구체적 하위 검색 질의 3~4개로 쪼개라. "
        "각 질의는 한국어 검색어 형태로 작성하라."
    )
    try:
        return structured.invoke(prompt).queries[:4]   # 최대 4개로 제한
    except Exception as e:
        # 구조화 실패 시 최소한의 폴백 질의
        print(f"[경고] 질의 분해 실패 → 기본 질의 사용: {e}")
        return [f"{topic} 시장 규모", f"{topic} 최신 동향", f"{topic} 주요 기업"]

def search_one(query: str) -> str:
    """하위 질의 하나를 웹 검색해 결과 텍스트를 반환한다(실패 시 폴백)."""
    try:
        return DuckDuckGoSearchResults().invoke(query)
    except Exception as e:
        # [왜 폴백] 한 질의의 네트워크 실패로 전체 조사가 멈추면 안 된다.
        print(f"[경고] 검색 실패('{query}') → LLM 지식으로 대체: {e}")
        llm = get_chat(temperature=0.3)
        return llm.invoke(f"'{query}'에 대해 아는 범위에서 핵심 사실 3가지를 한국어로 정리하라.").content

def synthesize(topic: str, findings: list[tuple]) -> str:
    """하위 질의별 검색 결과들을 하나의 마크다운 리포트로 종합한다."""
    llm = get_chat(temperature=0.3)
    # 각 결과를 1200자로 잘라 붙임(토큰 절약). findings = [(질의, 검색결과), ...]
    blocks = "\n\n".join(f"[하위질의] {q}\n{r[:1200]}" for q, r in findings)
    prompt = (
        f"주제: {topic}\n아래는 하위 질의별 검색 결과다. 이를 종합해 한국어 마크다운 리포트를 작성하라.\n"
        "'## 개요 / ## 핵심 동향 / ## 시사점' 섹션을 정확히 이 머리말로 포함하라.\n\n"
        f"{blocks}"
    )
    return llm.invoke(prompt).content

def deep_research(topic: str) -> str:
    """주제 분해 → 하위 검색 → 종합의 전체 파이프라인."""
    queries = split_topic(topic)                 # 1) 분해
    print(f"[분해] {len(queries)}개 하위 질의:")
    for i, q in enumerate(queries):
        print(f"  [{i}] {q}")
    findings = []
    for i, q in enumerate(queries):              # 2) 질의별 검색
        print(f"[검색 {i}] {q} ...")
        findings.append((q, search_one(q)))
    return synthesize(topic, findings)           # 3) 종합


if __name__ == "__main__":
    topic = "경쟁 무선이어버드 시장 동향"
    print("=" * 60)
    print(f"[조사 시작] {topic}")
    body = deep_research(topic)
    path = save_report(topic, body)              # 저장은 기존 함수 재사용
    print("=" * 60)
    print(body[:600], "...")
    print("=" * 60)
    print("[저장 완료]", path)
