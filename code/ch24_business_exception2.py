import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "code"))
from common import get_chat, DATA
import pandas as pd
from ch24_business import load_facts   # 원본 집계 로직 재사용

# 교안2. 안전판의 철학 — 절대 예외를 던지지 않는다
# [핵심] '계산은 코드'라는 원칙은 그대로 두되, 코드가 죽지 않게 방어막을 씌운다.
required_cols = ["month", "total"]    # 집계에 반드시 있어야 하는 컬럼

# 교안3. 실패 시 공통 반환 — fail()
def load_facts_safe(csv_path: pathlib.Path = None) -> dict:
    """load_facts 를 try/except 로 감싼 안전판. 어떤 상황이든 dict 를 반환한다."""
    path = csv_path or (DATA / "monthly_sales.csv")

    def fail(msg: str) -> dict:
        """실패 시 공통 반환 — 호출부가 facts['ok'] 만 보면 분기할 수 있게 한다."""
        return {
            "ok": False,
            "error": msg,
            "month": "n/a", "prev_month": "n/a",
            "total": 0, "prev_total": 0, "growth_pct": 0.0,
            "top_category": "없음", "top_value": 0,
            "second_category": "없음", "second_value": 0,
            "by_category": {},
        }

    # 교안4. 단계별 검증 — 터지기 전에 친절히 막기
    # 1) 파일 존재 확인 — pandas 가 던지기 전에 먼저 친절히 안내
    if not path.exists():
        return fail(f"매출 파일을 찾지 못했습니다: {path} (경로/파일명을 확인하세요)")

    # 2) 읽기 시도 (깨진 csv·인코딩 오류 대비)
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")   # bom 제거 위해 utf-8-sig
    except Exception as e:
        return fail(f"csv 를 읽을 수 없습니다: {type(e).__name__}\n{e}")

    # 3) 빈 데이터 확인
    if df.empty:
        return fail("매출 데이터가 비어 있습니다(행 0개).")

    # 4) 필수 컬럼 확인
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return fail(f"필수 컬럼이 누락되었습니다: {missing} / 현재 컬럼: {list(df.columns)}")

    # 5) 행 수 확인 (전월 대비는 최소 2개월 필요)
    if len(df) < 2:
        return fail(f"전월 대비 계산에는 최소 2개월이 필요한데 {len(df)}개월뿐입니다.")

    # 교안5. 검증 통과 후 실제 집계
    # 6) 실제 집계 (마지막 그물망 try/except - 원본 load_facts() 함수 사양에 맞춰 인자 없이 호출)
    try:
        facts = load_facts()
    except Exception as e:
        return fail(f"집계 중 알 수 없는 오류: {type(e).__name__}\n{e}")

    facts["ok"] = True             # 성공 표시
    return facts

# 교안6. 4가지 상황 시연
def print_facts(label: str, facts: dict):
    if facts["ok"]:
        print(f"  상태    : 정상 / 대상 월 {facts['month']} / 총매출 {facts['total']:,}원")
    else:
        print(f"  상태    : 실패(기본값 반환) / 안내: {facts['error']}")

# 7. 예시용 보조 함수 스텁 추가 코딩
def notify_admin(msg: str):
    print(f"  [알림 발송] 담당자 슬랙/메일: {msg}")

def write_report(facts: dict) -> str:
    return f"{facts['month']} 매출 보고서 내용..."

def save_report(facts: dict, body: str):
    print(f"  [리포트 저장 완료] {facts['month']} 리포트가 성공적으로 저장되었습니다.")

if __name__ == "__main__":
    print("[1] 정상 파일")
    print_facts("정상", load_facts_safe())

    print("[2] 없는 경로")
    print_facts("없는파일", load_facts_safe(DATA / "없는파일.csv"))

    # [3] total 컬럼 누락한 임시 csv
    bad = DATA / "_tmp_나쁜컬럼.csv"
    pd.read_csv(DATA / "monthly_sales.csv", encoding="utf-8-sig").drop(
        columns=["total"]).to_csv(bad, index=False, encoding="utf-8-sig")
    print("[3] total 컬럼 누락")
    print_facts("컬럼누락", load_facts_safe(bad))
    bad.unlink(missing_ok=True)   # 임시 파일 정리

    # [4] 빈 데이터(헤더만)
    empty = DATA / "_tmp_빈데이터.csv"
    pd.DataFrame(columns=["month", "total"]).to_csv(empty, index=False, encoding="utf-8-sig")
    print("[4] 빈 데이터")
    print_facts("빈데이터", load_facts_safe(empty))
    empty.unlink(missing_ok=True)


# ============================================================== 참고 추가
# 교안7. 호출부에서 활용
    print("\n--- [7. 호출부 실제 활용 시연] ---")
    facts = load_facts_safe()
    if not facts["ok"]:
        # 실패: 로그 남기고, 직전 달 리포트로 폴백하거나 알림 발송
        print(f"[배치 경고] 리포트 생성 실패: {facts['error']}")
        notify_admin(facts["error"])      # 담당자에게 슬랙 알림
    else:
        # 성공: 정상 리포트 생성
        body = write_report(facts)
        save_report(facts, body)