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

# 도구 단독 테스트
# 카테고리별 매출 top3 (배송완료 기준)
expr = "orders[orders['status']=='배송완료'].groupby('category')['amount'].sum().sort_values(ascending=False).head(3)"
print(run_pandas.invoke({"expr": expr}))