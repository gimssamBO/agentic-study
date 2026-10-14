# -*- coding: utf-8 -*-
# 실행: python code/ch25_ex_three.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, DATA
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from ch25_multi_agent import search_products, search_faq   # policy_words 직접 정의로 변경

# 키워드 리스트 직접 정의 (ImportError 방지)
policy_words = ["환불", "배송", "교환", "AS", "a/s", "취소", "결제", "정책", "faq", "문의"]
competitor_words = ["경쟁사", "경쟁", "비교", "타사", "다른 쇼핑몰", "라이벌"]

competitor = pd.read_csv(DATA / "competitor_data.csv")   # company,main_category,rating,strength,weakness

@tool
def search_competitor(keyword: str) -> str:
    """키워드로 경쟁사 데이터(강점·약점·평점)를 조회한다."""
    hit = competitor[competitor.apply(
        lambda r: keyword in str(r["company"]) or keyword in str(r["main_category"]), axis=1)]
    if hit.empty:
        hit = competitor   # 못 찾으면 전체 요약
    return "\n".join(
        f"- {r.company}({r.main_category}, 평점 {r.rating}): 강점 {r.strength} / 약점 {r.weakness}"
        for r in hit.head(3).itertuples())

def build_three_agents():
    llm = get_chat(temperature=0)
    sales = create_agent(llm, tools=[search_products],
        system_prompt="너는 '상품 추천' 전문 상담원이다.")
    policy = create_agent(llm, tools=[search_faq],
        system_prompt="너는 '정책/faq 안내' 전문 상담원이다. faq 근거로만 답하라.")
    comp = create_agent(llm, tools=[search_competitor],
        system_prompt="너는 '경쟁사 분석' 전문가다. 경쟁사 데이터 근거로 비교 분석하라.")
    return llm, sales, policy, comp

def route_rule3(question: str) -> str:
    """3-way 규칙 라우터: competitor → policy → sales(기본) 순 우선순위."""
    if any(w in question for w in competitor_words):
        return "competitor"
    if any(w in question for w in policy_words):
        return "policy"
    return "sales"

def route_llm3(llm, question: str) -> str:
    msg = ("다음 질문을 한 단어로 분류: 경쟁사 비교면 'competitor', "
           "환불/배송 등 정책이면 'policy', 상품 추천이면 'sales'.\n"
           f"질문: {question}\n분류:")
    ans = llm.invoke(msg).content.strip().lower()
    for t in ("competitor", "policy", "sales"):
        if t in ans:
            return t
    return "sales"

def supervisor3(llm, agents, question, use_llm=False):
    target = route_llm3(llm, question) if use_llm else route_rule3(question)
    print(f"  [supervisor] '{question}' → {target} 에이전트로 라우팅")
    agent = agents[target]
    return agent.invoke({"messages": [{"role": "user", "content": question}]})["messages"][-1].content

if __name__ == "__main__":
    llm, sales, policy, comp = build_three_agents()
    agents = {"sales": sales, "policy": policy, "competitor": comp}
    for q in ["전자기기 추천해줘", "환불 며칠 이내?", "경쟁사랑 비교하면 어때?"]:
        print("=" * 60)
        print("고객:", q)
        print("답변:", supervisor3(llm, agents, q)[:150])