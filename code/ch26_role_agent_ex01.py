# -*- coding: utf-8 -*-
# 실행: python code/ch26_role_agent_review.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat

# 기존 26강 로직을 그대로 재사용 (계획·실행)
from ch26_role_agent import load_brief_text, plan, work

from langchain_core.messages import SystemMessage, HumanMessage

# [추가] reviewer 역할 — '실행은 하지 말고, 전체를 검토만 하라'
REVIEWER_SYSTEM = (
    "너는 마케팅 캠페인 '검토자(Reviewer)'다. "
    "주어진 캠페인 실행안 전체를 읽고, 빠졌거나 더 보완하면 좋을 점을 "
    "구체적으로 3가지 이상 짚어라. 각 항목은 한 문장으로, 실무에 바로 반영할 수 있게 써라. "
    "새 실행안을 작성하지 말고, 검토 의견만 제시하라."
)


def review(llm, report: str) -> str:
    """완성된 실행안을 검토해 개선점 3가지 이상을 반환한다."""
    result = llm.invoke([
        SystemMessage(REVIEWER_SYSTEM),
        HumanMessage(f"[검토할 캠페인 실행안]\n{report}"),
    ])
    return result.content


def run_campaign_with_review(brief_text: str) -> str:
    """계획 → 실행 → 취합 → (추가) 검토."""
    llm_plan = get_chat(temperature=0)
    llm_work = get_chat(temperature=0.5)
    llm_review = get_chat(temperature=0)     # 검토는 일관성 있게 → 0

    # 1) 계획  2) 실행  3) 취합
    subtasks = plan(llm_plan, brief_text)
    outputs = [(t, work(llm_work, brief_text, t)) for t in subtasks]
    report = [f"# 캠페인 실행안\n\n> {brief_text}\n"]
    for i, (t, out) in enumerate(outputs, 1):
        report.append(f"## {i}. {t}\n{out}\n")
    final = "\n".join(report)

    # 4) 검토 단계 추가
    opinion = review(llm_review, final)
    final += f"\n## 🔍 검토 의견\n{opinion}\n"
    return final


if __name__ == "__main__":
    brief_text = load_brief_text("CMP02")
    print(run_campaign_with_review(brief_text))