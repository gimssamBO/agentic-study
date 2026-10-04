"""
LangChain Agent 실습 - 리서치 노트 자동 저장 (안전한 검색 도구 버전)
===========================================================
실행: python ch09_search_ex02_safe.py

ch09_search_ex02.py와의 차이
------------------------------
ch09_search_ex02.py는 langchain_community의 DuckDuckGoSearchResults를 그대로 썼습니다.
검색 백엔드가 DNS/네트워크 오류를 던지면 agent.invoke() 자체가 예외로 죽어서
답을 아예 만들지 못하고, 바깥의 try/except가 "검색 중 오류: ..."만 찍고 끝나버려
research_note.md에는 아무것도 저장되지 않는 문제가 있었습니다.

이 버전은 ddgs를 직접 호출하고 try/except로 감싼 커스텀 검색 도구(safe_search)를
써서, 검색이 실패해도 에이전트가 죽지 않고 "확인 필요"로 답을 만들어내며, 그
답도 정상적으로 research_note.md에 저장됩니다. (deprecated 경고도 해결됩니다.)

사전 준비
---------
    pip install langchain ddgs

common.py에 get_chat(), DATA가 이미 있다고 가정합니다.
(DATA: 노트를 저장할 데이터 폴더 경로, pathlib.Path)
"""

import sys, pathlib
from datetime import datetime
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

from langchain.agents import create_agent
from langchain.tools import tool
from ddgs import DDGS
from common import get_chat, DATA

llm = get_chat(provider="openai")


def safe_search(query: str, max_results: int = 5) -> str:
    """DuckDuckGo로 검색한 뒤, 제목+본문 스니펫+출처를 하나의 문자열로 합쳐 반환한다.
    네트워크/DNS 오류 등으로 검색이 실패해도 예외를 던지지 않고 문자열로 돌려준다."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        return f"(검색 실패: {e})"

    if not results:
        return "(검색 결과 없음)"

    lines = []
    for i, r in enumerate(results, start=1):
        title = r.get("title", "")
        body = r.get("body", "")
        href = r.get("href", "")
        lines.append(f"[{i}] {title}\n{body}\n출처: {href}")
    return "\n\n".join(lines)


@tool
def web_search(query: str) -> str:
    """웹에서 최신 정보를 검색한다. (에이전트가 도구로 쓸 수 있도록 safe_search를 감싼 것)"""
    return safe_search(query)


search = web_search

agent = create_agent(
    llm,
    tools=[search],
    system_prompt=(
        "너는 승승장구몰의 시장조사 담당자다. 필요하면 검색해 한국어로 요약하라. "
        "검색 결과가 '(검색 실패: ...)' 또는 '(검색 결과 없음)'이면, 지어내지 말고 "
        "'확인 필요'라고 답하라."
    ),
)

q = "요즘 인기 있는 무선 이어버드 트렌드를 3가지로 요약해줘."

try:
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})
    answer = result["messages"][-1].content
    print(answer)

    # 타임스탬프와 함께 append 저장
    note_path = DATA / "research_note.md"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")     # (현재 시각 문자열)
    with open(note_path, "a", encoding="utf-8") as f:     # "a" = append 모드
        f.write(f"\n## [{stamp}] {q}\n\n{answer}\n")
    print(f"\n저장 완료: {note_path}")
except Exception as e:
    print("검색 중 오류:", e)