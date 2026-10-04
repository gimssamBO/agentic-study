# -*- coding: utf-8 -*-
# 실행: python code/ch23_coding.py
import sys, pathlib, subprocess, re
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import get_chat, DATA

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = DATA / "buggy_script.py"          # 고칠 대상 (원본, 건드리지 않음)
FIXED = DATA / "fixed_script.py"           # 수정 결과를 저장할 새 파일
# [왜 원본 보존] 코딩 에이전트는 결과를 '새 파일'에 쓴다. 원본을 덮어쓰면
#   잘못 고쳤을 때 되돌릴 수 없으므로, 원본은 비교 기준으로 그대로 둔다.


def read_code(path: pathlib.Path) -> str:
    """대상 소스코드를 읽어 문자열로 반환."""
    return path.read_text(encoding="utf-8")




def ask_fix(source: str) -> str:
    """LLM에게 버그 수정된 전체 코드를 받아 순수 코드 문자열로 반환한다."""
    llm = get_chat(temperature=0)   # [왜 0] 코드 수정은 일관·정확이 생명이라 무작위성 제거
    prompt = (
        "다음 파이썬 스크립트에는 버그가 있다. 버그를 모두 찾아 고친 "
        "**전체 코드**를 하나의 코드블록으로만 출력하라. 설명·주석 외 텍스트는 쓰지 마라.\n"
        "주의: 한글 CSV 인코딩, 문자열/정수 타입 변환, 숫자 비교를 점검하라.\n\n"
        f"```python\n{source}\n```"      # 원본 코드를 코드블록에 담아 전달
    )

    out = llm.invoke(prompt).content
    return extract_code(out)         # 응답에서 코드블록만 추출해 반환


def extract_code(text: str) -> str:
    """LLM 응답에서 ```python ...``` 코드블록만 추출. 없으면 원문 반환.

    [왜 추출] LLM이 코드 앞뒤에 설명을 덧붙이는 경우가 많다. 그대로 실행하면
    SyntaxError 가 나므로, 정규식으로 코드블록 안쪽만 깔끔히 뽑아낸다.
    """
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)  # 첫 코드블록 매칭
    return (m.group(1) if m else text).strip()


#if __name__ == "__main__":
#    source = read_code(TARGET)
#    print("[원본 일부]")
#    print(source[:200], "...\n")

#    fixed = ask_fix(source)
#    print("[LLM 수정본 일부]")
#    print(fixed[:300], "...")


def save_and_run(code: str):
    """수정 코드를 새 파일로 저장한 뒤 별도 프로세스로 실행해 (종료코드, 출력)을 반환한다.

    [왜 실제 실행] '고쳤다'는 LLM 말만 믿지 않고, 진짜 돌려서 종료코드 0(성공)을
    확인한다 — 이것이 코딩 에이전트의 자체 검증(self-verification) 단계다.
    """
    FIXED.write_text(code, encoding="utf-8")       # 새 파일에 저장(원본 보존)
    # 원본이 'data/sales_daily.csv' 상대경로를 쓰므로 ROOT에서 실행
    proc = subprocess.run(
        [sys.executable, str(FIXED)],              # 현재 파이썬으로 수정 파일 실행
        cwd=str(ROOT), capture_output=True, text=True, timeout=60,  # 무한루프 방지 타임아웃
    )
    return proc.returncode, (proc.stdout + proc.stderr)   # 0=정상 종료, 출력은 합본   


if __name__ == "__main__":
    print("[1] 원본 코드 읽기:", TARGET.name)
    source = read_code(TARGET)              # 버그 있는 원본 읽기

    print("[2] LLM에게 버그 수정 요청 중...")
    fixed = ask_fix(source)                 # LLM이 고친 전체 코드 받기

    print("[3] 새 파일로 저장 후 실행 검증:", FIXED.name)
    code, output = save_and_run(fixed)      # 저장→실행→종료코드로 검증

    print("=" * 60)
    print("[실행 결과] 종료코드:", code, "(0=정상)")
    print(output)
    print("=" * 60)
    if code == 0:
        print("성공: 버그가 수정되어 정상 동작합니다 →", FIXED)
    else:
       print("실패: 여전히 오류가 있습니다. 출력을 LLM에 다시 피드백해 재수정하세요.")


