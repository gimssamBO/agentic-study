# -*- coding: utf-8 -*-
# 실행: python code/ch23_ex_summary.py
import sys, pathlib, re
# 1. common 및 ch23_coding 모듈 참조 설정 (Path 대문자 정정)
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, DATA
from ch23_coding import read_code, extract_code, save_and_run, TARGET, FIXED

def ask_fix_with_summary(source: str) -> tuple[str, str]:
    """수정 코드와 변경 요약을 함께 받아 (코드, 요약)으로 분리해 반환한다."""
    llm = get_chat(temperature=0)
    prompt = (
        "다음 파이썬 스크립트의 버그를 모두 고쳐라. 출력 형식은 정확히 다음과 같이 하라:\n"
        "먼저 '### 변경 요약'으로 시작해 고친 버그를 번호로 나열(무엇을 왜 고쳤는지),\n"
        "그 다음 수정한 **전체 코드**를 하나의 ```python 코드블록```으로 출력하라.\n\n"
        f"```python\n{source}\n```"
    )
    out = llm.invoke(prompt).content
    code = extract_code(out)                          # 코드블록만 추출 → 저장용
    # 요약 = 코드블록을 제거한 나머지 텍스트
    summary = re.sub(r"```(?:python)?\s*.*?```", "", out, flags=re.DOTALL).strip()
    return code, summary

if __name__ == "__main__":
    source = read_code(TARGET)                        # 대문자 경로 상수로 읽기
    code, summary = ask_fix_with_summary(source)
    print("[변경 요약]")                              # 요약은 콘솔에만
    print(summary)
    print("=" * 60)
    rc, output = save_and_run(code)                   # 코드만 저장·실행
    print("[실행] 종료코드:", rc, "(0=정상)")
    print(output)