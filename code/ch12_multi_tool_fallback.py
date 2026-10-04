import sys, pathlib
# 현재 파일이 위치한 디렉토리를 파이썬 모듈 검색 경로(sys.path)에 추가하여 common 모듈 참조 가능하게 설정
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

# 1. LLM 객체 생성 (OpenAI 모델 사용)
llm = get_chat(provider="openai")

# 2. 데이터셋 로드 (모듈 로드 시 1회만 수행하여 I/O 성능 최적화)
# - encoding="utf-8-sig": 한글 파일 깨짐 방지
orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")
inventory = pd.read_csv(DATA / "inventory.csv", encoding="utf-8-sig")

# 날짜 컬럼 형변환 및 연-월(YYYY-MM) 파생 변수 생성
orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["month"] = orders["order_date"].dt.strftime("%Y-%m")


# 3. 에이전트 도구(Tool) 정의
@tool
def get_order_status(customer_id: str) -> str:
    """고객 ID의 가장 최근 주문 1건의 상태를 조회한다."""
    # 해당 고객의 주문 내역 필터링
    df = orders[orders["customer_id"] == customer_id]
    
    # 예외 처리: 고객 데이터가 없는 경우
    # 모델이 예외(Exception)로 중단되지 않고 폴백 처리할 수 있도록 명확한 텍스트 반환
    if df.empty:
        return f"[조회실패] {customer_id} 고객의 주문 내역이 없습니다. 고객ID를 다시 확인해 주세요."
    
    # 가장 최근 주문 날짜 기준 1건 추출
    latest_order = df.sort_values(by="order_date", ascending=False).iloc[0]
    order_date_str = latest_order['order_date'].strftime('%Y-%m-%d')
    return f"고객 {customer_id}님의 최근 주문({order_date_str}) 상태는 '{latest_order['status']}'입니다."


@tool
def get_stock(product_id: str) -> str:
    """product_id의 현재 재고 수량을 조회한다."""
    try:
        # 해당 상품의 재고 정보 필터링
        df = inventory[inventory["product_id"] == product_id]
        if df.empty:
            return f"[조회실패] {product_id} 의 재고 정보가 없습니다."
        
        stock_cnt = df.iloc[0]["stock"]
        return f"상품 {product_id}의 현재 재고는 {stock_cnt}개입니다."
    except Exception as e:
        # 실행 중 발생하는 예외도 문자열 형태의 에러 메시지로 감싸서 반환
        return f"[도구오류] 재고 조회 중 문제가 발생했습니다: {e}"


# 에이전트에게 전달할 도구 목록
TOOLS = [get_order_status, get_stock]

# 4. 시스템 프롬프트 작성
# - 도구 수행 결과가 [조회실패] 또는 [도구오류]일 때 에이전트가 수행해야 할 행동(대체 안내) 지정
SYSTEM = (
    "너는 승승장구몰의 운영 비서다. 도구를 사용해 답하라.\n"
    "도구 결과가 '[조회실패]' 또는 '[도구오류]'로 시작하면, 그 사실을 사용자에게\n"
    "솔직히 알리고 멈추지 말고 대체 안내를 하라. 예: 올바른 입력 형식 안내,\n"
    "다른 식별 정보 요청, 고객센터(1588-0000) 연결 안내. 답은 한국어로 한다."
)

# 5. 에이전트 객체 생성
agent = create_agent(llm, tools=TOOLS, system_prompt=SYSTEM)

# 6. 테스트용 질문 리스트 (정상 데이터 vs 폴백 유도 데이터)
questions = [
    "C0001 고객의 최근 주문 상태를 알려줘.",  # 정상 케이스
    "C9999 고객의 최근 주문 상태를 알려줘.",  # 폴백 케이스 (존재하지 않는 고객 ID)
]

# 7. 질문을 하나씩 순회하며 에이전트 호출 (배열을 통째로 전달하면 400 에러 발생)
for q in questions:
    # OpenAI API 규격에 맞춰 content 항목에 단일 문자열(str) 전달
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})
    
    # 마지막 반환 메시지(최종 답변) 출력
    print(f"질문: {q}")
    print(f"답변: {result['messages'][-1].content}\n" + "="*50)