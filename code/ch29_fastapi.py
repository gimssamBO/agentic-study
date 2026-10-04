import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "code"))
from common import get_chat

# 29강 운영 자산을 그대로 재사용 (설정 분리·구조적 로깅·재시도 래퍼)
from ch29_deploy import load_config, setup_logging, robust_invoke
from  ch30_final import answer


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



    class ChatIn(BaseModel):                  # 요청 본문 스키마 = 입력 자동 검증
        thread_id: str = "demo"
        message: str

    class ChatOut(BaseModel):                 # 응답 스키마(문서화·검증용)
        thread_id: str
        reply: str

    # @app.post("/chat", response_model=ChatOut)
    # def chat(body: ChatIn):
    #     """[POST /chat] 사용자 메시지를 받아 견고한 래퍼로 답변을 생성한다."""
    #     logger.info(f"요청 수신(thread={body.thread_id}): {body.message}")
    #     reply = robust_invoke(llm, body.message, logger,
    #                           max_retries=cfg["llm"]["max_retries"])  # 재시도+폴백
    #     return {"thread_id": body.thread_id, "reply": reply}


    # 29강 /chat 엔드포인트에서 robust_invoke 대신 answer 를 호출
    @app.post("/chat")
    def chat(body: ChatIn):
        """[POST /chat] 사용자 메시지를 받아 견고한 래퍼로 답변을 생성한다."""
        logger.info(f"요청 수신(thread={body.thread_id}): {body.message}")
        reply = answer(body.message, body.thread_id)   # 완성된 에이전트!
        return {"thread_id": body.thread_id, "reply": reply}
    

    @app.get("/health")
    def health():
        """[GET /health] 헬스체크 — 로드밸런서/모니터가 살아있는지 확인."""
        return {"status": "ok", "app": cfg["app"]["name"], "version": cfg["app"]["version"]}

except ImportError:
    app = None       # fastapi 미설치여도 import 에러로 죽지 않게
    print("[안내] fastapi/uvicorn 미설치 — 'pip install fastapi uvicorn' 후 사용하세요.")



##################################################
# 5. 서버 실행과 호출


# code/ 폴더에 ch29_app.py 로 배치했다고 가정
#  terminal 에서 실행
#  uvicorn ch29_fastapi:app --reload