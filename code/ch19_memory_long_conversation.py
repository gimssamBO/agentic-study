import pathlib
import sys

# 1. 시스템 경로 설정 (공통 모듈 common 위치 참조)
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages
from langgraph.checkpoint.memory import InMemorySaver


# =====================================================================
# 1. 에이전트 생성 및 대화 관리 함수
# =====================================================================

def build_agent():
    """단기기억(InMemorySaver)을 붙인 상담 에이전트를 생성한다."""
    llm = get_chat(temperature=0.3)
    agent = create_agent(
        llm,
        tools=[],  # 단기기억 테스트용으로 도구 미사용
        system_prompt="너는 승승장구몰의 친절한 CS 상담원이다. 한국어 존댓말로 답하라.",
        checkpointer=InMemorySaver(),  # 세션별 대화 기록을 보존하는 인메모리 체크포인터
    )
    return agent


def chat(agent, text: str, config: dict):
    """한 번의 대화 턴을 실행하며 config 내 thread_id로 사용자 세션을 식별한다."""
    result = agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
    return result, result["messages"]


# =====================================================================
# 2. 대화 메시지 트리밍(Trimming) 및 요약/압축(Summarizing) 함수
# =====================================================================

def trim_recent(messages, keep=5):
    """
    최근 대화 메시지만 잘라내어 남긴다.
    - include_system=True: 시스템 프롬프트(SystemMessage)는 삭제하지 않고 항상 최상단에 유지.
    - start_on="human": 슬라이싱 후 첫 시작 메시지가 사용자(HumanMessage)가 되도록 경계 정제.
    - keep=5: 시스템 메시지 1개 + 최근 대화 메시지 4개 = 총 5개 보존.
    """
    return trim_messages(
        messages,
        max_tokens=keep,       # token_counter가 len이므로 '메시지 개수' 기준 처리
        strategy="last",       # 가장 최근(last) 메시지 위주로 보존
        token_counter=len,     # 메시지 객체 수 카운팅
        include_system=True,   # 시스템 프롬프트 삭제 방지 (true -> True 교정)
        start_on="human",      # 사용자 질문부터 시작하도록 슬라이싱
    )


def summarize_old(messages, keep_recent=4):
    """
    최근 keep_recent개의 대화는 원본대로 유지하고, 그 이전의 오래된 대화 기록은
    LLM을 호출하여 한 줄의 요약문(SystemMessage)으로 압축·치환한다.
    """
    # 1) 시스템 메시지(SystemMessage)와 일반 대화 메시지 분리
    sys_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    convo = [m for m in messages if not isinstance(m, SystemMessage)]
    
    # 2) 보존할 최근 대화 수보다 적거나 같으면 압축 없이 원본 반환
    if len(convo) <= keep_recent:
        return messages

    # 3) 오래된 대화(old)와 최근 대화(recent) 분리
    old, recent = convo[:-keep_recent], convo[-keep_recent:]
    
    # 4) 오래된 대화를 대화록 형태의 텍스트로 재구성
    transcript = "\n".join(
        f"{'사용자' if isinstance(m, HumanMessage) else '상담원'}: {m.content}"
        for m in old
    )
    
    # 5) LLM을 이용해 오래된 대화록 한 줄 요약 수행
    summary = get_chat(temperature=0).invoke(
        "다음 상담 대화를 한국어 한 문장으로 요약하라.\n\n" + transcript
    ).content

    # 6) 요약문을 새로운 SystemMessage 객체로 생성 (메모리 절감)
    압축 = SystemMessage(content=f"[이전 대화 요약] {summary}")
    
    # 7) [기존 시스템 메시지] + [압축된 이전 대화 요약] + [최근 대화] 조합으로 반환
    return sys_msgs + [압축] + recent


# =====================================================================
# 3. 테스트 실행 및 결과 출력
# =====================================================================

if __name__ == "__main__":
    # 테스트용 대화 데이터 세트 구성 (시스템 메시지 1개 + 대화 메시지 12개 = 총 13개)
    demo_msgs = [
        SystemMessage(content="너는 승승장구몰 cs 상담원이다."),
        HumanMessage(content="배송 문의합니다."),
        AIMessage(content="네, 배송 관련해서 어떤 점이 궁금하신가요?"),
        HumanMessage(content="환불 절차도 알려주세요."),
        AIMessage(content="환불은 수령 후 7일 이내 신청 가능합니다."),
        HumanMessage(content="멤버십 혜택은 뭐가 있나요?"),
        AIMessage(content="등급별 적립금 및 할인 쿠폰 혜택이 제공됩니다."),
        HumanMessage(content="쿠폰 등록은 어디서 하나요?"),
        AIMessage(content="마이페이지 > 쿠폰함에서 등록 가능합니다."),
        HumanMessage(content="배송비는 얼마인가요?"),
        AIMessage(content="3만원 이상 구매 시 무료배송입니다."),
        HumanMessage(content="오늘 주문하면 언제 오나요?"),
        AIMessage(content="보통 다음 날 발송됩니다."),
    ]

    # [1] 메시지 트리밍(Trimming) 테스트
    # 시스템 메시지 1개 + 최근 대화 4개 = 총 5개 유지
    trimmed = trim_recent(demo_msgs, keep=5)
    print(f"[원본] 메시지 {len(demo_msgs)}개 → [트리밍] {len(trimmed)}개 (시스템 1 + 최근 4)")

    # [2] 메시지 요약/압축(Summarize) 테스트
    # 최근 4개 유지, 이전 8개 대화는 요약문 1개로 압축 -> 총 6개 메시지로 재구성
    summarized = summarize_old(demo_msgs, keep_recent=4)
    print(f"[압축] 메시지 {len(demo_msgs)}개 → {len(summarized)}개")

    # [3] 요약/압축 결과 리스트 상세 출력
    print("\n[요약/압축 결과 상세보기]")
    for m in summarized:
        if isinstance(m, SystemMessage):
            print(f"- systemmessage: {m.content}")
        elif isinstance(m, HumanMessage):
            print(f"- humanmessage: {m.content}")
        elif isinstance(m, AIMessage):
            print(f"- aimessage: {m.content}")