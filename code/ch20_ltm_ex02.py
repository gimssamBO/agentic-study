import json
import pathlib
import shutil
import sys

# 1. pathlib.path -> pathlib.Path 교정
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# common 모듈의 DATA 상수를 불러오고 내부 dict 변수(data)와의 충돌 방지
from common import DATA

store = DATA / "user_profiles_rw.json"
src = DATA / "user_profiles.json"


def _load():
    if not store.exists():
        shutil.copy(src, store)
    with open(store, encoding="utf-8") as f:
        return json.load(f)


def _save(profile_data):
    # ensure_ascii=false -> False 오타 교정 및 파일 리소스 안전 닫기
    with open(store, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)


# 실행 인자로 단계 구분: python script.py 1  /  python script.py 2
phase = sys.argv[1] if len(sys.argv) > 1 else "1"

if phase == "1":
    # 1차 실행: 관심사 저장
    user_data = _load()
    user_data.setdefault("C0001", {})["관심사"] = "캠핑 용품"
    _save(user_data)
    print("[1차 실행] C0001 관심사를 '캠핑 용품'으로 저장하고 종료합니다.")
else:
    # 2차 실행 (재시작 가정): 저장한 값 읽기
    user_data = _load()
    관심사 = user_data.get("C0001", {}).get("관심사", "(없음)")
    print(f"[2차 실행] 재시작 후 읽은 C0001 관심사: {관심사}")
    print("→ 프로그램을 껐다 켰는데도 값이 살아있음 = 장기 기억!")