# 교안2. 설계 입력 명세
# -*- coding: utf-8 -*-
from dataclasses import dataclass

@dataclass
class DesignSpec:
    """설계 판단에 필요한 입력 신호."""
    name: str = "이름없는 에이전트"
    num_tools: int = 0               # 붙일 도구 개수
    has_internal_docs: bool = False  # 사내문서(정책·매뉴얼 pdf 등) 유무
    needs_realtime: bool = False     # 실시간 데이터(주문·재고) 필요 여부
    multi_turn: bool = False         # 멀티턴(대화 맥락 유지) 필요 여부
    num_roles: int = 1               # 분리할 역할 수(리서처/분석가/작성자 등)
    long_running: bool = False       # 장기 누적 기억(사용자별 프로필) 필요 여부

# 교안3. 판단 로직 — 점수와 근거
def decide(spec: DesignSpec) -> dict:
    """입력 신호를 규칙·점수로 평가해 구성요소 도입 여부와 근거를 반환한다."""
    result = {}

    # --- RAG: 사내문서가 있으면 강하게 권장 ---
    rag_score, rag_reasons = 0, []
    if spec.has_internal_docs:
        rag_score += 2
        rag_reasons.append("사내문서 보유 → 근거 있는 답변 위해 rag 필요")
    if spec.needs_realtime:
        rag_reasons.append("단, 실시간 데이터는 rag가 아니라 도구로 조회")
    result["RAG"] = {
        "도입": rag_score >= 2,
        "점수": rag_score,
        "근거": " / ".join(rag_reasons) or "검색할 고정 문서가 없어 불필요"
    }

    # --- 장기메모리: 멀티턴 + 장기누적이면 권장 ---
    mem_score, mem_reasons = 0, []
    if spec.multi_turn:
        mem_score += 1
        mem_reasons.append("멀티턴 → 최소 단기메모리(thread_id) 필요")
    if spec.long_running:
        mem_score += 2
        mem_reasons.append("사용자별 장기 누적 → 장기메모리(프로필 저장) 권장")
    result["장기메모리"] = {
        "도입": mem_score >= 2,
        "점수": mem_score,
        "근거": " / ".join(mem_reasons) or "단발성 대화라 메모리 불필요"
    }

    # --- 멀티에이전트: 역할 수·도구 수가 많으면 권장 ---
    ma_score, ma_reasons = 0, []
    if spec.num_roles >= 3:
        ma_score += 2
        ma_reasons.append(f"역할 {spec.num_roles}개 → 역할별 에이전트 분리 권장")
    if spec.num_tools >= 8:
        ma_score += 1
        ma_reasons.append(f"도구 {spec.num_tools}개 → 단일 에이전트엔 과부하")
    result["멀티에이전트"] = {
        "도입": ma_score >= 2,
        "점수": ma_score,
        "근거": " / ".join(ma_reasons) or "역할·도구가 적어 단일로 시작"
    }

    # --- 워크플로우(StateGraph): 역할이 정해진 순서로 흐르면 권장 ---
    wf_score, wf_reasons = 0, []
    if spec.num_roles >= 2:
        wf_score += 2
        wf_reasons.append(f"역할 {spec.num_roles}개의 정해진 처리 순서 → 워크플로우로 명시")
    result["워크플로우"] = {
        "도입": wf_score >= 2,
        "점수": wf_score,
        "근거": " / ".join(wf_reasons) or "단일 역할이라 선형 호출로 충분"
    }
    return result    

# 교안4. 출력과 실행
def print_decision(spec: DesignSpec) -> None:
    print("=" * 60)
    print(f"[시나리오] {spec.name}")
    print(f"  도구={spec.num_tools}개, 사내문서={spec.has_internal_docs}, "
          f"실시간={spec.needs_realtime}, 멀티턴={spec.multi_turn}, "
          f"역할={spec.num_roles}개, 장기={spec.long_running}")
    print("-" * 60)
    for i, (comp, d) in enumerate(decide(spec).items(), 1):
        mark = "도입 ✅" if d["도입"] else "보류 ⬜"
        print(f"[{i}] {comp:<7} {mark} (점수 {d['점수']}) — {d['근거']}")

if __name__ == "__main__":
    scenarios = [
        DesignSpec(name="승승장구몰 통합 CS 에이전트",
                   num_tools=4, has_internal_docs=True, needs_realtime=True,
                   multi_turn=True, num_roles=1, long_running=False),
        DesignSpec(name="승승장구몰 시장조사 팀",
                   num_tools=2, has_internal_docs=False, needs_realtime=False,
                   multi_turn=False, num_roles=3, long_running=False),
        DesignSpec(name="승승장구몰 간단 FAQ 봇",
                   num_tools=1, has_internal_docs=False, needs_realtime=False,
                   multi_turn=False, num_roles=1, long_running=False),
        DesignSpec(name="승승장구몰 VIP 개인비서",
                   num_tools=10, has_internal_docs=True, needs_realtime=True,
                   multi_turn=True, num_roles=2, long_running=True),
    ]
    for sp in scenarios:
        print_decision(sp)
        print()