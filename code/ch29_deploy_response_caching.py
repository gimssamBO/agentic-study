# 2. 캐시 key — 질문 정규화
import hashlib
import json
import sys
import pathlib

# 상위 경로 추가 (code/ 공통 모듈 참조용)
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "code"))

from common import ROOT, get_chat
from ch29_deploy import load_config, setup_logging, robust_invoke

cache_file = ROOT / "cache" / "response_cache.json"

def _key(question: str) -> str:
    """질문을 정규화 후 해시해 캐시 key로 쓴다(공백·대소문자 차이 흡수)."""
    norm = " ".join(question.strip().lower().split())   # 앞뒤 공백·중복 공백·대소문자 정규화
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]

# 3. 캐시 클래스 — 메모리 + 파일 영속
class ResponseCache:
    """질문→답변 캐시. 메모리 dict + json 파일 영속."""

    def __init__(self, persist: bool = True):
        self.persist = persist
        self.store = {}            # key → answer
        self.hits = 0              # 캐시 히트 횟수(= 절감된 호출 수)
        self.misses = 0            # 캐시 미스 횟수(= 실제 llm 호출)
        if persist and cache_file.exists():
            self.store = json.loads(cache_file.read_text(encoding="utf-8"))  # 기존 캐시 로드

    def get(self, question: str):
        return self.store.get(_key(question))

    def set(self, question: str, answer: str):
        self.store[_key(question)] = answer
        if self.persist:                                       # 파일에도 즉시 반영
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(
                json.dumps(self.store, ensure_ascii=False, indent=2), encoding="utf-8"
            )

# 5. 절감 효과 리포트 = (주의)코딩위치 => class ResponseCache안에 선언
    def report(self, cost_per_call: float = 0.002):
        total = self.hits + self.misses
        saved = self.hits * cost_per_call
        print("=" * 60)
        print(f"[캐시 리포트] 총 요청 {total}건 / 히트 {self.hits} / 미스 {self.misses}")
        print(f"  절감된 llm 호출: {self.hits}회  →  예상 절감 비용: ${saved:.4f}")

# 4. 캐시 우선 호출
def cached_invoke(cache: ResponseCache, llm, question: str, logger) -> str:
    """캐시를 먼저 보고, 없을 때만 robust_invoke로 llm을 부른다."""
    hit = cache.get(question)
    if hit is not None:
        cache.hits += 1
        logger.info(f"캐시 hit — llm 호출 건너뜀: {question}")
        print(f"  [hit ] {question[:30]}...")
        return hit

    cache.misses += 1
    logger.info(f"캐시 miss — llm 호출: {question}")
    print(f"  [miss] {question[:30]}...  → llm 호출")
    
    # LLM 호출
    res = robust_invoke(llm, question, logger)
    answer = res.content if hasattr(res, "content") else str(res)
    
    cache.set(question, answer)  # 결과를 캐시에 저장
    return answer

# 6. 실행과 결과
if __name__ == "__main__":
    cfg = load_config()
    logger = setup_logging(cfg)
    llm = get_chat(provider=cfg["llm"]["provider"], temperature=cfg["llm"]["temperature"])
    cache = ResponseCache(persist=True)

    questions = [
        "승승장구몰 무료배송 기준을 한 문장으로 알려줘.",
        "승승장구몰 무료배송 기준을 한 문장으로 알려줘.",     # 동일 → hit
        "환불은 며칠 안에 가능해?",
        "승승장구몰 무료배송 기준을   한문장으로 알려줘.",       # 공백만 다름 → 정규화로 hit
        "환불은 며칠 안에 가능해?",                          # 동일 → hit
    ]

    for i, q in enumerate(questions, 1):
        ans = cached_invoke(cache, llm, q, logger)
        print(f"[{i}] 답변: {ans[:60]}\n")

    cache.report()