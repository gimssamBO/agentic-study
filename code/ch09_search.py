# 실행: python code/ch09_search.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from langchain.agents import create_agent
# DuckDuckGoSearchResults = 무료·키 불필요 웹 검색 도구(내부적으로 ddgs 패키지 사용)
from langchain_community.tools import DuckDuckGoSearchResults
from common import get_chat

llm = get_chat()
# DuckDuckGoSearchResults 는 그 자체로 LangChain 도구라 @tool 작성 없이 바로 쓴다
#  DuckDuckGoSearchResults() 처음 실행하면  설치창이 뜨는데 "예" 해주면 된다.
search = DuckDuckGoSearchResults()
print(search.invoke("무선 이어버드 트렌드"))

# 에이전트 생성
search_agent = create_agent(
    llm,
    tools=[search],   # 검색 도구 하나
    system_prompt="너는 승승장구몰의 시장조사 담당자다. 필요하면 검색 도구로 최신 정보를 찾아 한국어로 요약하라.",
)

### invoke() :최종 답만 받음(과정 안 보임)
q = "요즘 인기 있는 무선 이어폰 트렌드를 조사해서 핵심만 3가지로 요약해줘."
# q = "오늘 날짜 알려줘"
# result = search_agent.invoke({"messages": [{"role": "user", "content": q}]})
# print(result["messages"][-1].content)

# stream — 매 단계를 순서대로 (과정 보임)
for step in search_agent.stream({"messages": [{"role": "user", "content": q}]}, stream_mode="values"):
    step["messages"][-1].pretty_print()