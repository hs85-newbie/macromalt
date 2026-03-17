# macromalt 통합 핸드오프 — Phase 5 ~ Phase 15E

작성일: 2026-03-17
기준 커밋: `1857847`
커버 범위: Phase 5 (DART 연동) ~ Phase 15E (현재 연도 과거 월 교정)
다음 단계: **Phase 15F** — 동사 독립 `[전망]` 월 기반 강제 제거
총괄 게이트: **PHASE15E_OUTPUT_HOLD**

> 이 문서는 개별 핸드오프(88_etc/Handoff/ 및 30_reference/Handoff/)를 통합한 인수자용 단일 참조 문서입니다.

---

## 프로젝트 개요

**macromalt**: 한국 주식시장 투자 분석 콘텐츠 자동 생성·발행 파이프라인.

증권사 리서치 + 뉴스 + DART 공시를 수집하여 두 종류의 기사를 LLM으로 생성 후 WordPress에 자동 발행한다.

- **Post1**: [심층분석] 매크로 경제 심층 분석
- **Post2**: [캐시의 픽] 종목 리포트

### 3단계 파이프라인

```
Step 1 — Gemini 2.5 Flash (temp 0.2, 3,000 tok)
  뉴스 + 리서치 PDF + DART 공시 원문 → 구조화 JSON

Step 2a — GPT-4o (temp 0.7, 5,000 tok)
  JSON → Post1 HTML 초고

Step 2b — GPT-4o (temp 0.65, 6,000 tok)
  JSON → Post2 HTML 초고

Step 3 — Gemini 2.5 Flash (temp 0.1 Verifier / 0.3 Reviser)
  HTML 초고 → 팩트체크 → 수정본 채택 → 발행
```

### 주요 파일

| 파일 | 역할 |
|------|------|
| `generator.py` | LLM 호출, 프롬프트, 후처리 (Phase 10~15E 누적 ~+2,200라인) |
| `scraper.py` | 뉴스/리서치 수집, DART API, PDF 파싱 |
| `publisher.py` | WordPress REST API 발행 |
| `main.py` | 슬롯 분기, 게이트 판정, 파이프라인 오케스트레이션 |
| `publish_history.json` | Fingerprint 기반 발행 이력 |
| `portfolio.json` | 누적 발행 기록 |

---

## Phase 진행 일람

| Phase | 커밋 | 날짜 | 핵심 목적 | 구현 | 실출력 |
|-------|------|------|-----------|------|--------|
| 5-A~D | `d7994ef` | 03-13 | DART 연동, PDF enrich, WP 자동 발행 | GO | GO |
| 6 | `c526d46` | 03-13 | 한경 세션, 사업보고서 파싱, DART XML 수정 | GO | GO |
| 7 | `fe36a27` | 03-13 | 최초 실 발행 회귀 검증 | GO | GO |
| 8 | `6474c87` | 03-13 | 시점 일관성·투자 권유 억제 + publish 전환 | GO | GO |
| 9 | `cb8df31` | 03-13 | 운영 회귀 검증 3회차 PASS | GO | GO |
| 10 | `5409bd9` | 03-16 | 슬롯 분기 + 이력 반복 완화 + 최신성 필터 | GO | GO |
| 11 | `077f647` | 03-16 | Fingerprint 기반 반복 완화 엔진 | GO | GO |
| 12 | `25a7cfc` | 03-16 | 증거 밀도 & 글쓰기 품질 강화 | GO | GO |
| 13 | `9416537` | 03-16 | 해석 지성 + 시간/수치 신뢰성 강화 | GO | HOLD* |
| 14 | (13 내) | 03-16 | 생성 강제 + 소스 정규화 | GO | GO |
| 14H | `da817d5` | 03-17 | 전체 재작성 → 타겟 블록 교체 전환 | GO | HOLD→GO |
| 14I | (14H 후속) | 03-17 | 해석 헤징 어미 억제 | GO | GO |
| 15 | `39548b1` | 03-17 | 완료 연도 시제 교정 초기 구현 | GO | HOLD |
| 15A | `39548b1` | 03-17 | 복합 패턴 시제 교정 핫픽스 | GO | GO |
| 15B | `d97f0b2` | 03-17 | 연결어미 커버 확장 | GO | GO |
| 15C | `798d3a6` | 03-17 | Step3 시간 기준점 주입 + Post2 레이블 차단 | GO | GO |
| 15D | `b3f1f89` | 03-17 | `[전망]` 오주입 태그 후처리 제거 | GO | HOLD |
| 15E | `0645e9d` | 03-17 | 현재 연도 과거 월 동사+태그 통합 교정 | GO | HOLD |

