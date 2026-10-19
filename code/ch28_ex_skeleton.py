# -*- coding: utf-8 -*-
# code/ch28_ex_skeleton.py
# 실행: python code/ch28_ex_skeleton.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA

from dataclasses import dataclass


@dataclass
class AgentSpec:
    """CS 티켓 분류·답변 에이전트의 설계 명세."""
    name: str = "CS 티켓 자동 분류·답변 에이전트"
    tools: tuple = ("classify_severity", "search_faq", "draft_reply")
    use_rag: bool = False         # FAQ가 짧아 CSV 검색으로 충분 → RAG 보류
    use_memory: bool = False      # 티켓 단건 처리 → 메모리 불필요
    use_multi_agent: bool = False # 도구 3개 → 단일로 시작


# ----- 도구 시그니처 (30강 구현 예정) -----
def classify_severity(content: str) -> str:
    """티켓 본문을 '긴급/보통/낮음'으로 분류. (구현: LLM 분류 또는 규칙)"""
    raise NotImplementedError("30강에서 구현 예정")  # TODO


def search_faq(keyword: str) -> str:
    """data/faq.csv 에서 키워드로 FAQ 답변 검색."""
    raise NotImplementedError("30강에서 구현 예정")  # TODO


def draft_reply(content: str, faq: str) -> str:
    """티켓 본문 + FAQ 근거로 답변 초안 작성."""
    raise NotImplementedError("30강에서 구현 예정")  # TODO


# ----- 진입 함수 시그니처 -----
def handle_ticket(content: str) -> dict:
    """티켓 한 건을 받아 {'severity':..., 'reply':...} 반환. (단일 진입점)"""
    # TODO: severity = classify_severity(content)
    #       faq = search_faq(키워드 추출)
    #       reply = draft_reply(content, faq)
    raise NotImplementedError("30강에서 구현 예정")


# ----- 설계 요약 출력 -----
def print_design():
    spec = AgentSpec()
    print("=" * 60)
    print(f"[설계] {spec.name}")
    print("=" * 60)
    print("요구사항:")
    print("  입력: support_tickets.csv 의 content")
    print("  출력: severity(긴급/보통/낮음) + 답변 초안")
    print(f"\n도구 목록: {', '.join(spec.tools)}")
    print(f"RAG: {spec.use_rag} / 메모리: {spec.use_memory} / "
          f"멀티에이전트: {spec.use_multi_agent}")
    print("\n데이터 흐름:")
    print("  티켓 → classify_severity → search_faq → draft_reply → [severity + 초안]")
    print(f"\n데이터 소스: {DATA}")


if __name__ == "__main__":
    print_design()