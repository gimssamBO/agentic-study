import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "code"))
from common import get_chat
# 교안2. 운영 자산 재사용 (설정 분리·구조적 로깅·재시도 래퍼)
from ch29_deploy import load_config, setup_logging, robust_invoke

# 교안3. 앱·로거·LLM은 시작 시 한 번만
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

# 요청4. 요청/응답 스키마와 엔드포인트
    class ChatIn(BaseModel):                  # 요청 본문 스키마 = 입력 자동 검증
        thread_id: str = "demo"
        message: str

    class ChatOut(BaseModel):                 # 응답 스키마(문서화·검증용)
        thread_id: str
        reply: str

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
#  uvicorn ch29_app:app --reload