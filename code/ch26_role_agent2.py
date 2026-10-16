# -*- coding: utf-8 -*-
# 실행: python code/ch26_role_agent.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat, DATA

import pandas as pd
from pydantic import BaseModel, Field           # 구조화 출력(JSON 스키마) 정의용
from langchain_core.messages import SystemMessage, HumanMessage

# 재시도 기본 설정
max_retry = 2


def load_brief_text(campaign_id: str = "CMP02") -> str:
    """캠페인 ID로 브리프 1건을 읽어 LLM에 넣을 한 줄 텍스트로 만든다."""
    brief = pd.read_csv(DATA / "marketing_brief.csv")
    campaign = brief[brief["campaign_id"] == campaign_id].iloc[0]   # 캠페인 1건 선택
    return (
        f"캠페인명: {campaign.title} / 카테고리: {campaign.category} / "
        f"타깃: {campaign.target} / 예산: {campaign.budget:,}원 / "
        f"핵심혜택: {campaign.key_offer}"
    )


# 2. 구조화 출력 스키마
class Plan(BaseModel):
    """Planner가 만드는 실행 계획(구조화 출력 스키마)."""
    subtasks: list[str] = Field(description="이 캠페인을 위해 필요한 하위 작업 3~4개")


# 3. Planner 함수
PLANNER_SYSTEM = (
    "너는 마케팅 캠페인 '기획 설계자(Planner)'다. "
    "주어진 캠페인 브리프를 보고, 실행에 필요한 하위 작업을 3~4개로 쪼개라. "
    "작업은 서로 겹치지 않게, 한 문장 명령형으로 작성하라. 실행은 하지 마라."
)

def plan(llm, brief_text: str) -> list[str]:
    """브리프를 보고 하위 작업 리스트(JSON)로 분해한다."""
    planner = llm.with_structured_output(Plan)   # 출력을 Plan 스키마로 강제
    result = planner.invoke([
        SystemMessage(PLANNER_SYSTEM),
        HumanMessage(f"[캠페인 브리프]\n{brief_text}"),
    ])
    return result.subtasks


# 4. Worker 함수
WORKER_SYSTEM = (
    "너는 마케팅 '실무 작업자(Worker)'다. "
    "주어진 캠페인 브리프 맥락에서, 지정된 '하나의 작업'만 구체적으로 수행하라. "
    "결과는 5줄 이내로 실무에 바로 쓸 수 있게 작성하라."
)

def work(llm, brief_text: str, subtask: str) -> str:
    """하나의 하위 작업만 받아 구체적으로 수행한 결과를 반환한다."""
    result = llm.invoke([
        SystemMessage(WORKER_SYSTEM),
        HumanMessage(f"[캠페인 브리프]\n{brief_text}\n\n[수행할 작업]\n{subtask}"),
    ])
    return result.content

#######################################################################
# 교안3. 재시도 래퍼 — work_with_retry
# 5. 재시도 제어 및 방어막 함수
def work_with_retry(llm, brief_text: str, subtask: str, idx: int, total: int, force_fail: bool = False):
    """work() 를 감싸 최대 max_retry 회 재시도. (성공여부, 결과 or 오류메시지) 반환."""
    for attempt in range(1, max_retry + 2):   # 1, 2, 3 (최초 + 재시도 2회)
        try:
            print(f"   작업 {idx}/{total} 수행 중 (시도 {attempt})...")
            
            # 시연용 테스트: 특정 작업 인덱스는 강제로 예외 발생
            if force_fail:
                raise RuntimeError("의도적인 시연용 API 연결 실패 에러")
                
            out = work(llm, brief_text, subtask)
            return True, out                  # 성공 → (True, 산출물)
        except Exception as e:                # 타임아웃·네트워크·파싱 등 모든 실패 흡수
            print(f"     [실패] {type(e).__name__}: {e}")
            if attempt <= max_retry:
                print(f"     → 재시도합니다 ({attempt}/{max_retry})")
            else:
                print(f"     → 최대 재시도 초과. 이 작업은 스킵합니다.")
                return False, f"{type(e).__name__}: {e}"   # 실패 → (False, 오류메시지)

=========================================================================================
# 교안4. 견고한 오케스트레이터
# 6. 견고한 오케스트레이터
def run_campaign_robust(brief_text: str, fail_indices=None) -> str:
    """계획 → (재시도 포함) 실행 → 취합. 실패 작업은 스킵하고 끝까지 진행한다."""
    fail_indices = set(fail_indices or [])    # 시연용: 일부러 실패시킬 작업 번호
    llm_plan = get_chat(temperature=0)
    llm_work = get_chat(temperature=0.5)

    print("[1] Planner 작업 분해 중...")
    subtasks = plan(llm_plan, brief_text)
    total = len(subtasks)
    
    print("\n[2] Worker 실행 및 재시도 검증 중...")
    outputs = []        # (작업, 산출물) — 성공한 것만
    failed = []         # (번호, 작업, 오류) — 스킵한 것

    for i, t in enumerate(subtasks, 1):
        # fail_indices에 속하면 일부러 예외를 발생시키도록 전달
        is_target_fail = i in fail_indices
        ok, info = work_with_retry(llm_work, brief_text, t, i, total, force_fail=is_target_fail)
        if ok:
            outputs.append((t, info))
            print(f"   작업 {i}/{total} 완료\n")
        else:
            failed.append((i, t, info))       # 스킵하고 다음 작업으로 진행
            print(f"   작업 {i}/{total} 스킵됨\n")

    # 취합 — 성공분 + 미완료 목록
    print(f"[3] 결과 취합 (성공 {len(outputs)}개 / 실패 {len(failed)}개 / 전체 {total}개)")
    report = [f"# 캠페인 실행안\n\n> {brief_text}\n"]
    for i, (t, out) in enumerate(outputs, 1):
        report.append(f"## {i}. {t}\n{out}\n")
    if failed:
        report.append("## ⚠️ 미완료(재시도 후 스킵된) 작업")
        for i, t, err in failed:
            report.append(f"- {t} — {err}")
    return "\n".join(report)

####################################################################################
# 교안5. 실행 — 일부러 실패시켜 시연
if __name__ == "__main__":
    brief_text = load_brief_text("CMP02")
    print("(2번 작업은 일부러 매번 실패시켜 재시도·스킵을 보여줍니다)\n")
    report = run_campaign_robust(brief_text, fail_indices=[2])
    print("=" * 60)
    print(report)