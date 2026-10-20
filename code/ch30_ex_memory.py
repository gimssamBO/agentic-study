# -*- coding: utf-8 -*-
# code/ch30_ex_memory.py
# 실행: python code/ch30_ex_memory.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

# 앞서 작성한 교환/통합 에이전트 스크립트에서 answer 함수 불러오기
from ch30_ex_exchange import answer


def test_memory_retention() -> bool:
    """① 같은 thread 안에서 이름을 기억하는가 (단기 기억 유지)."""
    answer("내 이름은 오지표야. 기억해줘.", thread_id="a")     # 이름 알려주기
    reply = answer("내 이름이 뭐였지?", thread_id="a")          # 같은 thread → 기억해야 함
    print(f"  [Thread a] 회상 응답: {reply}")
    return "오지표" in reply


def test_thread_isolation() -> bool:
    """② 다른 thread 에서는 그 이름을 모르는가 (스레드 간 메모리 격리)."""
    reply = answer("내 이름이 뭐였지?", thread_id="b")          # 다른 thread → 몰라야 함
    print(f"  [Thread b] 회상 응답: {reply}")
    return "오지표" not in reply        # 이름이 없으면 격리 성공


if __name__ == "__main__":
    print("=" * 60)
    print("메모리 유지 및 스레드 격리 검증")
    print("=" * 60)
    
    retention = test_memory_retention()
    isolation = test_thread_isolation()
    
    print("-" * 60)
    print(f"메모리 유지 테스트: {'PASS ✅' if retention else 'FAIL ❌'}")
    print(f"스레드 격리 테스트: {'PASS ✅' if isolation else 'FAIL ❌'}")
    print("=" * 60)