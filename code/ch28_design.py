
#############################
# 1. 시작부 & 설계 명세

# -*- coding: utf-8 -*-
# 실행: python code/ch28_design.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import DATA, DOCS

from dataclasses import dataclass

# [왜 설계 먼저] 30강에서 RAG+도구+메모리를 한꺼번에 구현하기 전에, 이 파일로
#   '무엇을 만들지'를 코드 스켈레톤(시그니처+TODO)으로 못 박는다. 함수 이름·시그니처를
#   먼저 합의해두면 구현 단계에서 설계가 흔들리지 않는다('살아있는 설계 문서').


@dataclass
class AgentSpec:
    """통합 CS 에이전트의 설계 명세(요약). dataclass 로 설정값을 한눈에 본다."""
    name: str = "승승장구몰 통합 CS 에이전트"
    tools: tuple = ("get_order_status", "get_stock", "search_faq", "policy_search")
    use_rag: bool = True          # 정책/멤버십 PDF 검색에 RAG 사용
    use_memory: bool = True       # 단기 기억(thread 별 대화 세션)
    use_multi_agent: bool = False # [왜 단일] 도구가 4개뿐이라 역할 분리 불필요 → 단일로 시작