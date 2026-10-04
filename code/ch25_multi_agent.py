#1. 공통 시작부와 데이터 로드

# -*- coding: utf-8 -*-
# 실행: python code/ch25_multi_agent.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat, DATA

import pandas as pd
from langchain_core.tools import tool         # 함수를 LLM이 쓸 수 있는 '도구'로 등록
from langchain.agents import create_agent

# [왜 멀티에이전트] 한 에이전트에 도구가 너무 많아지면 LLM이 '어느 도구를 언제 쓸지'
#   헷갈린다. 그래서 역할(추천/정책)별로 에이전트를 쪼개고(역할 분리), 질문이 들어오면
#   supervisor 가 알맞은 에이전트로 보낸다(라우팅). = '역할 분리 + 라우팅' 패턴.

products = pd.read_csv(DATA / "products.csv")   # product_id,product_name,category,price,cost,stock,rating
faq = pd.read_csv(DATA / "faq.csv")             # question,answer

###########################################
# 2. 역할별 도구 — 책임에 맞는 도구만
@tool
def search_products(category: str) -> str:
    """카테고리명을 받아 승승장구몰에서 평점 높은 상품 3개를 추천한다.

    @tool 데코레이터: 이 docstring 이 LLM에게 '도구 설명서'로 전달된다.
    LLM은 설명을 읽고 이 도구를 언제 호출할지 스스로 판단한다.
    """
    hit = products[products["category"].str.contains(category, na=False)]
    if hit.empty:
        return f"'{category}' 카테고리 상품을 찾지 못했습니다."
    top = hit.sort_values("rating", ascending=False).head(3)
    return "\n".join(
        f"- {r.product_name} ({r.price:,}원, 평점 {r.rating})"
        for r in top.itertuples()
    )


@tool
def search_faq(keyword: str) -> str:
    """키워드로 승승장구몰 FAQ에서 가장 관련 있는 답변을 찾는다."""
    hit = faq[faq["question"].str.contains(keyword, na=False)]
    if hit.empty:                       # 질문에 없으면 답변 본문에서도 검색
        hit = faq[faq["answer"].str.contains(keyword, na=False)]
    if hit.empty:
        return "관련 FAQ를 찾지 못했습니다."
    return "\n".join(f"Q. {r.question}\nA. {r.answer}" for r in hit.head(2).itertuples())


########################################
# 3. 역할별 에이전트 2개 생성
def build_agents():
    """역할별 에이전트 2개(추천/정책)를 생성해 반환한다(프롬프트·도구 분리).

    [왜 도구 분리] 추천 에이전트엔 search_products 만, 정책 에이전트엔 search_faq 만
    준다. 각 에이전트가 자기 책임의 도구만 보면 헷갈릴 일이 줄어 정확해진다.
    """
    llm = get_chat(temperature=0)   # [왜 0] 도구 선택·분류는 정해진 답이라 무작위성 제거

    sales_agent = create_agent(     # 추천 전문 에이전트
        llm,
        tools=[search_products],                              # 추천 도구만!
        system_prompt="너는 승승장구몰의 '상품 추천' 전문 상담원이다. "
               "상품 추천 외 질문은 답하지 말고 '정책 담당에게 문의하라'고 안내하라.",
    )
    policy_agent = create_agent(    # 정책/FAQ 전문 에이전트
        llm,
        tools=[search_faq],                                   # 정책 도구만!
        system_prompt="너는 승승장구몰의 '정책/FAQ 안내' 전문 상담원이다. "
               "환불·배송·교환·적립 등 정책만 답하고, 반드시 FAQ 근거로만 답하라.",
    )
    return llm, sales_agent, policy_agent


##############################################
#5. 에이전트 단독 테스트
if __name__ == "__main__":
    llm, sales_agent, policy_agent = build_agents()

    # 추천 에이전트 단독 테스트
    r = sales_agent.invoke({"messages": [{"role": "user", "content": "전자기기 추천해줘"}]})
    print("[추천 에이전트]", r["messages"][-1].content[:120])

    # 정책 에이전트 단독 테스트
    r = policy_agent.invoke({"messages": [{"role": "user", "content": "환불 며칠 이내?"}]})
    print("[정책 에이전트]", r["messages"][-1].content[:120])



##########################
  # 2. (A) 규칙 기반 라우터 — 빠르고 공짜  -  이방식은 약간 부정확함
    # supervisor: 여러 에이전트 중 '어디로 보낼지'를 결정하는 라우팅 담당.
POLICY_WORDS = ["환불", "교환", "배송", "취소", "적립", "포인트", "무료배송", "회원", "등급"]


def route_rule(question: str) -> str:
    """질문을 'policy' 또는 'sales' 로 분류한다(규칙 기반, 비용 0).

    [왜 규칙 라우터] 키워드 매칭은 LLM 호출이 없어 빠르고 공짜다.
    명확한 정책 단어가 있으면 굳이 LLM에 물어볼 필요가 없다.
    """
    return "policy" if any(w in question for w in POLICY_WORDS) else "sales"


###############################################
#3. (B) LLM 기반 라우터 — 애매한 질문까지 - 정확하지만 비용이 발생
def route_llm(llm, question: str) -> str:
    """LLM에게 분류만 시킨다. 'policy' 또는 'sales' 한 단어만 받는다.

    [왜 LLM 라우터] '가성비 좋은 거'처럼 키워드로 안 잡히는 애매한 질문은
    LLM의 의미 이해로 분류한다(비용은 들지만 정확). 규칙→LLM 2단계 전략.
    """
    msg = (
        "다음 고객 질문을 한 단어로 분류하라. "
        "환불/배송/교환/적립 등 정책이면 'policy', 상품 추천이면 'sales'.\n"
        f"질문: {question}\n분류(policy/sales):"
    )
    ans = llm.invoke(msg).content.strip().lower()
    return "policy" if "policy" in ans else "sales"

########################
# 4. Supervisor — 분류 후 위임
def supervisor(llm, sales_agent, policy_agent, question: str, use_llm: bool = False) -> str:
    """질문을 분류해 적절한 전문 에이전트에 위임하고 답을 돌려준다(라우팅의 핵심)."""
    target = route_llm(llm, question) if use_llm else route_rule(question)  # 라우터 선택
    agent = policy_agent if target == "policy" else sales_agent             # 위임 대상 결정
    print(f"  [Supervisor] '{question}' → {target} 에이전트로 라우팅")
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content   # 위임받은 에이전트의 최종 답변



##########################
#5. 실행
def main():
    llm, sales_agent, policy_agent = build_agents()
    questions = [
        "전자기기 카테고리에서 뭐 살만한 거 추천해줘",
        "환불은 며칠 안에 신청해야 해?",
        "무료배송 기준이 어떻게 돼?",
    ]
    for q in questions:
        print("=" * 60)
        print("고객:", q)
        print("답변:", supervisor(llm, sales_agent, policy_agent, q))      # 규칙 라우터
    print("=" * 60)
    print("고객: 가성비 좋은 거 없을까?")
    print("답변:", supervisor(llm, sales_agent, policy_agent,
                            "가성비 좋은 거 없을까?", use_llm=True))         # LLM 라우터


if __name__ == "__main__":
    main()