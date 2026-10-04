import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from common import get_chat, DATA

llm = get_chat(provider="openai")
df = pd.read_csv(DATA / "sales_daily.csv")

@tool
def run_pandas(expr: str) -> str:
    """일별 매출 df(컬럼: date 'YYYY-MM-DD', sales)에 pandas 식을 실행한다. df, pd 만 사용."""
    # OpenAI 모델 특성상 전달될 수 있는 마크다운 백틱(```) 전처리 방어
    clean_expr = expr.replace("```python", "").replace("```", "").strip()
    try:
        return str(eval(clean_expr, {"__builtins__": {}}, {"df": df, "pd": pd}))
    except Exception as e:
        return f"실행 오류: {e}"

agent = create_agent(llm, tools=[run_pandas],
    system_prompt="너는 데이터 분석가다. 계산은 반드시 run_pandas로 하고 천단위 콤마로 한국어 설명하라.")

q = "2024년 11월 매출 합계는?"
for step in agent.stream({"messages": [{"role": "user", "content": q}]}, stream_mode="values"):
    step["messages"][-1].pretty_print()