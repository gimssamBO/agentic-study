import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL, DATA
import pandas as pd
import json

client = get_openai_client()
rates = pd.read_csv(DATA / "exchange_rates.csv", encoding="utf-8-sig")

def get_exchange_rate(currency: str) -> str:
    """통화 코드(USD, EUR, JPY 등)를 받아 1단위당 원화(KRW) 환율을 반환한다."""
    row = rates[rates["currency"].str.upper() == currency.upper()]
    if row.empty:
        return f"{currency} 환율 정보가 없습니다."
    return f"1 {currency.upper()} = {float(row.iloc[0]['krw_per_unit']):,.2f} KRW"

TOOLS = {"get_exchange_rate": get_exchange_rate}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "통화 코드(USD, EUR, JPY 등)를 받아 1단위당 원화(KRW) 환율을 반환한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "description": "통화 코드 (예: USD, EUR, JPY)",
                    },
                },
                "required": ["currency"],
            },
        },
    }
]

# (1) 도구 호출 확인 및 실행 후 최종 답변 생성
messages = [{"role": "user", "content": "10000엔이면 원화로 얼마야?"}]

resp = client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=messages,
    tools=tools_schema,
    temperature=0,
)

msg = resp.choices[0].message

if msg.tool_calls:
    messages.append(msg)
    for tc in msg.tool_calls:
        func = TOOLS.get(tc.function.name)
        args = json.loads(tc.function.arguments)
        result = func(**args) if func else f"도구 {tc.function.name} 없음"
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "name": tc.function.name,
            "content": json.dumps({"result": result}),
        })

    followup = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0,
    )
    print("[모델 답]", followup.choices[0].message.content)
else:
    print("[모델 답]", msg.content)

# (2) 직접 계산해 검증
jpy = float(rates[rates["currency"].str.upper() == "JPY"].iloc[0]["krw_per_unit"])
print(f"[직접 계산] 10000 × {jpy} = {10000 * jpy:,.0f} 원")