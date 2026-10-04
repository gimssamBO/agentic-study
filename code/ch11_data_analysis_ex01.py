import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from common import DATA

orders = pd.read_csv(DATA / "orders.csv", encoding="utf-8-sig")

def revenue_by_channel():
    """이상치·취소/환불을 제외한 채널별 평균 주문금액을 출력한다."""
    # 데이터 함정 제거 (02번 규칙)
    clean = orders[
        (~orders["status"].isin(["취소", "환불"]))   # 취소/환불 제외
        & (orders["quantity"] != 999)               # quantity 이상치 제외
        & (orders["amount"] >= 0)                    # 음수 금액 제외
    ]
    avg = clean.groupby("channel")["amount"].mean().sort_values(ascending=False)
    print("[채널별 평균 주문금액] (이상치·취소/환불 제외)")
    for channel, val in avg.items():
        print(f"  - {channel}: {int(val):,}원")

if __name__ == "__main__":
    revenue_by_channel()