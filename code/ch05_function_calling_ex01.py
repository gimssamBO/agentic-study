import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL, DATA
from openai import pydantic_function_tool
from pydantic import BaseModel, Field
import pandas as pd

client = get_openai_client()
inv = pd.read_csv(DATA / "inventory.csv", encoding="utf-8-sig")

# 1. Pydantic 모델로 파라미터 규격 정의
class StockQuery(BaseModel):
    product_name: str = Field(description="조회할 상품명")

def test(doc: str, label: str):
    # 2. 함수 대신 BaseModel에 description(독스트링 역할)을 직접 부여하거나
    #    pydantic_function_tool(model, description=...) 규격으로 전달
    tool = pydantic_function_tool(
        model=StockQuery,
        name="get_stock",
        description=doc
    )
    
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": "이어버드 남았어?"}],
        tools=[tool],
        temperature=0,
    )
    calls = resp.choices[0].message.tool_calls or []
    picked = calls[0].function.name if calls else "(도구 미선택)"
    print(f"[{label}] 독스트링={doc!r} → 모델 선택: {picked}")

test("재고.", "부실")
test("상품명(일부만 입력해도 됨)을 받아 현재 재고 수량을 반환한다.", "자세함")