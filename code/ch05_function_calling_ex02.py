import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_genai_client, GEMINI_MODEL, DATA
from google.genai import types
import pandas as pd

client = get_genai_client()
inv = pd.read_csv(DATA / "inventory.csv", encoding="utf-8-sig")

def make_get_stock(doc: str):
    """독스트링만 다른 get_stock 함수를 만들어 돌려준다."""
    def get_stock(product_name: str) -> str:
        row = inv[inv["product_name"].str.contains(product_name, na=False)]
        if row.empty:
            return f"'{product_name}' 재고 정보를 찾지 못했습니다."
        r = row.iloc[0]
        return f"{r['product_name']} 재고 {int(r['stock'])}개"
    get_stock.__doc__ = doc      # 독스트링을 바꿔치기
    return get_stock

def test(doc: str, label: str):
    tool = make_get_stock(doc)
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents="이어버드 남았어?",
        config=types.GenerateContentConfig(
            tools=[tool],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0),
    )
    calls = resp.function_calls or []
    picked = calls[0].name if calls else "(도구 미선택)"
    print(f"[{label}] 독스트링={doc!r} → 모델 선택: {picked}")

test("재고.", "부실")
test("상품명(일부만 입력해도 됨)을 받아 현재 재고 수량을 반환한다.", "자세함")