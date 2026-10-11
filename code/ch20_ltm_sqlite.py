import json
import pathlib
import sqlite3
import sys

# 1. 경로 설정 및 대문자 DATA 상수 불러오기
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA
from langchain_core.tools import tool

# 데이터베이스 경로 설정
db = DATA / "profiles.db"


def init_db():
    """profiles 테이블을 만들고, 비어 있으면 json 원본을 한 번 이관한다."""
    with sqlite3.connect(db) as conn:
        # customer_id를 기본키(pk)로 → 고객당 한 행만 존재
        conn.execute(
            "create table if not exists profiles ("
            " customer_id text primary key, name text, membership text,"
            " 선호카테고리 text, 관심사 text, 비고 text)"
        )
        # 비어 있으면 json → sqlite 이관 (최초 1회)
        if conn.execute("select count(*) from profiles").fetchone()[0] == 0:
            # 변수명 충돌 방지: data -> raw_data 사용
            json_file = DATA / "user_profiles.json"
            if json_file.exists():
                with open(json_file, encoding="utf-8") as f:
                    raw_data = json.load(f)
                for cid, p in raw_data.items():
                    conn.execute(
                        "insert into profiles values (?,?,?,?,?,?)",
                        (
                            cid,
                            p.get("name", ""),
                            p.get("membership", ""),
                            json.dumps(p.get("선호카테고리", []), ensure_ascii=False), # false -> False 교정
                            p.get("관심사", ""),
                            p.get("비고", ""),
                        ),
                    )

@tool
def get_profile(customer_id: str) -> str:
    """고객id로 sqlite에 저장된 프로필을 조회한다."""
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row  # sqlite3.row -> sqlite3.Row 교정
        row = conn.execute(
            "select * from profiles where customer_id=?", (customer_id,)
        ).fetchone()
    if not row:
        return f"{customer_id} 프로필이 없습니다."
    p = dict(row)
    p["선호카테고리"] = json.loads(p["선호카테고리"] or "[]")  # 다시 리스트로
    return json.dumps(p, ensure_ascii=False) # false -> False 교정

@tool
def update_profile(customer_id: str, field: str, value: str) -> str:
    """고객 프로필의 지정된 필드 값을 갱신한다."""
    # [경고] 컬럼명(field)을 외부 입력 그대로 sql에 끼우면 인젝션 위험!
    allowed = {"name", "membership", "선호카테고리", "관심사", "비고"}
    if field not in allowed:  # 허용 컬럼만 화이트리스트
        return f"'{field}'은(는) 갱신할 수 없는 필드입니다."
    with sqlite3.connect(db) as conn:
        conn.execute(
            f"update profiles set {field}=? where customer_id=?",
            (value, customer_id),
        )  # value는 ? 파라미터로 (안전)
    return "저장했습니다."

# 테스트용 실행 코드
if __name__ == "__main__":
    # 1. DB 및 테이블 생성 & JSON 데이터 이관 실행
    print("=== 1. DB 초기화 ===")
    init_db()
    print("DB 초기화 완료!")

    # 2. 프로필 조회 테스트 (JSON 파일에 있던 customer_id 예: c0001)
    print("\n=== 2. 프로필 조회 테스트 ===")
    res_get = get_profile.invoke({"customer_id": "C0001"})
    print("조회 결과:", res_get)

    # 3. 프로필 수정 테스트
    print("\n=== 3. 프로필 수정 테스트 ===")
    res_update = update_profile.invoke({"customer_id": "C0001", "field": "membership", "value": "VIP"})
    print("수정 결과:", res_update)

    # 4. 수정 후 재조회 확인
    print("\n=== 4. 수정 후 다시 조회 ===")
    res_re_get = get_profile.invoke({"customer_id": "CS0001"})
    print("재조회 결과:", res_re_get)