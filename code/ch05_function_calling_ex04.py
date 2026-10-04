import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_genai_client, GEMINI_MODEL, DATA
from google.genai import types
import pandas as pd

client = get_genai_client()
rates = pd.read_csv(DATA / "exchange_rates.csv", encoding="utf-8-sig")

def get_exchange_rate(currency: str) -> str:
    """통화 코드(USD, EUR, JPY 등)를 받아 1단위당 원화(KRW) 환율을 반환한다."""
    row = rates[rates["currency"].str.upper() == currency.upper()]
    if row.empty:
        return f"{currency} 환율 정보가 없습니다."
    return f"1 {currency.upper()} = {float(row.iloc[0]['krw_per_unit']):,.2f} KRW"

# (1) 모델에게 자동 처리 시키기
resp = client.models.generate_content(
    model=GEMINI_MODEL,
    contents="10000엔이면 원화로 얼마야?",
    config=types.GenerateContentConfig(tools=[get_exchange_rate], temperature=0),
)
print("[모델 답]", resp.text)

# (2) 직접 계산해 검증
jpy = float(rates[rates["currency"].str.upper() == "JPY"].iloc[0]["krw_per_unit"])
print(f"[직접 계산] 10000 × {jpy} = {10000 * jpy:,.0f} 원")