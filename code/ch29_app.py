import sys
import pathlib

# 1. 상위 경로 추가 (code/ 공통 모듈 참조)
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "code"))

# 공통 모듈 및 교안 모듈 로드
from common import get_chat
from ch29_deploy import load_config, setup_logging, robust_invoke

# 3. 앱·로거·LLM은 시작 시 한 번만
try:
    from fastapi import FastAPI
    from pydantic import BaseModel

    # [핵심] 설정·로거·LLM은 서버 시작 시 '한 번만' 만든다
    #        (요청마다 재생성하면 느리고 낭비)
    cfg = load_config()
    logger = setup_logging(cfg)
    llm = get_chat(provider=cfg["llm"]["provider"],
                   temperature=cfg["llm"]["temperature"])
    logger.info(f"FastAPI 앱 초기화: {cfg['app']['name']} v{cfg['app']['version']}")

    app = FastAPI(title="승승장구몰 CS Agent")

    #요청/응답 스키마 정의
    class ChatIn(BaseModel):
        thread_id: str = "demo"
        message: str

    class ChatOut(BaseModel):
        thread_id: str
        reply: str

# 4. 엔드포인트 정의
    @app.get("/health")
    def health():
        """[GET /health] 헬스체크"""
        return {"status": "ok", "app": cfg["app"]["name"], "version": cfg["app"]["version"]}

    @app.post("/chat", response_model=ChatOut)
    def chat_endpoint(req: ChatIn):
        """[POST /chat] CS 대화 응답"""
        logger.info(f"[{req.thread_id}] 요청: {req.message}")
        try:
            # robust_invoke 함수에 logger 매개변수를 함께 전달하도록 수정
            res = robust_invoke(llm, req.message, logger)
            
            # res가 객체일 경우 텍스트(.content)만 가져오고, 문자열이면 그대로 사용
            reply_text = res.content if hasattr(res, "content") else res

            return ChatOut(
                thread_id=req.thread_id,
                reply=str(reply_text)
            )
        except Exception as e:
            logger.error(f"[{req.thread_id}] 오류: {e}")
            raise HTTPException(status_code=500, detail="LLM 응답 실패")

except ImportError:
    app = None       # fastapi 미설치여도 import 에러로 죽지 않게
    print("[안내] fastapi/uvicorn 미설치 — 'pip install fastapi uvicorn' 후 사용하세요.")
##################################################
# 5. 터미널 실행 방법
# 
# 터미널(Terminal)에서 ch29_app.py가 있는 위치로 이동 후 아래 명령어를 실행하세요.
#
# uvicorn ch29_app:app --reload
#
# - Swagger API 문서 확인: http://127.0.0.1:8000/docs
# - 헬스체크 확인: http://127.0.0.1:8000/health
# - CS대화응답 확인: http://127.0.0.1:8000/chat
##################################################