*Phase 13 HOLD: hedge_overuse, counterpoint_specificity 일부 차원 지속

---

## Phase 5 — DART 연동 & 데이터 수집 강화

**커밋:** `d7994ef` 외 다수

### 주요 구현

| 컴포넌트 | 내용 |
|----------|------|
| OpenDART API 연동 | 공시 스캔, corp_code 캐시, 재무수치, 기업정보 |
| `_fetch_dart_document_zip` | `document.xml` → ZIP → XML → `full_text` 800자 |
| PDF enrich | `pdfplumber` 기반 네이버금융 리포트 핵심 섹션 추출 |
| WordPress 발행 자동화 | `publisher.py` draft→publish 전환 |
| BROKER_KW | 23개 키워드 (신한투자/NH투자/IBK투자 오탐 정제 포함) |
| DART_TARGET_ACCOUNTS | 9개 재무 계정 |

### 핵심 상수

| 상수 | 값 |
|------|----|
| `_DART_DOC_MAX_CHARS` | 800자 |
| `_PDF_PROMPT_SNIPPET_LEN` | 400자 |
| `enrich_*` max_fetch/max_pdf | 기본값 3 |

---

## Phase 6 — 데이터 수집 확장

**커밋:** `c526d46` 외

| 항목 | 내용 |
|------|------|
| 한경 세션 연동 | `_hankyung_login()` → `enrich_research_with_pdf` 세션 전달 경로 구현 |
| 사업보고서 섹션 파싱 | `_find_annual_report_rcept_no`, `_extract_sections_from_zip` — "사업의 내용" / MD&A |
| DART 엔드포인트 수정 | `document.json` → `document.xml` (공식 경로) |
| BROKER_KW 오탐 정제 | 신한/NH/IBK 키워드 구체화 |
| DEBUG_LLM 플래그 | `DEBUG_LLM=1 python generator.py` |

---

## Phase 7~9 — 실운영 검증

**Phase 7**: 최초 실 발행 1회. 14항목 + P1~P10 전체 PASS.

**Phase 8**: 시점 일관성·투자 권유 억제 규칙 3차 보강.

최종 금지 표현 목록:
```
"매수", "지금 사야 할", "유망", "주목해야 한다", "담아야 한다",
"기회다", "추천한다", "저평가 매력", "매수 기회", "하방 경직성 제공",
"수혜를 받을 수 있는", "실적 개선 효과를 기대할 수 있는"
```

**Phase 9**: 운영 회귀 검증 3회차. 기준1/기준5 위반 0건 안정화. GO.

---

## Phase 10 — 슬롯 분기 & 이력 기반 반복 완화

**커밋:** `5409bd9`

| 컴포넌트 | 내용 |
|----------|------|
| `detect_slot()` | morning / evening / us_open / default 4분류 (DST 고려) |
| `_SLOT_ANALYST_CONTEXTS` | 슬롯별 Gemini 분석 방향 힌트 |
| `_load/save_publish_history()` | `publish_history.json` 기반 이력 관리 |
| `_build_history_context()` | 24h/48h 이내 동일 fingerprint → 관점/하위축 전환 지시 |
| `_log_freshness_summary()` | 7일/30일/초과/불명 자료 건수 로그 |

---

## Phase 11 — Fingerprint 기반 반복 완화

**커밋:** `077f647`

| 함수 | 역할 |
|------|------|
| `_make_theme_fingerprint()` | macro 카테고리 10종 keyword 매핑 |
| `_make_axes_fingerprint()` | sub_axes → axis_id 11종 매핑 |
| `_make_ticker_buckets()` | 티커 → 섹터 버킷 8종 (~40종목) |
| `_build_history_context()` (재작성) | D1 STRONG / D2 BUCKET / D3 MILD 조건부 회전 지시 |

**`publish_history.json` 확장 필드:** `theme_fingerprint`, `sub_axes_fingerprint`, `tickers`, `stock_buckets`

---

## Phase 12 — 증거 밀도 & 품질 강화

**커밋:** `25a7cfc`

| 컴포넌트 | 역할 |
|----------|------|
| `_build_numeric_highlight_block()` | 핵심 수치 추출 → Gemini 입력 앞 주입 |
| `_score_post_quality()` | 5개 품질 지표 rule-based 진단 (비파괴) |
| `_check_post_separation()` | Post1/Post2 h3 헤딩 + 단락 중복 체크 |
| `_P12_QUALITY_THRESHOLDS` | 튜닝 가능 임계값 dict |

