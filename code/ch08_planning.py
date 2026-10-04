# 실행: python code/ch08_planning.py
import pandas as pd
from common import get_chat, DATA
from langchain_core.tools import tool
from langchain.agents import create_agent

# 1. LLM 모델 초기화 (OpenAI 사용)
llm = get_chat(provider="openai")

# 2. 데이터 로드 및 도구 정의
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


# 3. 에이전트 생성
planning_agent = create_agent(
    llm,
    tools=[list_tasks],
    system_prompt="너는 승승장구몰의 프로젝트 매니저다. list_tasks 도구로 진행상황을 확인하고 한국어로 답하라.",
)

# 4. 실행
q = "신상품 출시 프로젝트 진행상황을 정리하고, 지금 가장 먼저 시작해야 할 대기 작업을 하나 추천해줘."
result = planning_agent.invoke({"messages": [{"role": "user", "content": q}]})

# 5. 결과 파싱 및 출력 (문자열 및 리스트 포맷 모두 대응)
# create_agent가 반환한 메시지 목록에서 마지막 메시지(에이전트의 최종 응답)의 content를 꺼낸다
# LangChain 버전/모델에 따라 content가 문자열일 수도, 리스트(멀티파트)일 수도 있어 분기 처리 필요
last_content = result["messages"][-1].content

if isinstance(last_content, list):
    # content가 리스트인 경우: 각 파트가 {"type": "text", "text": "..."} 형태의 dict일 수 있음
    # dict인 파트에서만 "text" 키를 꺼내 이어붙이고, dict가 아닌 파트(예: 이미지 등)는 무시
    final_text = "".join(
        part.get("text", "") for part in last_content if isinstance(part, dict)
    )
else:
    # content가 이미 단순 문자열인 경우: 그대로 사용
    final_text = last_content

# 두 경우 모두 처리된 최종 텍스트만 출력
print(final_text)