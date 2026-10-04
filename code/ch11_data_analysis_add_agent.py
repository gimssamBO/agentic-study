# 실행: python code/ch11_data_analysis.pyy
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

llm = get_chat()

# 주문·상품 데이터 로드
orders = pd.read_csv(DATA / "orders.csv")
products = pd.read_csv(DATA / "products.csv")

# 전처리: 날짜 타입 변환 + 월(YYYY-MM) 파생 컬럼 추가 → 월별 집계가 쉬워진다
orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["month"] = orders["order_date"].dt.strftime("%Y-%m")


@tool
def run_pandas(expr: str) -> str:
    """미리 로드된 주문 데이터로 pandas 식을 실행해 결과를 문자열로 반환한다.
    사용 가능한 객체:
      - orders : 주문 DataFrame. 컬럼 = order_id, order_date(datetime),
                 month('YYYY-MM'), customer_id, product_id, product_name,
                 category, quantity, unit_price, amount, channel,
                 status('배송완료'/'배송중'/'결제완료'/'취소'/'환불')
      - products : 상품 DataFrame (product_id, product_name, category, price, ...)
      - pd : pandas
    분석 주의사항:
      * 매출(amount) 집계는 보통 status가 '취소','환불'인 건을 제외한다.
      * amount 에 음수(환불 오류)나 quantity=999 같은 이상치가 섞여 있을 수 있다.
    예: "orders[orders['status']=='배송완료'].groupby('category')['amount']
         .sum().sort_values(ascending=False).head(3)"
    """
    allowed = {"orders": orders, "products": products, "pd": pd}  # 화이트리스트
    try:
        result = eval(expr, {"__builtins__": {}}, allowed)
    except Exception as e:
        return f"실행 오류: {e}"
    return str(result)

# 에이전트 호출
SYSTEM = (
    "너는 승승장구몰의 데이터 분석가다. 계산은 반드시 run_pandas 도구로만 하라.\n"
    "규칙:\n"
    "1) 매출(amount) 집계 시 status가 '취소','환불'인 행은 제외한다.\n"
    "2) quantity=999 처럼 비정상적으로 큰 값과 음수 amount는 이상치이므로,\n"
    "   집계 전에 적절히 제외하거나 사용자에게 언급한다.\n"
    "3) 최종 답변은 한국어로 간결하게, 숫자는 천단위 콤마를 붙여 설명한다."
)
agent = create_agent(llm, tools=[run_pandas], system_prompt=SYSTEM)

questions = [
    "배송완료된 주문 기준으로 카테고리별 매출 top3 알려줘.",   # 그룹화 + 정렬
    "전체 주문 중 환불 건수와 환불 비율(%)은?",              # 비율 계산
    "2026년 월별 매출 추이를 알려줘. (취소/환불 제외)",        # 시계열 집계
]


for q in questions:
    print("Q:", q)
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})
    print("A:", result["messages"][-1].content)
    print()

