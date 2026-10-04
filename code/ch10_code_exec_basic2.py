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

# 자연어 위한 에이전트 구성
agent = create_agent(
    llm,
    tools=[run_pandas],
    system_prompt="너는 승승장구몰의 데이터 분석가다. 계산은 반드시 run_pandas 도구로 하고, "
                  "결과 숫자는 천단위 콤마를 붙여 한국어로 설명하라."
                  "사용자가 질문한 항목에 대해서만 답한다. "
                "질문하지 않은 추가 통계, 분석, 설명은 절대 덧붙이지 않는다. "
                "결과 숫자는 천단위 콤마를 붙여 한국어로 간단히 설명한다."
)
# 자연어 질문 던지기
questions = [
    # "전체 기간 총 매출은 얼마야?",
    # "일평균 매출은?",
    # "매출이 가장 높았던 날짜와 그날의 매출을 알려줘.",
    # "2024년 11월 매출 합계는?",
    "매출 상위 3일은?"
]

for q in questions:
    print("Q:", q)
    result = agent.invoke({"messages": [{"role":"user","content":q}]})
    print("A:", result["messages"][-1].content)

# 에이전트 호출 실행
# python ch10_code_exec_basic2.py