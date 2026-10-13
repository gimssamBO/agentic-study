# 교안3. 오류를 받는 ask_fix
import sys, pathlib, subprocess
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "code"))
from common import get_chat, DATA
from ch23_coding import read_code, extract_code   # 기존 도우미 재사용

root = DATA.parent
target = DATA / "buggy_script.py"          # 원본
fixed = DATA / "fixed_script_loop.py"      # 수정 결과 새 파일
max_tries = 3                              # 최대 시도 횟수


def ask_fix(source: str, error: str = "") -> str:
    """버그 수정 전체 코드를 llm에서 받는다. error가 있으면 그 오류를 피드백에 포함."""
    llm = get_chat(temperature=0)
    
    if not error:
        # 최초 수정 시: 타입 변환/천단위 쉼표 처리를 일부러 언급하지 않고 가볍게 지시
        # (LLM이 int('1,500') 변환 버그를 미처 발견하지 못해 1회차에 ValueError 유도)
        prompt = (
            "다음 파이썬 스크립트의 한글 csv 인코딩 및 경로 오류만 고쳐라.\n"
            "수정된 **전체 코드**를 하나의 ```python 코드블록```으로만 출력하라. 설명 텍스트는 쓰지 마라.\n"
            f"```python\n{source}\n```"
        )
    else:
        # 피드백 수신 시: 발생한 오류 메시지를 그대로 전달하여 표적 수정 유도 (2회차 성공)
        feedback = (
            "\n\n[직전 실행 오류 — 이 오류가 사라지도록 반드시 고쳐라]\n"
            f"{error[:1500]}\n"
        )
        prompt = (
            "다음 파이썬 스크립트에는 버그가 있다. 직전 실행 오류를 참고하여 버그를 완벽히 고쳐라.\n"
            "**전체 코드**를 하나의 ```python 코드블록```으로만 출력하라. 설명 텍스트는 쓰지 마라.\n"
            "주의: 한글 csv 인코딩, 천단위 쉼표가 포함된 문자열/정수 타입 변환, 숫자 비교, 파일 경로를 모두 점검하라."
            f"{feedback}\n"
            f"```python\n{source}\n```"
        )
        
    return extract_code(llm.invoke(prompt).content)

# 교안4. 실행 함수
def run_code(code: str):
    """수정 코드를 새 파일로 저장 후 별도 프로세스로 실행해 (종료코드, 출력) 반환."""
    fixed.write_text(code, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(fixed)],
        cwd=str(root), capture_output=True, text=True, timeout=60,
    )
    return proc.returncode, (proc.stdout + proc.stderr)

# 교안5. self-debugging 루프

if __name__ == "__main__":
    print("[0] 원본 코드 읽기:", target.name)
    source = read_code(target)
    error = ""              # 첫 시도엔 피드백 없음
    success = False

    for i in range(1, max_tries + 1):
        print("=" * 60)
        print(f"[시도 {i}/{max_tries}] {'오류 피드백으로 재수정' if error else '최초 수정'}")
        fixed_code = ask_fix(source, error)          # (재)수정 코드 받기
        code, output = run_code(fixed_code)          # 저장→실행→검증
        print(f"  종료코드: {code} (0=정상)")
        if code == 0:
            print("  결과: 정상 동작")
            print(output.strip())
            success = True
            break                                   # 성공 → 루프 탈출
        # 실패 → 오류를 다음 시도의 피드백으로 넘기고, 수정본을 다음 입력으로 사용
        print("  결과: 여전히 오류 →")
        print("  " + output.strip().replace("\n", "\n  "))
        error = output       # [핵심] 이번 오류를 다음 시도에 피드백
        source = fixed_code  # [핵심] 다음 라운드는 '직전 수정본'을 기준으로 더 고친다

    print("=" * 60)
    if success:
        print("성공: self-debugging 루프로 버그를 잡았습니다 →", fixed)
    else:
        print(f"실패: {max_tries}회 시도에도 해결되지 않았습니다(사람 검토 필요).")
