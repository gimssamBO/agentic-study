# 실행: python code/ch04_cot.py
import sys, pathlib, re
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_openai_client, OPENAI_MODEL, DATA
import pandas as pd

client = get_openai_client()
# math_word_problems.csv = 쇼핑 계산 문제 8개. answer 컬럼이 정수 정답.
df = pd.read_csv(DATA / "math_word_problems.csv")
print("문제 수:", len(df))
print(df.iloc[0]["question"], "→ 정답:", df.iloc[0]["answer"])


def extract_number(text: str):
    """답변에서 마지막 숫자를 정수로 반환(콤마 제거)."""
    nums = re.findall(r"-?\d[\d,]*", text.replace(" ", ""))
    return int(nums[-1].replace(",", "")) if nums else None

def ask_direct(question: str) -> str:
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": f"{question}\n설명 없이 최종 숫자(원)만 답하라."}
        ],
        temperature=0,
    )
    return resp.choices[0].message.content

def ask_cot(question: str) -> str:
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    f"{question}\n단계적으로 풀어라. 각 계산을 한 줄씩 쓰고, "
                    "맨 마지막 줄에 '정답: <숫자>' 형식으로 답하라."
                ),
            }
        ],
        temperature=0,
    )
    return resp.choices[0].message.content

direct_ok = cot_ok = 0
for _, row in df.iterrows():
    ans = int(row["answer"])
    d = extract_number(ask_direct(row["question"]))   # 직접 답변의 숫자
    c = extract_number(ask_cot(row["question"]))      # CoT 답변의 숫자
    direct_ok += (d == ans)     # bool(True/False)은 1/0으로 더해진다
    cot_ok += (c == ans)
    print(f"{row['problem_id']} 정답={ans:>7} | 직접={d} {'O' if d==ans else 'X'}"
          f" | CoT={c} {'O' if c==ans else 'X'}")

n = len(df)
print(f"\n직접 답변 정답률 : {direct_ok}/{n} = {direct_ok/n:.0%}")
print(f"CoT  정답률      : {cot_ok}/{n} = {cot_ok/n:.0%}")



# Gemini
# # 실행: python code/ch04_cot.py
# import sys, pathlib, re
# sys.path.append(str(pathlib.Path(__file__).resolve().parent))
# from common import get_genai_client, GEMINI_MODEL, DATA
# from google.genai import types
# import pandas as pd

# client = get_genai_client()
# # math_word_problems.csv = 쇼핑 계산 문제 8개. answer 컬럼이 정수 정답.
# df = pd.read_csv(DATA / "math_word_problems.csv")
# print("문제 수:", len(df))
# print(df.iloc[0]["question"], "→ 정답:", df.iloc[0]["answer"])


# def extract_number(text: str):
#     """답변에서 마지막 숫자를 정수로 반환(콤마 제거)."""
#     nums = re.findall(r"-?\d[\d,]*", text.replace(" ", ""))
#     return int(nums[-1].replace(",", "")) if nums else None

# def ask_direct(question: str) -> str:
#     resp = client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=f"{question}\n설명 없이 최종 숫자(원)만 답하라.",
#         config=types.GenerateContentConfig(temperature=0),
#     )
#     return resp.text

# def ask_cot(question: str) -> str:
#     resp = client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=(f"{question}\n단계적으로 풀어라. 각 계산을 한 줄씩 쓰고, "
#                   "맨 마지막 줄에 '정답: <숫자>' 형식으로 답하라."),
#         config=types.GenerateContentConfig(temperature=0),
#     )
#     return resp.text


# direct_ok = cot_ok = 0
# for _, row in df.iterrows():
#     ans = int(row["answer"])
#     d = extract_number(ask_direct(row["question"]))   # 직접 답변의 숫자
#     c = extract_number(ask_cot(row["question"]))      # CoT 답변의 숫자
#     direct_ok += (d == ans)     # bool(True/False)은 1/0으로 더해진다
#     cot_ok += (c == ans)
#     print(f"{row['problem_id']} 정답={ans:>7} | 직접={d} {'O' if d==ans else 'X'}"
#           f" | CoT={c} {'O' if c==ans else 'X'}")

# n = len(df)
# print(f"\n직접 답변 정답률 : {direct_ok}/{n} = {direct_ok/n:.0%}")
# print(f"CoT  정답률      : {cot_ok}/{n} = {cot_ok/n:.0%}")