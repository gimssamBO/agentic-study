# -*- coding: utf-8 -*-
"""
common.py — 모든 실습 공통 파일

목적:
  - .env 의 API 키를 한 곳에서 로드한다.
  - OpenAI(주력) / Gemini(보조) 모델 객체를 일관되게 생성한다.
  - 실습 데이터(data/) 경로를 쉽게 찾는다.

각 강의 실습 코드 맨 위에서 다음처럼 불러 씁니다.
    from common import get_chat, get_openai_client, DATA, OPENAI_MODEL
"""
import os
import pathlib
from dotenv import load_dotenv

if "SSL_CERT_FILE" in os.environ and not os.path.exists(os.environ["SSL_CERT_FILE"]):
    del os.environ["SSL_CERT_FILE"]

# override=True 옵션을 주어 기존 환경변수를 .env 값으로 강제 덮어씁니다.
load_dotenv(override=True)

# 프로젝트 루트
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = DATA / "docs"

# .env 로드 (루트의 .env 를 읽음)
load_dotenv(ROOT / ".env")

# OpenAI 기본 모델 설정
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# Gemini 모델 설정 (보조)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")


def require_key(name: str) -> str:
    """환경변수 키가 없으면 종료."""
    val = os.getenv(name)
    if not val or val.startswith("여기에"):
        raise SystemExit(
            f"[설정 필요] {name} 가 .env 에 없습니다.\n"
            f" 1) .env 파일을 열어 {name} 값을 입력하세요."
        )
    return val


# ---------- raw SDK (원리 학습용) ----------
def get_openai_client():
    """openai 공식 SDK 클라이언트 (from openai import OpenAI)."""
    from openai import OpenAI
    return OpenAI(api_key=require_key("OPENAI_API_KEY"))


def get_genai_client():
    """google-genai 클라이언트 (from google import genai)."""
    from google import genai
    return genai.Client(api_key=require_key("GOOGLE_API_KEY"))

# ---------- LangChain Chat 모델 (현업용) ----------
def get_chat(provider: str = "openai", temperature: float = 0.0):  
    """LangChain ChatModel 반환. provider: 'openai'(기본) | 'gemini'."""
    if provider == "openai":
        require_key("OPENAI_API_KEY")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=OPENAI_MODEL, temperature=temperature)
    elif provider == "gemini":
        require_key("GOOGLE_API_KEY")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=temperature)
    raise ValueError(f"알 수 없는 provider: {provider}")


# ---------- LangChain Embeddings ----------
def get_embeddings(provider: str = "openai"):  
    """LangChain Embeddings 반환. provider: 'openai'(기본) | 'gemini'."""
    if provider == "openai":
        require_key("OPENAI_API_KEY")
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=OPENAI_EMBED_MODEL)
    elif provider == "gemini":
        require_key("GOOGLE_API_KEY")
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBED_MODEL, output_dimensionality=768
        )
    raise ValueError(f"알 수 없는 provider: {provider}")


if __name__ == "__main__":
    print("ROOT :", ROOT)
    print("DATA :", DATA, "(존재:", DATA.exists(), ")")
    print("OPENAI_MODEL :", OPENAI_MODEL)
    print("키 로드 상태 — OPENAI_API_KEY:", bool(os.getenv("OPENAI_API_KEY")),
          "/ GOOGLE_API_KEY:", bool(os.getenv("GOOGLE_API_KEY")))