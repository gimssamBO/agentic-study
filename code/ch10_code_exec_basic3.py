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
    예: "df.groupby(pd.to_datetime(df['date']).dt.day_name())['sales'].sum().idxmax()"
    식 안에서는 df, pd 만 사용할 수 있다.
    """
    try:
        result = eval(expr, {"__builtins__": {}}, {"df": df, "pd": pd})
    except Exception as e:
        return f"실행 오류: {e}"
    return str(result)

# SYSTEM 프롬프트: 단일 표현식(eval) 규칙 명시
SYSTEM = (
    "너는 승승장구몰의 데이터 분석가다. 일별 매출 DataFrame df에 대해 질문에 답할 pandas 식 '한 줄'만 출력하라.\n"
    "[작성 규칙]\n"
    "1. 식 안에서는 df, pd 만 사용할 수 있다.\n"
    "2. eval()로 실행되므로 변수 할당문(=)이나 세미콜론(;)을 쓸 수 없다. 단일 표현식(Expression)만 출력하라.\n"
    "3. date 컬럼은 날짜 문자열(str)이므로 요일 변환 시 pd.to_datetime(df['date']).dt.day_name() 형태를 사용하라.\n"
    "4. 코드블록, 설명 없이 순수 pandas 식만 출력하라."
)

def make_expr(question: str, error_feedback: str = "") -> str:
    """질문(과 이전 오류 피드백)을 받아 pandas 식 한 줄을 생성한다."""
    prompt = f"{SYSTEM}\n\n질문: {question}"
    if error_feedback:
        prompt += (
            f"\n\n[직전 시도가 실패했다] 오류: {error_feedback}\n"
            "위 오류를 분석하고 고쳐서 올바른 단일 pandas 식 한 줄을 다시 출력하라.\n"
            "실제 존재하는 컬럼은 'date', 'sales' 뿐임을 명심하라."
        )
    raw_output = llm.invoke(prompt).content.strip()
    return raw_output.replace("```python", "").replace("```", "").strip()

def answer_with_retry(question: str, max_retries: int = 3) -> str | None:
    """식 생성 → 실행 → 실패 시 오류를 피드백해 다시 식을 만드는 자가교정 루프."""
    feedback = ""
    for step in range(1, max_retries + 1):
        expr = make_expr(question, feedback)
        print(f"[STEP {step}] 생성된 식: {expr}")
        
        result = run_pandas.invoke({"expr": expr}) if hasattr(run_pandas, "invoke") else run_pandas(expr)

        if not str(result).startswith("실행 오류:"):
            print(f"[STEP {step}] 실행 성공 → 결과: {result}\n")
            return str(result)

        print(f"[STEP {step}] 실행 실패 → {result} (오류 피드백 후 재시도)\n")
        feedback = str(result)

    print("[종료] 최대 재시도 횟수 초과\n")
    return None

# 의도적 오류 유발 질문 테스트
question = "매출(revenue)이 가장 높았던 요일은 무슨 요일이야?"
print(f"=== 질문: {question} ===\n")

# 1단계: Self-correcting 루프로 실행 결과 도출
raw_result = answer_with_retry(question)

# 2단계: 최종 자연어 답변
if raw_result:
    agent = create_agent(
        llm,
        tools=[run_pandas],
        system_prompt="너는 승승장구몰의 데이터 분석가다. 사용자가 질문한 항목에 대해서만 간결하게 한국어로 답변하라."
    )
    prompt = f"질문: {question}\n계산 결과: {raw_result}\n위 결과를 바탕으로 질문에 한 문장으로 답변하라."
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    print("최종 답변:", result["messages"][-1].content)