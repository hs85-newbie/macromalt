# macromalt Phase 6 ~ 8 통합 핸드오프

**기준일: 2026-03-13 | 브랜치: `main` | 최종 커밋: `6474c87`**
**문서 경로: `docs/handoff_phase6to8.md`**

---

## 0. 컨텍스트

Phase 5까지 구축된 파이프라인 위에 Phase 6~8을 통해 아래 세 영역을 개선함:

| Phase | 핵심 목표 |
|---|---|
| 6 | 데이터 수집 확장 — 한경 세션, 사업보고서 섹션 파싱, DART 엔드포인트 수정 |
| 7 | 실운영 회귀 검증 — 파이프라인 최초 실 발행 1회 |
| 8 | 품질 보강 — 시점 일관성·투자 권유 억제 규칙 강화 + publish 전환 |

---

## 1. Phase 6 — 데이터 수집 확장

### 1-A. 한경 세션 연동 (`863afba`)

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| `_fetch_pdf_bytes` 시그니처 | `session` 미지원 | `session=None` 파라미터 추가 |
| `enrich_research_with_pdf` | 세션 미전달 | `_hankyung_login()` 세션 전달 지원 |
| `generator.py` | 세션 없이 호출 | Post1/Post2 각 호출부에 `session=` 전달 |
| `sources.json` | naver_research 산업 페이지만 | `company_list.naver` 종목 페이지 추가 |

> **운영 상태**: `_hankyung_login()` 세션 전달 경로는 구현 완료. 실 인증 연동 검증은 Phase 7 이후 운영 모니터링 항목으로 분리.

### 1-B. BROKER_KW 오탐 정제 (`863afba`)

금융계열사(은행·보험) 오탐 방지:

| 이전 키워드 | 수정 키워드 | 이유 |
|---|---|---|
| `"신한"` | `"신한투자"` | 신한은행·신한카드 오탐 차단 |
| `"NH"` | `"NH투자"` | NH농협 오탐 차단 |
| `"IBK"` | `"IBK투자"` | IBK기업은행 오탐 차단 |

### 1-C. DART 원문 API 엔드포인트 수정 (`6624719` → `c439c98` cherry-pick 통합)

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| 엔드포인트 | `document.json` (HTTP 200 + `status=101` 오류) | `document.xml` |
| 이유 | `document.json`은 공식 미지원 엔드포인트 | `document.xml` 이 ZIP 반환 공식 경로 |

### 1-D. 사업보고서 핵심 섹션 파싱 (`4d7ac37` + `d54b462` + `350ef1e` + `e0c0f09`)

**신규 함수 (scraper.py Section 17):**

```
_find_annual_report_rcept_no(corp_code)
  → list.json?pblntf_ty=A&bgn_de=2년전&end_de=오늘&page_count=10
  → items 중 report_nm에 "사업보고서" 포함 첫 번째 rcept_no 반환
  (pblntf_detail_ty=A001 미작동 → report_nm 문자열 필터로 대체)

_extract_sections_from_zip(rcept_no, corp_code)
  → ZIP 내 단일 대형 XML 전체 텍스트(raw.find(kw)) 검색
  (probe 방식 앞 200자 탐지 실패 → 전체 텍스트 검색으로 교체)
  → _ANNUAL_SECTION_KEYWORDS dict 순서로 섹션 추출

run_dart_annual_report_sections(tickers)
  → 종목코드 리스트 → {code: {섹션명: 텍스트}} 반환
```

**_ANNUAL_SECTION_KEYWORDS (fallback 정책 포함):**

```python
{
    "사업의 내용":  ["사업의 내용"],
    "재무상태":    ["재무상태", "재무제표", "재무위험", "재무위험관리", "유동성"],
    "MD&A":       ["MD&A"],
    "경영진의 논의": ["경영진의 논의"],
}
```
- 1순위 키워드 직접 매칭 → 없으면 fallback 순서대로 탐색
- fallback 사용 시 `INFO: [DART/annual] '{canonical}' fallback 매칭: '{primary}' 없음 → '{kw}' 사용` 로그 출력

