# -*- coding: utf-8 -*-
# 실행: python code/ch26_ex_yaml.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat, DATA

import yaml                                     # pip install pyyaml
from ch26_role_agent import load_brief_text, Plan  # 데이터 로드·구조화 스키마(Plan) 재사용
from langchain_core.messages import SystemMessage, HumanMessage

# [핵심] 프롬프트를 코드가 아니라 yaml 파일에서 읽는다.
def load_prompts() -> dict:
    with open(DATA / "role_prompts.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)             # {'planner': ..., 'worker': ..., 'reviewer': ...}


prompts = load_prompts()


def plan(llm, brief_text: str) -> list[str]:
    planner = llm.with_structured_output(Plan)
    result = planner.invoke([
        SystemMessage(prompts["planner"]),          # ← yaml에서 읽은 프롬프트
        HumanMessage(f"[캠페인 브리프]\n{brief_text}"),
    ])
    return result.subtasks


def work(llm, brief_text: str, subtask: str) -> str:
    result = llm.invoke([
        SystemMessage(prompts["worker"]),           # ← yaml에서 읽은 프롬프트
        HumanMessage(f"[브리프]\n{brief_text}\n\n[작업]\n{subtask}"),
    ])
    return result.content


def review(llm, report: str) -> str:
    result = llm.invoke([
        SystemMessage(prompts["reviewer"]),         # ← yaml에서 읽은 프롬프트
        HumanMessage(f"[검토할 캠페인 실행안]\n{report}"),
    ])
    return result.content


def run_campaign(brief_text: str) -> str:
    # temperature 지정 시 키워드 인자로 전달하도록 수정
    llm_plan = get_chat(temperature=0)
    llm_work = get_chat(temperature=0.5)
    llm_review = get_chat(temperature=0)

    subtasks = plan(llm_plan, brief_text)
    report = [f"# 캠페인 실행안\n\n> {brief_text}\n"]
    for i, t in enumerate(subtasks, 1):
        report.append(f"## {i}. {t}\n{work(llm_work, brief_text, t)}\n")
    final = "\n".join(report)
    final += f"\n## 검토 의견\n{review(llm_review, final)}\n"
    return final


if __name__ == "__main__":
    print(run_campaign(load_brief_text("CMP02")))