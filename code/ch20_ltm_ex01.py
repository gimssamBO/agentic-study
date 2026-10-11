import json
import pathlib
import shutil
import sys

# 1. pathlib.path -> pathlib.Path 교정
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import DATA, get_chat
from langchain.agents import create_agent
from langchain_core.tools import tool

# 2. 경로 상수 정의 (common 모듈의 DATA와 변수명 충돌 방지)
store = DATA / "user_profiles_rw.json"
src = DATA / "user_profiles.json"


def _load():
    if not store.exists():
        shutil.copy(src, store)
    with open(store, encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    # ensure_ascii=false -> False 오타 교정
    with open(store, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@tool
def get_profile(user_id: str) -> str:
    """고객id로 프로필을 조회한다."""
    # ensure_ascii=false -> False 오타 교정
    return json.dumps(_load().get(user_id, {}), ensure_ascii=False)


@tool
def update_profile(user_id: str, key: str, value: str) -> str:
    """프로필의 한 항목을 갱신해 영속 저장한다."""
    data = _load()
    data.setdefault(user_id, {})[key] = value
    _save(data)
    return f"{user_id}의 {key}를 {value}로 저장했습니다."


# 3. 에이전트 생성 및 실행
agent = create_agent(
    get_chat(temperature=0),
    tools=[get_profile, update_profile],
    system_prompt="너는 상담원이다. 선호를 말하면 update_profile로 저장하라.",
)

out = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "나 C0001인데 선호 카테고리를 가전으로 바꿔줘",
            }
        ]
    }
)
print(out["messages"][-1].content)

# 4. 파일에서 저장 결과 검증
print("파일 확인:", _load()["C0001"].get("선호카테고리"))