**generator.py 주입 위치:**
- Post2 Step 1D-2 블록: `run_dart_financials` 직후 호출
- `[DART 사업보고서 핵심 섹션]` context_text → Step1 Gemini 프롬프트 삽입

### 1-E. DEBUG_LLM 플래그 (`43b62f2` + `6b4f76d`)

```bash
DEBUG_LLM=1 python generator.py
```

- LLM 호출 직전 payload 파라미터 DEBUG 레벨 로그 출력
- scraper.py `basicConfig(INFO)` 선점 문제 → named logger 레벨 직접 조정으로 해결

---

## 2. Phase 7 — 실운영 회귀 검증 (`fe36a27`)

**목표**: 파이프라인 최초 실 발행 1회 및 데이터 수집 경로 확인

| 항목 | 결과 |
|---|---|
| Post1/Post2 생성 | 완료 |
| DART 사업보고서 섹션 추출 | `['사업의 내용', '재무상태']` 확인 |
| 검증 기준 (14항목 + P1~P10) | 전체 PASS |
| 발행 상태 | `draft` (publisher.py 미수정 상태) |
| portfolio.json | 업데이트 커밋 완료 |

> Phase 7은 회귀 검증 목적으로, 신규 코드 변경 없음.

---

## 3. Phase 8 — 품질 보강

### 3-A. 프롬프트 규칙 강화 (3회차 보정)

#### 1차 보강 (`3395356`)
- Step2a: 미래 연도 숫자 [전망] 태그 의무화 규칙 추가
- Step2a 자기검수: 시점 키워드 + 투자 권유성 표현 체크리스트 추가
- Step2b 작성규칙2: 투자 권유 금지 표현 목록 초기 구성
- Step3 기준1③: 시점 단정 서술 탐지 기준 추가
- Step3 기준5: 투자 권유 탐지 표현 목록 초기 구성
- Step3 수정규칙4: 투자 권유성 문장 치환 규칙 추가

#### 2차 보강 — 금지 표현 3개 추가 (`003ff63`)

| 위치 | 추가 표현 |
|---|---|
| Step3 기준5 | `"저평가 매력"`, `"매수 기회"`, `"하방 경직성 제공"` |
| Step3 수정규칙4 | 동일 3개 — 분석형 문장 치환 대상 |

#### 3차 보강 — 기준1 오탐 제거 + 표현 2종 추가 (`5fc5b82`)

**기준1 오탐 제거:**
- 과거 확정 실적·집계값 (예: `2024년 매출액`, `2025년 실적`)은 [전망] 강제 대상에서 제외
- `2026년`, `가이던스`, `전망`, `예상`, `추정`, `상향 조정`, `하향 조정` 포함 문장만 계속 적용

**기준5 표현 2종 추가 (Step2a/2b/Step3 기준5/수정규칙4 전체 동기화):**
- `"수혜를 받을 수 있는"`
- `"실적 개선 효과를 기대할 수 있는"`

### 3-B. 최종 금지 표현 목록 (Phase 8 완료 시점 기준)

```
"매수", "매수하세요", "지금 사야 할", "유망", "주목해야 한다", "담아야 한다",
"기회다", "추천한다", "매력적인 선택지", "관심 가져볼 만한", "주가 상승을 견인",
"장기 성장 가능성을 갖춘", "긍정적으로 평가", "수혜가 기대",
"저평가 매력", "매수 기회", "하방 경직성 제공",
"수혜를 받을 수 있는", "실적 개선 효과를 기대할 수 있는"
```

### 3-C. publisher.py: draft → publish 전환 (`6ded3a0`)

```python
# 변경 전
"status": "draft"
# 변경 후
"status": "publish"
```

### 3-D. 기존 draft 포스트 수동 publish 전환 (운영 작업)

WP REST API `POST /wp-json/wp/v2/posts/{id}` + `{"status": "publish"}`

| Post | ID | 발행 URL |
|---|---|---|
| Post1 (심층분석) | p=104 | https://macromalt.com/심층분석-중동-지정학적-리스크-고조에-따른-국제-유-2/ |
| Post2 (캐시의 픽) | p=105 | https://macromalt.com/캐시의-픽-sk하이닉스-외-중동-리스크와-유가-상승/ |

