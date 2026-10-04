import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

llm = get_chat(provider="openai")

# - encoding="utf-8-sig": 한글 파일 깨짐 방지
orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")
inventory = pd.read_csv(DATA / "inventory.csv", encoding="utf-8-sig")

# 날짜 컬럼 형변환 및 연-월(YYYY-MM) 파생 변수 생성
orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["month"] = orders["order_date"].dt.strftime("%Y-%m")


# 교안 2. 검증/정규화 헬퍼
'''
정규화(normalize): 고칠 수 있는 건 고침 (c1 → C1, 공백 제거)
검증(validate): 못 고치는 건 오류로 (C1은 4자리가 아니므로 오류)
'''
import re
# 고객ID 형식: 대문자 C + 숫자 4자리 (예: C0001) 
# => r=파이썬 이스케이프 인식 못하도록 붙이는 접두사 | ^=문자열 시작 | C=시작하는 C중에 | d=숫자로 {4}=4자리 | $=문자열 끝
CUSTOMER_ID_RE = re.compile(r"^C\d{4}$")

def validate_customer_id(customer_id: str):
    """고객ID를 정규화(공백 제거·대문자화)하고 'C+4자리' 형식을 검사한다.
    반환: (정규화된_ID, 오류문자열). 오류가 없으면 오류문자열은 None."""
    cid = (customer_id or "").strip().upper()    # ① 정규화: 공백 제거 + 대문자
    if not CUSTOMER_ID_RE.match(cid):            # ② 검증: 형식 검사
        return None, (
            f"[입력오류] 고객ID '{customer_id}' 형식이 올바르지 않습니다. "
            f"'C' 다음 숫자 4자리(예: C0001) 형태로 입력해 주세요."
        )
    return cid, None

def normalize_product_name(name: str) -> str:
    """상품명의 양끝 공백 제거 + 연속 공백을 하나로 정리한다."""
    return re.sub(r"\s+", " ", (name or "").strip())


# 교안 4. 도구 안에서 검증 적용
@tool
def get_order_status(customer_id: str) -> str:
    """고객 ID(예: 'C0001')의 가장 최근 주문 상태를 조회한다."""
    cid, err = validate_customer_id(customer_id)   # 조회 전에 형식부터 검증
    if err:
        return err          # 형식 위반 → 친절한 오류 문자열 반환
    df = orders[orders["customer_id"] == cid]      # 정규화된 cid로 조회
    if df.empty:
        return f"[조회실패] {cid} 고객의 주문 내역이 없습니다."
    
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

# - 도구 수행 결과가 [조회실패] 또는 [도구오류]일 때 에이전트가 수행해야 할 행동(대체 안내) 지정
SYSTEM = (
    "너는 승승장구몰의 운영 비서다. 도구를 사용해 답하라.\n"
    "도구 결과가 '[조회실패]' 또는 '[도구오류]'로 시작하면, 그 사실을 사용자에게\n"
    "솔직히 알리고 멈추지 말고 대체 안내를 하라. 예: 올바른 입력 형식 안내,\n"
    "다른 식별 정보 요청, 고객센터(1588-0000) 연결 안내. 답은 한국어로 한다."
)

agent = create_agent(llm, tools=TOOLS, system_prompt=SYSTEM)

# 교안 5. 실행 — 검증 동작 확인
samples = ["C0001", "c1", " C0156 ", "X0001", ""]
for s in samples:
    cid, err = validate_customer_id(s)
    print(f"입력 {s!r:>10} -> 정규화 {cid!r} / 오류: {err}")