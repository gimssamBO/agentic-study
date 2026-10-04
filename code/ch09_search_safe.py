"""
LangChain Agent 실습 - 시장조사 에이전트 (안전한 검색 도구 버전)
===========================================================
실행: python ch09_search_safe.py

이 파일에서 비교하는 두 가지 방식
----------------------------------
PART 1. 에이전트가 스스로 검색 도구를 호출 (create_agent + web_search 도구)
         → 검색 여부/검색어 선택을 LLM이 알아서 판단
PART 2. 우리가 직접 safe_search()로 검색 → 그 결과를 프롬프트에 넣어 LLM 호출
         → '신중한 요약'과 '교차확인'처럼, 검색·검증 절차를 우리가 직접 설계하고
           통제하고 싶을 때 쓰는 방식

두 방식 모두 검색 로직은 safe_search() 하나를 공유합니다. (web_search는
safe_search를 감싸서 에이전트가 도구로 쓸 수 있게 만든 것뿐입니다.)

ch09_search.py와의 차이
------------------------
ch09_search.py는 langchain_community의 DuckDuckGoSearchResults를 그대로 썼습니다.
이 버전은 검색 백엔드가 네트워크/DNS 오류를 던져도 죽지 않도록, ddgs를 직접
호출하고 try/except로 감싼 커스텀 함수(safe_search)를 사용합니다. (deprecated
경고도 함께 해결됩니다.)

이번 실습에서 배우는 것
-----------------------
1) @tool 데코레이터로 나만의 검색 도구를 직접 만드는 법
2) 도구 안에서 예외를 잡아 에이전트가 죽지 않고 계속 동작하게 만드는 법
3) create_agent로 '검색 도구를 쓸 수 있는' 에이전트를 만드는 법
4) invoke() vs stream()의 차이
   - invoke(): 에이전트가 내부에서 검색→추론을 몇 번 반복하든, 최종 답만 한 번에 받는다
   - stream(): 매 단계(질문 → 도구 호출 → 검색 결과 → 최종 답)를 순서대로 볼 수 있어
     디버깅·수업용으로 유용하다
5) 에이전트에게 맡기지 않고, 검색→요약→교차확인 절차를 우리가 직접 코드로
   설계하는 방식 (PART 2)

사전 준비
---------
    pip install langchain ddgs

common.py는 이전 실습에서 만든 get_chat() 헬퍼가 있는 모듈이 같은 폴더에
있다고 가정합니다. get_chat(provider=..., temperature=...)처럼 provider/온도를
지정할 수 있다고 가정합니다.
"""

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

from langchain.agents import create_agent
from langchain.tools import tool
from ddgs import DDGS
from common import get_chat

llm = get_chat()


