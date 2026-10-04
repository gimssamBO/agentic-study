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
    """미리 로드된 일별 매출 DataFrame(df)에 대한 pandas 식을 실행해 결과를 문자열로 반환한다.
    df 컬럼: date(날짜 문자열 'YYYY-MM-DD'), sales(정수 매출).
    예: "df['sales'].sum()", "df['sales'].mean()",
        "df.loc[df['sales'].idxmax(), 'date']".
    식 안에서는 df, pd 만 사용할 수 있다.
    """
    try:
        result = eval(expr, {"__builtins__":{}}, {"df":df, "pd":pd})
    except Exception as e:
        return f"실행 오류: {e}"
    return str(result)

print(run_pandas.invoke({"expr":"df['sales']"}))
print(run_pandas.invoke({"expr":"df['sales'].sum()"}))
print(run_pandas.invoke({"expr":"df['sales'].mean()"}))

print(run_pandas.invoke({"expr":"df.loc[df['sales'].idxmax(),'date']"}))

print(run_pandas.invoke({"expr":"df['date']"}))

# 독스트링 정의해서 실행 오류 남
print(run_pandas.invoke({"expr":"df['revoke']"}))
# len() 빌트인 함수라 실행오류 남
print(run_pandas.invoke({"expr":"len(df)"}))
# 행 갯수 리턴 = pandas 메서드 사용해야 함
print(run_pandas.invoke({"expr":"df.shape[0]"}))