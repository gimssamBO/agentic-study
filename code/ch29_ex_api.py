# -*- coding: utf-8 -*-
# code/ch29_ex_api.py
# 실행(서버): uvicorn ch29_ex_api:app --reload   (code/ 폴더에서)
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat
from ch29_deploy import load_config, setup_logging, robust_invoke

from fastapi import FastAPI
from pydantic import BaseModel

# 설정·로거·llm은 서버 시작 시 1회만 생성
cfg = load_config()
logger = setup_logging(cfg)
llm = get_chat(provider=cfg["llm"]["provider"], temperature=cfg["llm"]["temperature"])

app = FastAPI(title="승승장구몰 Q&A API")

class AskIn(BaseModel):
    question: str               # 입력 자동 검증(없으면 422)

@app.post("/ask")
def ask(body: AskIn):
    """[POST /ask] 질문을 받아 답변을 반환. 예외 시 {'error':...} 반환."""
    try:
        logger.info(f"질문 수신: {body.question}")
        answer = robust_invoke(llm, body.question, logger,
                               max_retries=cfg["llm"]["max_retries"])
        return {"answer": answer}
    except Exception as e:
        # robust_invoke 자체는 폴백을 주지만, 그 외 예외도 500 대신 json으로
        logger.error(f"엔드포인트 오류: {e}")
        return {"error": "요청 처리 중 오류가 발생했습니다."}