---

## 4. 전체 커밋 이력 (Phase 6 ~ 8)

| 커밋 | Phase | 내용 |
|---|---|---|
| `330d8e3` | 5-C/5-D | DART 원문 파싱 + 통합 품질 재검증 (Phase 5 마무리) |
| `863afba` | 6-A | 한경 세션 연동 / 종목 리포트 페이지 / BROKER_KW 오탐 정제 |
| `4d7ac37` | 6-B | 사업보고서 핵심 섹션 파싱 + Post2 주입 |
| `6624719` | 6-B | DART document.json → document.xml 수정 |
| `c439c98` | 6-B | document.xml 수정 cherry-pick 통합 |
| `d54b462` | 6-B | _extract_sections_from_zip probe→전체텍스트 검색 교체 |
| `a973396` | 6-B | docs: 사업보고서 섹션 추출 우선순위 정책 반영 |
| `350ef1e` | 6-B | 재무상태 섹션 fallback 키워드 정책 적용 |
| `e0c0f09` | 6-B | 재무상태 fallback 정책 확대 + INFO 로그 |
| `c526d46` | 6 | Phase 6-A/B worktree → main merge |
| `eaab3c7` | 6 | _find_annual_report_rcept_no bgn_de 추가 + report_nm 필터 |
| `43b62f2` | 6 | DEBUG_LLM 플래그 추가 |
| `6b4f76d` | 6 | DEBUG_LLM 로그 레벨 수정 |
| `fe36a27` | 7 | Phase 7 운영 검증 후 portfolio.json 업데이트 |
| `3395356` | 8 | 시점 일관성 + 투자 권유성 표현 억제 규칙 강화 1차 |
| `003ff63` | 8 | Step3 기준5/수정규칙 금지 표현 3개 추가 |
| `5fc5b82` | 8 | 기준1 오탐 제거 + 기준5 표현 2종 추가 |
| `6ded3a0` | 8 | publisher.py draft → publish |
| `4c3084e` | 8 | portfolio.json 업데이트 |
| `6474c87` | 8 | docs: handoff_phase8.md 작성 |

---

## 5. Phase 8 품질 지표

| 지표 | Phase 8 시작 | 최종 |
|---|---|---|
| 기준1/5 위반 합계 | 10건 | **1건 이하** |
| 기준1 오탐 (과거 확정 실적) | 발생 | **제거** |
| publish 상태 발행 | ❌ draft | ✅ publish |

---

## 6. 현재 LLM 파라미터 (Phase 5 이후 변경 없음)

| Step | 모델 | temperature | max_tokens |
|---|---|---|---|
| Step1 (분석재료) | Gemini 2.5 Flash | 0.2 | 3,000 |
| Step2a (심층분석) | GPT-4o | 0.7 | 5,000 |
| Step2b (종목리포트) | GPT-4o | 0.65 | 6,000 |
| Step3 팩트체크 | Gemini 2.5 Flash | 0.1 | 3,000 |
| Step3 수정 | Gemini 2.5 Flash | 0.3 | 3,000 |
| thinking_budget | — | — | 0 |

---

## 7. 잔존 이슈 → Phase 9 인계

| 항목 | 내용 | 우선순위 |
|---|---|---|
| 기준5 완충 표현 | "수익성이 개선될 여지", "가능성이 크다" 계열 반복 생성 — reviser가 매번 수정 처리 중 | 중 |
| 기준1 혼합 문장 | 과거 실적 + 미래 전망 한 문장 혼합 — 예외 규칙 미적용 케이스 잔존 | 중 |
| 한경 세션 실 인증 연동 | 세션 전달 경로 구현 완료. 실 PDF 수신 여부 미검증 | 중 |
| 기준12 오탐 | verifier가 마크다운 없음을 항상 위반 보고 — HTML 전용 포맷이므로 기준12 삭제 검토 | 저 |
| 기준15 종목 4단계 | Post2에서 간헐적 미달 — Step2b 종목 구조 규칙 보강 여지 | 저 |

---

**repo**: `https://github.com/hs85-newbie/macromalt` | **branch**: `main` | **head**: `6474c87`
