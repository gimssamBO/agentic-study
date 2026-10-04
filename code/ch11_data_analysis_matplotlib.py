import matplotlib
matplotlib.use("Agg")  # 화면 없는 서버/CI 환경에서도 동작하도록 파일 저장용 백엔드 설정

import matplotlib.pyplot as plt
import koreanize_matplotlib   # 한글 폰트 깨짐 자동 처리
import pandas as pd
from common import get_chat, DATA, ROOT

# OpenAI 환경 표준화 (프로젝트 공통)
llm = get_chat(provider="openai")

# 데이터 로드
df = pd.read_csv(DATA / "monthly_sales.csv", encoding="utf-8-sig")

# 차트를 저장할 reports 폴더 (없으면 자동 생성)
out_dir = ROOT / "reports"
out_dir.mkdir(exist_ok=True)

# 월별 total 꺾은선 그래프 생성
fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(df["month"], df["total"], marker="o", color="#2563eb")
ax1.set_title("승승장구몰 월별 총매출 추이")
ax1.set_xlabel("월")
ax1.set_ylabel("총매출(원)")

# y축 숫자에 천단위 콤마 포맷팅
ax1.yaxis.set_major_formatter(lambda x, _: f"{int(x):,}")
plt.xticks(rotation=45, ha="right")     # x축 라벨 45도 기울이기

fig1.tight_layout()
fig1.savefig(out_dir / "11_월별총매출_꺾은선.png", dpi=120)   # 이미지 파일로 저장
plt.close(fig1)

print(f"차트 생성 및 저장 완료: {out_dir / '11_월별총매출_꺾은선.png'}")