**5개 품질 지표:** `numeric_density` / `time_anchor` / `counterpoint_presence` / `generic_wording` / `evidence_binding`

---

## Phase 13 — 해석 지성 & 시간/수치 신뢰성

**커밋:** `9416537`

| 컴포넌트 | 역할 |
|----------|------|
| `_P13_INTERPRETATION_STANDARD` | 비자명성 기준 5조건 (a~e) |
| `_P13_HEDGING_TRIAGE_RULES` | 팩트/분석/전망 3분류 헤징 허용 기준 |
| `_P13_COUNTERPOINT_SPEC` | 반론 3요소 필수 규격 (조건/결과/충돌) |
| `_P13_ANALYTICAL_SPINE_RULE` | `<!-- SPINE: ... -->` 뼈대 주석 강제 |
| `_score_interpretation_quality()` | weak_interp / hedge_overuse / counterpoint_spec 진단 |
| `_check_temporal_consistency()` | 연도/시점 불일치 탐지 |
| `_check_numeric_sanity()` | 수치 합리성 검증 |

**잔존 HOLD (별도 트랙):** hedge_overuse Post1 (16/27), counterpoint_specificity

---

## Phase 14 / 14H / 14I — 생성 강제 + 헤징 억제

**커밋:** `da817d5`

| 컴포넌트 | 역할 |
|----------|------|
| `_normalize_source_for_generation()` | CONFIRMED / FORECAST / AMBIGUOUS 분류 → 프롬프트 주입 |
| `_P14_FEWSHOT_BAD_GOOD_INTERP` | BAD→GOOD 대조 예시 5쌍 |
| `_enforce_interpretation_rewrite()` | [해석] 블록만 타겟 교체 (14H: 전체 재작성 → 블록 단위로 전환) |
| `_P14I_INTERP_HEDGE_ENDINGS` | 억제 대상 헤징 어미 10개 |
| `_detect_interp_hedge_density()` | [해석] 블록 헤징 포화도 측정 |

**14I 실출력 GO 기준:** Post2 hedge_overuse PASS, weak_interp PASS.

---

## Phase 15 계보 — 시제 신뢰도 강화

### Phase 15A/15B — 완료 연도 시제 교정 (GO)

**커밋:** `39548b1` / `d97f0b2`

- `completed_years = range(run_year-3, run_year)` → 2023, 2024, 2025 커버
- `_P15A_COMPOUND_RE_FORMAL`: `([가-힣]+)할(\s+것으로\s+)(추정|예상|전망)됩니다` regex
- `_P15B_COMPOUND_RE_CONNECTIVE`: 연결어미 (되며/되고/되어) 확장

### Phase 15C — Step3 시간 기준점 주입 + Post2 레이블 차단 (GO)

**커밋:** `798d3a6`

- `_P15C_STEP3_TEMPORAL_GROUNDING`: Verifier/Reviser에 `run_year/month` 명시 (46줄)
- `_P15C_POST2_LABEL_BAN`: "Post1", "Post2" 내부 레이블 독자 노출 차단
- `_detect_internal_label_leakage()`: 발행 전 내부 레이블 탐지

### Phase 15D — [전망] 오주입 태그 제거 (HOLD)

**커밋:** `b3f1f89`

- `_P15D_CONFIRMED_VERB_MARKERS`: 확정 어미 19종
- `_strip_misapplied_jeonmang_tags()`: 확정 어미 조건 + (완료 연도 OR 확정 기간) → `[전망]` 제거
- **사각지대:** "파악됩니다" — `_P15D_CONFIRMED_VERB_MARKERS`에 미포함

### Phase 15E — 현재 연도 과거 월 통합 교정 (HOLD) ← 현재 게이트

**커밋:** `0645e9d`

- `_P15E_COMPOUND_RE_NAL_FORMAL/INFORMAL/CONNECTIVE`: "날 것으로 X됩니다" regex
- `_P15E_FORECAST_VERB_MARKERS`: 예측 동사 15종
- `_detect_current_year_past_month_as_forecast()`: Track A/C 위반 탐지
- `_enforce_current_year_month_settlement()`: 동사 교정 + `[전망]` 제거
- **단위 테스트:** 11/11 PASS

---

## generator.py 현재 레이어 구조

