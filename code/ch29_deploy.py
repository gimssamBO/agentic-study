############################################
# 1. 시작부 & 설정 로더
# -*- coding: utf-8 -*-
# 실행: python code/ch29_deploy.py
import sys, pathlib, time, logging
sys.path.append(str(pathlib.Path(__file__).resolve().parent))  # code/ 를 import 경로에
from common import DATA, ROOT, get_chat

import yaml

# [이 강의 핵심] '내 PC에선 됐는데요' 방지. 설정 분리 / 구조적 로깅 / 재시도+폴백으로
#   어디서 돌려도 똑같이 동작하고, 일시 오류에도 죽지 않는 견고한 서비스로 만든다.


def load_config() -> dict:
    """data/config.yaml 을 읽어 dict로 반환한다(하드코딩 금지)."""
    with open(DATA / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
    

##############################################
#2. 로깅 설정
def setup_logging(cfg: dict) -> logging.Logger:
    """config의 logging 설정으로 로거를 구성한다(콘솔+파일 동시 출력)."""
    level = getattr(logging, cfg["logging"]["level"].upper(), logging.INFO)
    log_path = ROOT / cfg["logging"]["file"]
    log_path.parent.mkdir(parents=True, exist_ok=True)   # logs/ 자동 생성

    logger = logging.getLogger("cs_agent")
    logger.setLevel(level)
    logger.handlers.clear()                              # 재호출 시 핸들러 중복 방지
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    sh = logging.StreamHandler();  sh.setFormatter(fmt)              # 콘솔
    fh = logging.FileHandler(log_path, encoding="utf-8"); fh.setFormatter(fmt)  # 파일
    logger.addHandler(sh); logger.addHandler(fh)
    return logger


# 3. 견고한 LLM 호출 래퍼
def robust_invoke(llm, message: str, logger, max_retries: int = 3) -> str:
    """LLM 호출을 재시도+폴백으로 감싼다. 끝내 실패해도 서비스는 죽지 않는다."""
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"LLM 호출 시도 {attempt}/{max_retries}")
            resp = llm.invoke(message)
            logger.info("LLM 호출 성공")
            return resp.content                          # 성공하면 즉시 반환
        except Exception as e:
            wait = 2 ** (attempt - 1)                    # 지수 백오프: 1, 2, 4초
            logger.warning(f"LLM 호출 실패({attempt}회): {e} → {wait}초 후 재시도")
            time.sleep(wait)
    logger.error("LLM 호출 최종 실패 — 폴백 응답 반환")
    return "죄송합니다. 일시적인 오류로 답변을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요."


# 4. 조립 & 실행
def main():
    cfg = load_config()                  # 1) 설정 로드
    logger = setup_logging(cfg)          # 2) 로깅 구성
    logger.info(f"앱 시작: {cfg['app']['name']} v{cfg['app']['version']}")

    # config의 값으로 LLM 생성(코드에 모델명·온도를 박지 않음 = 하드코딩 아님)
    llm = get_chat(provider=cfg["llm"]["provider"],
                   temperature=cfg["llm"]["temperature"])

    answer = robust_invoke(
        llm, "승승장구몰 무료배송 기준을 한 문장으로 알려줘.",
        logger, max_retries=cfg["llm"]["max_retries"],
    )
    print("\n[답변]", answer)
    logger.info("앱 종료")


if __name__ == "__main__":
    main()
