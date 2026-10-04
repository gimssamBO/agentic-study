import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

llm = get_chat(provider="openai")
tasks_df = pd.read_csv(DATA / "project_tasks.csv", encoding="utf-8-sig")

@tool
def list_tasks(status: str = "전체") -> str:
    """프로젝트 작업을 상태별로 조회한다(마감 임박순 정렬). '대기'/'진행중'/'완료'/'전체'."""
    df = tasks_df
    if status != "전체":
        df = df[df["status"] == status]
    if df.empty:
        return f"'{status}' 상태인 작업이 없습니다."
    df = df.sort_values("due_date")   # ← 마감 임박순 정렬 추가
    lines = [f"- [{r.status}] {r.task_name} (담당:{r.team}, 마감:{r.due_date})"
             for r in df.itertuples()]
    return "\n".join(lines)

agent = create_agent(llm, tools=[list_tasks],
                     system_prompt="너는 승승장구몰의 프로젝트 매니저다. list_tasks로 진행상황을 보고 한국어로 답하라.")

q = "지금 가장 먼저 시작해야 할 대기 작업을 하나 추천해줘."
result = agent.invoke({"messages": [{"role": "user", "content": q}]})
print(result["messages"][-1].content)