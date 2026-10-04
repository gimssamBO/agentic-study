import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

def data_quality_report(df: pd.DataFrame) -> None:
    """주문 DataFrame을 받아 분석 전에 확인할 품질 지표를 표로 출력한다."""
    # ① 총 행수
    print("[1] 총 행수:", f"{len(df):,}행")

    # ② 컬럼별 결측치 수
    print("[2] 컬럼별 결측치 수")
    for col, cnt in df.isnull().sum().items():
        mark = "  <-- 결측 있음" if cnt > 0 else ""
        print(f"  - {col:<14}: {cnt:>5,}개{mark}")

    # ③ 중복행 수
    print("[3] 중복행 수:", f"{int(df.duplicated().sum()):,}행")

    # ④ 음수 amount 수
    neg = int((df["amount"] < 0).sum())
    print("[4] 음수 amount 행:", f"{neg:,}행  [경고] 집계 전 제외 검토")

    # ⑤ quantity 이상치
    outlier = df[df["quantity"] >= 999]
    print("[5] quantity 이상치(999 이상):", f"{len(outlier):,}행")

    # ⑥ status 값 분포
    print("[6] status 값 분포")
    for status, cnt in df["status"].value_counts(dropna=False).items():
        print(f"  - {str(status):<8}: {cnt:>6,}건 ({cnt/len(df)*100:5.1f}%)")

# 실행 결과
orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")
data_quality_report(orders)
        