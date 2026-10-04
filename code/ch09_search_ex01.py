import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from langchain.agents import create_agent
from langchain_community.tools import DuckDuckGoSearchResults
from common import get_chat

llm = get_chat(provider="openai")
search = DuckDuckGoSearchResults()
agent = create_agent(llm, tools=[search],
                     system_prompt="너는 승승장구몰의 시장조사 담당자다. 필요하면 검색해 한국어로 요약하라.")

q = "무선 이어버드 시장의 최근 경쟁사 프로모션을 3가지 조사해줘."

try:
    for step in agent.stream({"messages": [{"role": "user", "content": q}]}, stream_mode="values"):
        msg = step["messages"][-1]
        # LLM이 만든 검색어(도구 호출)를 출력
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                print("🔎 LLM이 만든 검색어:", tc["args"])
        msg.pretty_print()
except Exception as e:
    print("검색 중 오류:", e)