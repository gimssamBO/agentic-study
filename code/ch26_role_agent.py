######################################
# 1. 시작부와 데이터 로드

# -*- coding: utf-8 -*-
# 실행: python code/ch26_role_agent.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat, DATA

import pandas as pd
from pydantic import BaseModel, Field           # 구조화 출력(JSON 스키마) 정의용
from langchain_core.messages import SystemMessage, HumanMessage

# [왜 Planner/Worker 분리] 한 LLM에게 '계획도 세우고 실행도 하라'고 하면 둘 다 어설퍼진다.
#   Planner(계획 세우는 역할)가 작업을 잘게 쪼개고, Worker(실행 역할)가 한 작업씩
#   집중 수행하면 각자 잘하는 일에만 몰두해 품질이 올라간다. (25강 역할 분리의 연장선)


def load_brief_text(campaign_id: str = "CMP02") -> str:
    """캠페인 ID로 브리프 1건을 읽어 LLM에 넣을 한 줄 텍스트로 만든다."""
    brief = pd.read_csv(DATA / "marketing_brief.csv")
    campaign = brief[brief["campaign_id"] == campaign_id].iloc[0]   # 캠페인 1건 선택
    return (
        f"캠페인명: {campaign.title} / 카테고리: {campaign.category} / "
        f"타깃: {campaign.target} / 예산: {campaign.budget:,}원 / "
        f"핵심혜택: {campaign.key_offer}"
    )



################################
# 2. 구조화 출력 스키마
class Plan(BaseModel):
    """Planner가 만드는 실행 계획(구조화 출력 스키마)."""
    # [왜 구조화 출력] 자유 텍스트가 아니라 list[str] 형태로 강제해, 코드가
    #   결과를 바로 반복(for)할 수 있게 한다. 파싱 실수가 사라진다.
    subtasks: list[str] = Field(description="이 캠페인을 위해 필요한 하위 작업 3~4개")


############################
# 3. Planner 함수

PLANNER_SYSTEM = (        # Planner 역할 고정 프롬프트 — '쪼개기만, 실행은 금지'
    "너는 마케팅 캠페인 '기획 설계자(Planner)'다. "
    "주어진 캠페인 브리프를 보고, 실행에 필요한 하위 작업을 3~4개로 쪼개라. "
    "작업은 서로 겹치지 않게, 한 문장 명령형으로 작성하라. 실행은 하지 마라."
)


def plan(llm, brief_text: str) -> list[str]:
    """브리프를 보고 하위 작업 리스트(JSON)로 분해한다."""
    planner = llm.with_structured_output(Plan)   # 출력을 Plan 스키마로 강제
    result = planner.invoke([
        SystemMessage(PLANNER_SYSTEM),           # 역할 지시
        HumanMessage(f"[캠페인 브리프]\n{brief_text}"),  # 입력 데이터
    ])
    return result.subtasks                       # 하위 작업 문자열 리스트


###########################
# 4. 실행해 확인
# if __name__ == "__main__":
#     brief_text = load_brief_text("CMP02")
#     print("[브리프]", brief_text)
#     print()

#     llm_plan = get_chat(temperature=0)    # 계획은 재현성 → 0
#     subtasks = plan(llm_plan, brief_text)
#     print("[Planner 분해 결과]")
#     for i, t in enumerate(subtasks, 1):
#         print(f"   {i}. {t}")


#######################################
# 1. Worker 함수

WORKER_SYSTEM = (         # Worker 역할 고정 프롬프트 — '딱 한 작업만' 집중
    "너는 마케팅 '실무 작업자(Worker)'다. "
    "주어진 캠페인 브리프 맥락에서, 지정된 '하나의 작업'만 구체적으로 수행하라. "
    "결과는 5줄 이내로 실무에 바로 쓸 수 있게 작성하라."
)


def work(llm, brief_text: str, subtask: str) -> str:
    """하나의 하위 작업만 받아 구체적으로 수행한 결과를 반환한다."""
    result = llm.invoke([
        SystemMessage(WORKER_SYSTEM),
        HumanMessage(f"[캠페인 브리프]\n{brief_text}\n\n[수행할 작업]\n{subtask}"),  # 맥락+그 작업 하나
    ])
    return result.content


 ################################
 # 4. 실행해 확인
# if __name__ == "__main__":
#     brief_text = load_brief_text("CMP02")
#     llm_plan = get_chat(temperature=0)
#     llm_work = get_chat(temperature=0.5)

#     subtasks = plan(llm_plan, brief_text)            # 04번 Planner
#     print("[작업 분해 완료]", len(subtasks), "개\n")

#     for i, subtask in enumerate(subtasks, 1):
#         print(f"[작업 {i}] {subtask}")
#         result = work(llm_work, brief_text, subtask)  # Worker 실행
#         print(result)
#         print("-" * 50)    


###############################
# 1. 오케스트레이터 — 계획 → 실행 → 취합
def run_campaign(brief_text: str) -> str:
    """Planner로 쪼개고, Worker로 하나씩 실행해, 결과를 하나의 실행안으로 취합한다."""
    llm_plan = get_chat(temperature=0)      # [왜 0] 계획은 일관성·재현성이 중요
    llm_work = get_chat(temperature=0.5)    # [왜 0.5] 카피 등 창의 작업은 다양성이 도움

    print("[1] Planner 작업 분해 중...")
    subtasks = plan(llm_plan, brief_text)        # 계획 단계
    for i, t in enumerate(subtasks, 1):
        print(f"   서브태스크 {i}: {t}")

    print("\n[2] Worker 실행 중...")
    outputs = []
    for i, t in enumerate(subtasks, 1):          # 하위 작업을 하나씩 순회 실행
        print(f"   - 작업 {i} 수행: {t}")
        outputs.append((t, work(llm_work, brief_text, t)))   # (작업, 산출물) 보관

    print("\n[3] 결과 취합")
    report = [f"# 캠페인 실행안\n\n> {brief_text}\n"]
    for i, (t, out) in enumerate(outputs, 1):
        report.append(f"## {i}. {t}\n{out}\n")
    return "\n".join(report)         


#################################
#4. 전체 실행
def main():
    brief_text = load_brief_text("CMP02")   # 캠페인 1건 텍스트 로드
    print(run_campaign(brief_text))


if __name__ == "__main__":
    main()