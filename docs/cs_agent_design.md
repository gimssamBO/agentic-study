# cs 티켓 자동 분류·답변 에이전트 — 설계 문서

## 1. 요구사항 분석
- 목적: 고객 지원 티켓을 자동으로 심각도 분류하고 답변 초안을 생성한다.
- 입력: data/support_tickets.csv 의 `content`(티켓 본문 텍스트)
- 출력: severity(긴급/보통/낮음) + 답변 초안(마크다운)
- 사용자 시나리오:
  - t1 "결제했는데 주문이 안 보여요" → 긴급 분류 + 즉시 안내 초안
  - t2 "배송 언제 와요?" → 보통 분류 + faq 기반 안내

## 2. 도구 목록
| 도구 | 입력 → 출력 | 설명 |
|------|-------------|------|
| classify_severity(content: str) | str → str | 티켓 본문을 '긴급/보통/낮음'으로 분류 |
| search_faq(keyword: str) | str → str | data/faq.csv 에서 관련 faq 답변 검색 |
| draft_reply(content: str, faq: str) | (str, str) → str | 티켓+faq 근거로 답변 초안 작성 |

## 3. 데이터 흐름
티켓(content) → classify_severity(분류) → search_faq(근거 검색)
→ draft_reply(초안 생성) → [severity + 답변 초안]

## 4. 아키텍처 (흐름)
1. support_tickets.csv (content)
2. → classify_severity → severity(긴급/보통/낮음)
3. → search_faq(키워드) → faq.csv 에서 근거
4. → draft_reply(티켓, 근거) → 답변 초안
5. → [출력] severity + 답변 초안

## 5. 구성요소 판단
- 도구: ✅ (분류·검색·작성)
- rag: △ faq가 짧으면 csv 검색으로 충분, 길고 많아지면 rag로 승격
- 메모리: ❌ 티켓 단건 처리라 대화 맥락 불필요
- 멀티에이전트: ❌ 도구 3개 → 단일로 시작