# ── 공통 검색 함수 (PART 1, PART 2 모두 이것 하나를 공유) ─────
def safe_search(query: str, max_results: int = 5) -> str:
    """DuckDuckGo로 검색한 뒤, 제목+본문 스니펫+출처를 하나의 문자열로 합쳐 반환한다.
    네트워크/DNS 오류 등으로 검색이 실패해도 예외를 던지지 않고 문자열로 돌려준다."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        # 여기서 잡아서 문자열로 돌려줘야, 이 함수를 쓰는 쪽(에이전트든 직접 호출이든)이
        # 예외로 죽지 않고 상황에 맞게 답을 이어갈 수 있다.
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


search = web_search  # ch09_search.py의 search 변수명과 맞춰 이후 코드는 그대로 재사용

# ── 도구 단독 테스트 ─────────────────────────────────────────
# 에이전트 없이 도구 자체가 잘 동작하는지 먼저 확인해본다.
print("[도구 단독 테스트]")
print(search.invoke("무선 이어버드 트렌드"))
print()

# ── 에이전트 생성 ────────────────────────────────────────────
search_agent = create_agent(
    llm,
    tools=[search],  # 검색 도구 하나
    system_prompt=(
        "너는 승승장구몰의 시장조사 담당자다. "
        "필요하면 검색 도구로 최신 정보를 찾아 한국어로 요약하라. "
        "검색 결과가 '(검색 실패: ...)' 또는 '(검색 결과 없음)'이면, 지어내지 말고 "
        "'확인 필요'라고 답하라."
    ),
)

q = "요즘 인기 있는 무선 이어폰 트렌드를 조사해서 핵심만 3가지로 요약해줘."
# q = "오늘 날짜 알려줘"  # 검색이 필요 없는 질문 - 에이전트가 도구를 안 부르는지 비교해보기 좋다

# ── 방법 1: invoke() — 최종 답만 받음 (중간 과정 안 보임) ─────
# result = search_agent.invoke({"messages": [{"role": "user", "content": q}]})
# print(result["messages"][-1].content)

# ── 방법 2: stream() — 매 단계를 순서대로 확인 (중간 과정 보임) ─
print("[에이전트 실행 - 단계별 확인]")
for step in search_agent.stream({"messages": [{"role": "user", "content": q}]}, stream_mode="values"):
    step["messages"][-1].pretty_print()


# ══════════════════════════════════════════════════════════════
# PART 2. 우리가 직접 검색 → 프롬프트에 넣어 호출하는 방식
#          (신중한 요약 + 교차확인)
#   - PART 1은 검색 여부·검색어 선택을 에이전트(LLM)가 알아서 판단
#   - 아래 방식은 검색 → 요약 → 재검색 → 검증까지 절차를 우리가 직접 설계·통제
#   - 검색은 위에서 만든 safe_search()를 그대로 재사용
# ══════════════════════════════════════════════════════════════
def summarize_with_caution(question: str, evidence: str) -> str:
    """검색 근거를 받아, 출처가 불충분하면 '확인 필요'라고 답하도록 신중히 요약한다."""
    answer_llm = get_chat(provider="openai", temperature=0.3)
    prompt = (
        "너는 승승장구몰의 시장조사 담당자다. 아래 검색 결과만 근거로 질문에 답하라.\n"
        "[규칙] 검색 결과에서 근거를 찾을 수 없거나 출처가 불충분하면, 지어내지 말고 "
        "반드시 '확인 필요'라고 답하라. 확실한 부분만 한국어로 간결히 요약하라.\n\n"
        f"질문: {question}\n\n검색 결과:\n{evidence}"
    )
    return answer_llm.invoke(prompt).content


def cross_check(claim: str) -> str:
    """핵심 주장 1개를 다른 검색어로 재검색해 교차확인 결과를 돌려준다."""
    requery = f"{claim} 사실 확인 후기 비교"      # 다른 각도의 검색어
    evidence2 = safe_search(requery)
    verify_llm = get_chat(provider="openai", temperature=0.3)
    prompt = (
        "아래 두 번째 검색 결과가 다음 주장을 뒷받침하는지 판단하라.\n"
        "뒷받침되면 '교차확인됨', 근거가 약하거나 상반되면 '확인 필요'로 시작해 "
        "한 문장으로 한국어로 답하라.\n\n"
        f"주장: {claim}\n\n두 번째 검색 결과:\n{evidence2}"
    )
    return verify_llm.invoke(prompt).content


print()
print("=" * 60)
print("[PART 2] 직접 검색 + 프롬프트 방식")
print("=" * 60)

question = "요즘 인기 있는 무선 이어버드 트렌드를 핵심만 알려줘."

# STEP 1: 1차 검색
evidence = safe_search("무선 이어버드 최신 트렌드 2026")

# STEP 2: 신뢰성 강조 요약(불충분하면 '확인 필요')
summary = summarize_with_caution(question, evidence)
print(summary)

# STEP 3~4: 핵심 주장 1개를 골라 교차확인
claim = "노이즈 캔슬링(ANC) 탑재가 무선 이어버드의 핵심 트렌드다."
verdict = cross_check(claim)
print("교차확인 결과:", verdict)