```
[Phase 10]  슬롯 분기 + fingerprint (_SLOT_ANALYST_CONTEXTS, _build_history_context)
[Phase 11]  Fingerprint 엔진 (_make_theme_fingerprint, _make_axes_fingerprint)
[Phase 12]  증거 밀도 (_build_numeric_highlight_block, _score_post_quality)
[Phase 13]  해석 지성 (_score_interpretation_quality, _check_temporal_consistency)
[Phase 14]  소스 정규화 + 생성 강제 (_normalize_source_for_generation, few-shot)
[Phase 14H] 타겟 블록 교체 (_enforce_interpretation_rewrite 재작성)
[Phase 14I] 헤징 억제 (_detect_interp_hedge_density)
[Phase 15A] 완료 연도 복합 regex (_P15A_COMPOUND_RE_FORMAL/INFORMAL)
[Phase 15B] 연결어미 확장 (_P15B_COMPOUND_RE_CONNECTIVE)
[Phase 15C] Step3 시간 기준점 주입 + Post2 레이블 차단  (~line 2300)
[Phase 15D] 확정 어미 조건 [전망] 제거  (~line 2371)
[Phase 15E] 현재 연도 과거 월 통합 교정  (~line 2467)
        ↓
[Phase 15F] ← 다음 단계 (미구현)
```

---

## 잔존 이슈 및 다음 단계

### Phase 15F — 즉시 처리 (최소 구현)

**문제:** `[전망]` + `{run_year}년 {past_month}월` 조합 시 동사 형태에 무관하게 태그 잔존.

| 잔존 케이스 | 실패 이유 |
|------------|-----------|
| `파악됩니다` | Phase 15D/15E 탐지 사각지대 |
| `증가한 것으로 추정됩니다` | Phase 15E 탐지 성공, 교정 regex 미매치 |

**설계 (40~60라인):**

```python
def _strip_current_year_past_month_jeonmang(content, run_year, run_month, label) -> tuple:
    # 조건: [전망] 직후 문장에 {run_year}년 {m}월 (m < run_month) 포함
    # 예외: 순수 미래 동사("할 것으로 전망됩니다" 등) → 보존
```

**단위 테스트 케이스:**
- T1: "파악됩니다" 앞 `[전망]` 제거
- T2: "증가한 것으로 추정됩니다" 앞 `[전망]` 제거
- T3: 순수 미래 동사 → `[전망]` 보존

### Phase 16 — 반복 에러 승격 처리

Phase 15A~15E에서 반복된 동사 사각지대 패턴을 Phase 16에서 구조적으로 해결.

**MACROMALT_PHASE_EXECUTION_POLICY** 공통 규칙 적용:
- 매 진행마다 실출력 검증 보고서 → `docs/88_etc/REPORT/`
- 매 진행마다 커밋 + 핸드오프 문서 작성
- 미세 조정 최대 5회 (15F + Phase 16 각각 적용)
- 동일 문제 반복 시 다음 Phase 승격

### 별도 트랙 (우선순위 낮음)

| 이슈 | Phase | 상태 |
|------|-------|------|
| hedge_overuse Post1 FAIL (16/27) | Phase 13/14I | 개선 중, 완전 해소 미완 |
| counterpoint_specificity FAIL | Phase 13 | 미완 |
| 스타일 분리 (tokens.py, templates/) | Style-Sep | 설계 완료 (`20_tracks/wordpress_style/`) |

---

## 발행 이력 (주요 런)

| run_id | Post IDs | 게이트 | 비고 |
|--------|----------|--------|------|
| 20260317_112105 | 143/144 | Phase 14I GO | |
| 20260317_180244 | 158/159 | PHASE15D_OUTPUT_HOLD | |
| 20260317_190543 | 160/161 | PHASE15E_OUTPUT_HOLD | 현재 최신 |

---

## 인수자 체크리스트

- [ ] Phase 15F `_strip_current_year_past_month_jeonmang()` 구현 (40~60라인)
- [ ] Post1/Post2 call site 연결 (Phase 15E 이후)
- [ ] 단위 테스트 T1~T3 PASS 확인
- [ ] 실출력 검증 → REPORT 저장 → 커밋 → 핸드오프
- [ ] GO 판정 시 Phase 16 설계 착수
- [ ] hedge_overuse / counterpoint_specificity 별도 트랙 (Phase 15F 이후)

---

## 파일/디렉토리 위치

| 항목 | 경로 |
|------|------|
| 핸드오프 (현행) | `docs/88_etc/Handoff/` |
| 핸드오프 (아카이브) | `docs/30_reference/Handoff/` |
| 실출력 검증 보고서 | `docs/88_etc/REPORT/` |
| 프롬프트 파일 | `jobs/` |
| 정책 문서 | `docs/10_policies/` |
| 스타일 트랙 | `docs/20_tracks/wordpress_style/` |
