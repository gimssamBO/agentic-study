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


# 가장 최근 달의 카테고리별 매출
categories = [c for c in df.columns if c not in ("month", "total")]
last = df.iloc[-1]                          # 마지막 행 (최근 달)
values = [last[c] for c in categories]

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.bar(categories, values, color="#16a34a")     # 막대그래프
ax2.set_title(f"{last['month']} 카테고리별 매출")
ax2.set_xlabel("카테고리")
ax2.set_ylabel("매출(원)")
ax2.yaxis.set_major_formatter(lambda x, _: f"{int(x):,}")
plt.xticks(rotation=45, ha="right")
fig2.tight_layout()
fig2.savefig(out_dir / "11_카테고리별매출_막대.png", dpi=120)
plt.close(fig2)

print(f"차트 생성 및 저장 완료: {out_dir / '11_월별총매출_막대.png'}")