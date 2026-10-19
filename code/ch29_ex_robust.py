# -*- coding: utf-8 -*-
# code/ch29_ex_robust.py
# 실행: python code/ch29_ex_robust.py
import sys, pathlib, time
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat
from ch29_deploy import load_config, setup_logging   # 운영 자산 재사용

_cache = {}   # 질문 → 답변 (간단한 메모리 캐시)


def robust_invoke_cached(llm, message: str, logger, max_retries: int = 3) -> str:
    """캐시 + 재시도 + 폴백 + 소요시간 로깅을 모두 갖춘 호출 래퍼."""
    # 1) 캐시 확인
    if message in _cache:
        logger.info(f"캐시 적중(hit) — llm 호출 생략: {message}")
        return _cache[message]
    logger.info(f"캐시 미스(miss) — llm 호출 시작: {message}")

    # 2) 재시도 + 소요시간 측정
    for attempt in range(1, max_retries + 1):
        t0 = time.time()
        try:
            logger.info(f"llm 호출 시도 {attempt}/{max_retries}")
            resp = llm.invoke(message)
            elapsed = time.time() - t0
            logger.info(f"llm 호출 성공 (소요 {elapsed:.2f}초)")
            _cache[message] = resp.content        # 3) 결과 캐시 저장
            return resp.content
        except Exception as e:
            wait = 2 ** (attempt - 1)
            logger.warning(f"실패({attempt}회): {e} → {wait}초 후 재시도")
            time.sleep(wait)

    logger.error("최종 실패 — 폴백 응답 반환")
    return "죄송합니다. 일시적인 오류로 답변을 생성하지 못했습니다."


if __name__ == "__main__":
    cfg = load_config()
    logger = setup_logging(cfg)
    llm = get_chat(provider=cfg["llm"]["provider"], temperature=cfg["llm"]["temperature"])
    mr = cfg["llm"]["max_retries"]                 # config에서 재시도 횟수

    q = "승승장구몰 무료배송 기준을 한 문장으로 알려줘."
    print("[1차]", robust_invoke_cached(llm, q, logger, mr))   # miss → llm 호출
    print("[2차]", robust_invoke_cached(llm, q, logger, mr))   # hit  → 캐시