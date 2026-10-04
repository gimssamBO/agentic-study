import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool
from common import get_chat, DATA

# OpenAI 환경으로 표준화
llm = get_chat(provider="openai")
df = pd.read_csv(DATA / "sales_daily.csv")

@tool
def run_pandas(expr: str) -> str:
    """일별 매출 df에 pandas 식을 실행한다. df, pd 만 사용."""
    # LLM이 전달할 수 있는 마크다운 코드블록 백틱(```) 전처리 방어
    clean_expr = expr.replace("```python", "").replace("```", "").strip()
    try:
        return str(eval(clean_expr, {"__builtins__": {}}, {"df": df, "pd": pd}))
    except Exception as e:
        return f"실행 오류: {e}"

if __name__ == "__main__":
    print("위험한 식 (파일 목록 조회 시도):")
    print(" ", run_pandas.invoke({"expr": "__import__('os').listdir('.')"}))

    print("\n정상 식 (매출 합계):")
    print(" ", run_pandas.invoke({"expr": "df['sales'].sum()"}))