# 실행: python code/ch08_planning.py


from common import get_chat, DATA

# get_chat = common.py가 만들어 주는 LangChain ChatModel (ChatGoogleGenerativeAI, gemini-2.5-flash)
# llm = get_chat(provider="gemini")
llm = get_chat()

#-------------------------------------------------------------------



import pandas as pd
from langchain_core.tools import tool
from common import DATA

tasks_df = pd.read_csv(DATA / "project_tasks.csv")

@tool
def list_tasks(status: str = "전체") -> str:
    """신상품 출시 프로젝트의 작업 목록을 상태별로 조회한다.
    status 에 '완료'/'진행중'/'대기' 를 넣으면 해당 상태만, '전체'면 모든 작업을 반환한다.
    각 작업의 담당팀(team)과 마감일(due_date)도 함께 돌려준다."""
    df = tasks_df
    if status != "전체":
        df = df[df["status"] == status]
    if df.empty:
        return f"'{status}' 상태인 작업이 없습니다."
    lines = [
        f"- [{r.status}] {r.task_id} {r.task_name} (담당:{r.team}, 마감:{r.due_date})"
        for r in df.itertuples()
    ]
    return "\n".join(lines)

# -----------------------------------------------------------------

from langchain.agents import create_agent

planning_agent = create_agent(
    llm,                          # 사용할 모델
    tools=[list_tasks],           # 도구 목록
    system_prompt="너는 승승장구몰의 프로젝트 매니저다. list_tasks 도구로 진행상황을 확인하고 한국어로 답하라.",
)


q = "신상품 출시 프로젝트 진행상황을 정리하고, 지금 가장 먼저 시작해야 할 대기 작업을 하나 추천해줘."

result = planning_agent.invoke({"messages": [{"role": "user", "content": q}]})

# 결과의 마지막 메시지가 최종 답변
print(result["messages"][-1].content)

 #print(dir(result["messages"][-1].content[0]))



# print(result["messages"][-1].content[0]['text'])
