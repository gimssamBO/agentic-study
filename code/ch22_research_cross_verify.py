# 교안2. 판정 결과를 구조화
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "code"))
from common import get_chat
from pydantic import BaseModel, Field
from langchain_community.tools import DuckDuckGoSearchResults

class Verdict(BaseModel):
    """[왜 구조화] 교차검증 결론을 일관된 형식(일치여부·신뢰도·근거)으로 강제."""
    agree: str = Field(description="두 검색 결과의 관계: '일치' | '부분일치' | '불일치'")
    confidence: str = Field(description="주장 신뢰도: '높음' | '보통' | '낮음'")
    reason: str = Field(description="판단 근거 1~2문장(한국어)")

# 교안3. 검색 함수 (폴백 포함)
def search(query: str) -> str:
    """검색어 하나로 웹 검색(실패 시 llm 지식 폴백)."""
    try:
        results = DuckDuckGoSearchResults().invoke(query)
        return str(results)
    except Exception as e:
        print(f"[경고] 검색 실패('{query}') → llm 지식으로 대체: {e}")
        llm = get_chat(temperature=0.3)
        return llm.invoke(f"'{query}'에 대해 아는 핵심 사실을 한국어로 3가지 정리하라.").content

# 교안4. 교차 검증 함수
def cross_check(claim: str, q1: str, q2: str) -> Verdict:
    """동일 주장을 서로 다른 검색어 2개로 검증해 일치/신뢰도를 llm이 판단한다."""
    # [핵심] 같은 사실을 '다른 검색어'로 두 번 본다 → 한 출처에만 의존하지 않는 교차검증.
    r1, r2 = search(q1), search(q2)
    llm = get_chat(temperature=0)                 # [왜 0] 판정은 일관돼야 하니 결정적으로
    structured = llm.with_structured_output(Verdict)
    prompt = (
        f"검증할 주장: \"{claim}\"\n\n"
        f"[검색a: {q1}]\n{r1[:1200]}\n\n"
        f"[검색b: {q2}]\n{r2[:1200]}\n\n"
        "두 검색 결과가 이 주장을 지지하는지 비교하라. 서로 어긋나거나 근거가 약하면 신뢰도를 낮춰라."
    )
    try:
        return structured.invoke(prompt)
    except Exception as e:
        print(f"[경고] 판단 실패 → 보수적 결론: {e}")
        # [왜 보수적] 검증이 실패하면 '믿을 수 없음'으로 처리하는 게 안전하다.
        return Verdict(agree="불일치", confidence="낮음", reason="검증 과정 오류로 신뢰 불가")

# 교안5. 실행
if __name__ == "__main__":
    claim = "최근 무선이어버드 시장은 노이즈 캔슬링(anc) 기능 중심으로 성장하고 있다."
    q1 = "무선이어버드 시장 성장 노이즈 캔슬링"
    q2 = "tws 이어버드 anc 트렌드 2026"

    print("=" * 60)
    print("[검증 대상 주장]", claim)
    print(f"[검색어a] {q1}")
    print(f"[검색어b] {q2}")
    print("=" * 60)
    v = cross_check(claim, q1, q2)
    print("[교차검증 결과]")
    print(f"  일치여부 : {v.agree}")
    print(f"  신뢰도   : {v.confidence}")
    print(f"  근거     : {v.reason}")