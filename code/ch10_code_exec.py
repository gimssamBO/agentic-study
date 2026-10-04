# 실행: python code/ch10_code_exec.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from langchain_core.tools import tool          # @tool: 함수를 도구로 등록
from langchain.agents import create_agent       # create_agent: ReAct 에이전트 생성
from common import get_chat, DATA

# OpenAI 환경으로 설정
llm = get_chat(provider="openai")
# 일자별 매출 데이터 로드 (컬럼: date, sales)
df = pd.read_csv(DATA / "sales_daily.csv")

@tool
def run_pandas(expr: str) -> str:
    """미리 로드된 일별 매출 DataFrame(df)에 대한 pandas 식을 실행해 결과를 문자열로 반환한다.
    df 컬럼: date(날짜 문자열 'YYYY-MM-DD'), sales(정수 매출).
    예: "df['sales'].sum()", "df['sales'].mean()",
        "df.loc[df['sales'].idxmax(), 'date']".
    식 안에서는 df, pd 만 사용할 수 있다."""
    # 빌트인 차단 + df/pd 화이트리스트
    try:
        result = eval(expr, {"__builtins__": {}}, {"df": df, "pd": pd})
    except Exception as e:
        return f"실행 오류: {e}"     # 잘못된 식이어도 에이전트가 죽지 않게
    return str(result)

agent = create_agent(
    llm,
    tools=[run_pandas],
    system_prompt="너는 승승장구몰의 데이터 분석가다. 계산은 반드시 run_pandas 도구로 하고, "
                  "결과 숫자는 천단위 콤마를 붙여 한국어로 설명하라.",
)

questions = [
    "전체 기간 총 매출은 얼마야?",
    "일평균 매출은?",
    "매출이 가장 높았던 날짜와 그날의 매출을 알려줘.",
]

for q in questions:
    print("Q:", q)
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})
    print("A:", result["messages"][-1].content)
    print()

SYSTEM = (
    "너는 승승장구몰의 데이터 분석가다. 일별 매출 DataFrame df(컬럼: date, sales)에 대해 "
    "질문에 답할 pandas 식 '한 줄'만 출력하라. 식 안에서는 df, pd 만 쓸 수 있다. "
    "코드블록·설명 없이 식만 출력하라."
)

def make_expr(question: str, error_feedback: str = "") -> str:
    """질문(과 이전 오류 피드백)을 받아 pandas 식 한 줄을 생성한다."""
    prompt = f"{SYSTEM}\n\n질문: {question}"
    if error_feedback:
        # 직전 실패의 오류 메시지를 그대로 보여주고 고치게 한다 (self-correcting)
        prompt += (
            f"\n\n[직전 시도가 실패했다] 오류: {error_feedback}\n"
            "위 오류를 고쳐 올바른 pandas 식 한 줄을 다시 출력하라. "
            "존재하는 컬럼은 date, sales 뿐임을 명심하라."
        )
    # LangChain invoke 결과의 text 추출 및 마크다운 백틱(`) 방어 처리
    content = llm.invoke(prompt).content.strip()
    return content.replace("```python", "").replace("```", "").strip()

def answer_with_retry(question: str, max_retries: int = 3):
    """식 생성 → 실행 → 실패 시 오류를 피드백해 다시 식을 만드는 자가교정 루프."""
    feedback = ""
    for step in range(1, max_retries + 1):
        expr = make_expr(question, feedback)
        print(f"[STEP {step}] 생성된 식: {expr}")
        # @tool 데코레이터 객체를 직접 함수로 호출하거나 invoke 사용
        result = run_pandas.invoke({"expr": expr}) if hasattr(run_pandas, "invoke") else run_pandas(expr)

        if not str(result).startswith("실행 오류:"):
            print(f"[STEP {step}] 실행 성공 → 결과: {result}")
            return result                 # 성공!

        # 실패 → 오류 메시지를 다음 시도의 피드백으로 넘긴다
        print(f"[STEP {step}] 실행 실패 → {result} (오류를 피드백해 재시도)")
        feedback = str(result)

    print("[종료] 최대 재시도 초과")
    return None

answer_with_retry("매출(revenue)이 가장 높았던 요일은 무슨 요일이야?")