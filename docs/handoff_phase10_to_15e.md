# 마스터 핸드오프 — Phase 10 ~ Phase 15E 전체 세션 이력

작성일: 2026-03-17
세션 범위: Phase 10 (슬롯 분기) → Phase 15E 실출력 검증
최종 게이트: **PHASE15E_OUTPUT_HOLD**
다음 단계: **Phase 15F — 동사 형태 독립 월 기반 `[전망]` 강제 제거**

> 이 문서는 해당 채팅 세션에서 진행된 모든 Phase의 통합 핸드오프입니다.
> 각 Phase별 상세 내용은 `docs/` 내 개별 보고서 및 핸드오프 파일을 참조하세요.

---

## 전체 Phase 진행 일람

| Phase | 커밋 | 날짜 | 목적 | 구현 | 실출력 |
|-------|------|------|------|------|--------|
| 10 | `5409bd9` | 03-16 | 슬롯 분기 + 이력 반복 완화 + 최신성 필터 | GO | GO |
| 11 | `077f647` | 03-16 | Fingerprint 기반 반복 완화 엔진 | GO | GO |
| 12 | `25a7cfc` | 03-16 | 증거 밀도 & 글쓰기 품질 강화 | GO | GO |
| 13 | `9416537` | 03-16 | 해석 지성 + 시간/수치 신뢰성 강화 | GO | HOLD* |
| 14 | (13 내 배선) | 03-16 | 생성 강제 + 소스 정규화 | GO | GO |
| 14H | `da817d5` | 03-17 | 전체 재작성 → 타겟 블록 교체 전환 | GO | HOLD |
| 14I | (14H 후속) | 03-17 | 해석 헤징 어미 억제 + 실출력 GO | GO | GO |
| 15 | `39548b1` | 03-17 | 완료 연도 시제 교정 초기 구현 | GO | HOLD |
| 15A | `39548b1` | 03-17 | 복합 패턴 시제 교정 핫픽스 | GO | HOLD |
| 15B | `d97f0b2` | 03-17 | 연결어미 커버 확장 마이크로 핫픽스 | GO | HOLD |
| 15C | `798d3a6` | 03-17 | Step3 시간 기준점 주입 + Post2 내부 레이블 차단 | GO | GO |
| 15D | `b3f1f89` | 03-17 | `[전망]` 오주입 태그 후처리 제거 | GO | HOLD |
| 15E | `0645e9d` | 03-17 | 현재 연도 과거 월 동사+태그 통합 교정 | GO | HOLD |

*Phase 13 실출력 HOLD는 일부 차원에서 지속 중 (hedge_overuse, counterpoint_specificity)

---

## Phase 10 — 슬롯 분기 & 이력 기반 반복 완화

**커밋:** `5409bd9` | **파일:** `main.py`, `generator.py`, `scraper.py`

**해결한 문제:**
- 아침/저녁/미장 오픈 시점 구분 없이 동일 톤으로 발행
- 전날 같은 테마를 다시 발행하더라도 차별화 없음
- 소스 자료 최신성 미표시

**주요 구현:**

| 컴포넌트 | 내용 |
|----------|------|
| `detect_slot()` in `main.py` | morning / evening / us_open / default 4분류. us_open: DST 21:30~22:29 / non-DST 22:30~23:29 |
| `_SLOT_ANALYST_CONTEXTS` | 슬롯별 Gemini 분석 방향 힌트 상수 |
| `_load_publish_history()` / `_save_publish_history()` | `publish_history.json` 기반 이력 저장/로드 |
| `_build_history_context()` | 24h 이내 동일 sub_axes → 관점 전환 / 동슬롯 48h 이내 → 하위 축 전환 지시 생성 |
| `_log_freshness_summary()` | 7일/30일/초과/불명 자료 건수 로그 |

**인수자 참고:** `generate_deep_analysis()`, `generate_stock_picks_report()` 모두 `slot` 인자 추가됨.

---

## Phase 11 — Fingerprint 기반 반복 완화 엔진

**커밋:** `077f647` | **파일:** `generator.py`

**해결한 문제:**
Phase 10의 이력 비교가 "테마 문자열 직접 비교" 방식이어서 같은 테마를 다른 표현으로 쓰면 반복 미감지.

**주요 구현:**

| 함수 | 역할 |
|------|------|
| `_make_theme_fingerprint()` | macro 카테고리 10종 keyword 매핑 → 정규화 ID |
| `_make_axes_fingerprint()` | sub_axes → axis_id 11종 매핑 |
| `_make_ticker_buckets()` | 티커 → 섹터 버킷 8종 (약 40종목) |
| `_build_history_context()` (재작성) | D1 STRONG / D2 BUCKET / D3 MILD 조건부 회전 지시. 완전 차단 대신 조건부 |

**`save_publish_history()` 확장 저장 필드:**
`theme_fingerprint`, `sub_axes_fingerprint`, `tickers`, `stock_buckets`

---

## Phase 12 — 증거 밀도 & 글쓰기 품질 강화

**커밋:** `25a7cfc` | **파일:** `generator.py`, `main.py`
**상세 핸드오프:** `docs/handoff_phase12.md`

**해결한 문제:**
구조 규칙은 있으나 수치·시점·출처 없는 범용 AI 요약문 수준의 생성.

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_build_numeric_highlight_block()` | 수집 자료의 핵심 수치 추출 → Gemini 입력 앞 주입 |
| `_score_post_quality()` | 5개 품질 지표 rule-based 진단 (비파괴) |
| `_check_post_separation()` | Post1/Post2 h3 헤딩 + 단락 중복 체크 |
| `_P12_QUALITY_THRESHOLDS` | 튜닝 가능 임계값 dict (코드 수정 없이 조정 가능) |

**5개 품질 지표:** numeric_density / time_anchor / counterpoint_presence / generic_wording / evidence_binding

---

## Phase 13 — 해석 지성 & 시간/수치 신뢰성 강화

**커밋:** `9416537` | **파일:** `generator.py`, `main.py`
**상세 핸드오프:** `docs/handoff_phase13.md`

**해결한 문제:**
- [해석]/[전망] 태그 존재하나 교과서 인과관계만 전달
- 모든 문장 헤징 어미 기계적 반복
- 반론이 카테고리 이름 수준 (변동성, 불확실성)
- Post2 도입부가 Post1 매크로 설정 반복

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_P13_INTERPRETATION_STANDARD` | 비자명성 기준 5조건 (a~e) |
| `_P13_HEDGING_TRIAGE_RULES` | 팩트/분석/전망 3분류 헤징 허용 기준 |
| `_P13_COUNTERPOINT_SPEC` | 반론 3요소 필수 규격 (조건/결과/충돌) |
| `_P13_ANALYTICAL_SPINE_RULE` | `<!-- SPINE: ... -->` 뼈대 주석 강제 |
| `_P13_POST2_CONTINUITY_RULE` | Post2 → Post1 배경 재설명 금지 |
| `_score_interpretation_quality()` | weak_interp / hedge_overuse / counterpoint_spec 진단 |
| `_check_temporal_consistency()` | 연도/시점 불일치 탐지 |
| `_check_numeric_sanity()` | 수치 합리성 검증 (2026 KOSPI 5,000+ 기준 재보정) |
| `_check_post_continuity()` | n-gram 중복 + 배경 재설명 패턴 체크 |

---

## Phase 14 — Generation Enforcement & Source Normalization

**파일:** `generator.py`, `main.py`
**상세 핸드오프:** `docs/handoff_phase14.md`

**해결한 문제:**
Phase 13 탐지기가 작동하나 GPT 생성 결과가 바뀌지 않음. 소스 데이터 전망형 어미가 팩트 서술 오염.

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_normalize_source_for_generation()` | CONFIRMED / FORECAST / AMBIGUOUS 소스 분류 → 프롬프트 주입 |
| `_P14_FEWSHOT_BAD_GOOD_INTERP` | BAD→GOOD 대조 예시 5쌍 |
| `_P14_ANALYTICAL_SPINE_ENFORCEMENT` | SPINE 주석 강제 주입 |
| `_P14_POST2_CONTINUATION_TEMPLATE` | Post2 연속성 강제 템플릿 |
| `_enforce_interpretation_rewrite()` | weak_interp / hedge_overuse FAIL 시 재작성 루프 |
| `_check_verifier_revision_closure()` | Step3 검수 이슈 해소 여부 확인 |

---

## Phase 14H — 타겟 블록 교체 핫픽스

**커밋:** `da817d5` | **보고서:** `docs/REPORT_PHASE14_TARGETED_REWRITE_HOTFIX.md`

**문제:**
`_enforce_interpretation_rewrite()`가 기사 전체를 Gemini로 재작성해서 Phase 12-13이 만든 구조·수치를 파괴.

**해결:**
전체 재작성 → `[해석]` 블록만 식별해 타겟 블록 단위 교체. 나머지 본문 보존.

**`_P14_WEAK_INTERP_PATTERNS`:** 문장 레벨에서 (키워드1, 키워드2) 쌍이 동일 문장 내 공존 시에만 weak_hit 카운트 (기존: 기사 전체 plain에서 검사 → 오탐 다수).

---

## Phase 14I — 해석 헤징 어미 억제

**보고서:** `docs/REPORT_PHASE14I_INTERPRETATION_HEDGE_CLAMP.md`

**문제:**
Phase 14H 이후 [해석] 섹션이 "~것으로 판단됩니다", "~것으로 보입니다" 같은 헤징 어미를 과도 사용. 독자 신뢰 저하.

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_P14I_INTERP_HEDGE_ENDINGS` | 억제 대상 헤징 어미 10개 |
| `_P14I_INTERP_HEDGE_CLAMP` | GPT/Gemini 프롬프트 주입용 금지 지시 블록 |
| `_detect_interp_hedge_density()` | [해석] 블록 헤징 포화도 측정 |
| `_extract_hedge_heavy_interp_blocks()` | 헤징 과다 [해석] 블록 추출 |
| `hedge_overuse_status` 파라미터 | `_enforce_interpretation_rewrite()` 트리거 경로 추가 |

**실출력 GO 기준:** Post2 hedge_overuse PASS, weak_interp PASS.
**참고 보고서:** `docs/REPORT_PHASE14I_REAL_OUTPUT_VALIDATION.md`

---

## Phase 15 (초기) — 완료 연도 시제 교정

**커밋:** `39548b1` 포함 | **보고서:** `docs/REPORT_PHASE15_TEMPORAL_TENSE_ENFORCEMENT.md`

**문제:**
Phase 14I 실출력 검증(run_id 20260317_112105)에서 Post2가 2024년 SK하이닉스 연간 실적을 "예상치"로 표기. 2026년 기사에서 2024년 확정 실적은 과거 사실이어야 함.

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_P15_COMPLETED_YEAR_FORECAST_VERBS` | 완료 연도에 쓰이면 안 되는 예측 동사 목록 |
| `_P15_TENSE_CORRECTION_MAP` | 예측 동사 → 확정 동사 매핑 |
| `_P15_TEMPORAL_TENSE_ENFORCEMENT` | Step3 Verifier/Reviser 시제 강제 프롬프트 블록 |
| `_detect_completed_year_as_forecast()` | 완료 연도 + 예측 동사 조합 탐지 |
| `_enforce_tense_correction()` | 탐지 후 map 기반 동사 교정 |

**커버 연도:** `completed_years = range(run_year-3, run_year)` → 2023, 2024, 2025

---

## Phase 15A — 복합 패턴 시제 교정 핫픽스

**커밋:** `39548b1` | **보고서:** `docs/REPORT_PHASE15A_COMPOUND_TENSE_CORRECTION_HOTFIX.md`

**문제:**
Phase 15 초기 단일 동사 교정만으로는 "기록할 것으로 추정됩니다" 같은 복합 동사 패턴 미처리. 또한 `[전망]` 태그가 교정 후에도 잔존.

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_P15A_COMPOUND_RE_FORMAL` | `([가-힣]+)할(\s+것으로\s+)(추정\|예상\|전망\|기대\|관측)됩니다` regex |
| `_P15A_COMPOUND_RE_INFORMAL` | 된다 어미 regex |
| `_P15A_FUTURE_STEM_RE` | 잔여 미래 어간 탐지 |
| `_has_mixed_tense_residue()` | 교정 후 잔여 예측 어미 재검사 |
| `_enforce_tense_correction()` Step 0 추가 | regex 복합 교정 먼저 수행 |

---

## Phase 15B — 연결어미 커버 확장 마이크로 핫픽스

**커밋:** `d97f0b2` | **보고서:** `docs/REPORT_PHASE15B_VERB_ENDING_COVERAGE_MICRO_HOTFIX.md`

**문제:**
Phase 15A regex가 `됩니다`/`된다`만 커버. "전망되며", "전망되고", "전망되어" 등 연결어미 형태가 교정되지 않고 남음.

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_P15B_COMPOUND_RE_CONNECTIVE` | `([가-힣]+)할(\s+것으로\s+)(추정\|전망\|...)(되며\|되고\|되어)` regex |
| `_P15B_CONNECTIVE_ENDING_MAP` | 연결어미 → 확정 연결어미 매핑 (됩니다→됐습니다, 되며→됐으며, ...) |
| `_enforce_tense_correction()` Step 0b 추가 | 연결어미 교정 패스 |

---

## Phase 15C — Step3 시간 기준점 주입 + Post2 내부 레이블 차단

**커밋:** `798d3a6` | **보고서:** `docs/REPORT_PHASE15C_STEP3_TEMPORAL_CONTEXT_AND_POST2_LABEL_FIX.md`

**문제:**
- Step3 Verifier가 "2026년 2월 데이터는 3월에도 전망치"라는 오판을 내림 → Phase 15A/B 교정 후 Step3가 다시 오염
- Post2 본문에 "Post1의 결론에 따르면" 같은 내부 파이프라인 레이블 노출

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_P15C_STEP3_TEMPORAL_GROUNDING` | Step3 Verifier/Reviser에 주입하는 시간 기준점 지시문 (46줄). run_year/month 명시, 과거 연도 범위 정의 |
| `_P15C_POST2_LABEL_BAN` | Post2 user_msg 최우선 prepend — "Post1", "Post2" 내부 레이블 독자 노출 금지 |
| `_detect_internal_label_leakage()` | Post2 발행 전 내부 레이블 노출 탐지 함수 |
| `_P13_POST2_CONTINUITY_RULE` 수정 | 예시 표현 "Post1 분석에서" → 독자용 표현으로 교체 |

---

## Phase 15D — `[전망]` 오주입 태그 후처리 제거

**커밋:** `b3f1f89` | **보고서:** `docs/REPORT_PHASE15D_JEONMANG_TAG_STRIP.md`
**실출력 검증:** `docs/REPORT_PHASE15D_REAL_OUTPUT_VALIDATION.md` (HOLD)

**문제:**
Phase 15A/B/C가 동사 교정 후에도 `[전망]` 텍스트 태그가 문장 앞에 잔존. 확정 실적 문장에 `[전망]` 붙으면 독자가 "아직 모르는 수치"로 인식.

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_P15D_CONFIRMED_VERB_MARKERS` | 확정 어미 목록 (집계됐습니다, 기록됐습니다, 달성했습니다 등 19종) |
| `_strip_misapplied_jeonmang_tags()` | 조건: (완료 연도 OR 확정 기간) AND 확정 어미 → `[전망]\s*` 제거. 역순 처리로 인덱스 보존 |

**실출력 성과:**
- 2025년 SK하이닉스 `[전망]` 제거 ✅
- 2026년 2월 양극재 `[전망]` → **미해결** (동사가 "늘어날 것으로 전망됩니다" — 확정 어미 없음)

---

## Phase 15E — 현재 연도 과거 월 동사+태그 통합 교정

**커밋:** `0645e9d` | **보고서:** `docs/REPORT_PHASE15E_CURRENT_YEAR_PAST_MONTH_SETTLEMENT_FIX.md`
**실출력 검증:** `docs/REPORT_PHASE15E_REAL_OUTPUT_VALIDATION.md` (HOLD)

**문제:**
Phase 15D는 확정 어미가 이미 있어야 `[전망]` 제거 가능. 그러나 현재 연도 과거 월(2026년 2월) 데이터에 "늘어날 것으로 전망됩니다" 같은 예측 어미가 함께 있으면 Phase 15D가 작동하지 않음.

**주요 구현:**

| 컴포넌트 | 역할 |
|----------|------|
| `_P15E_COMPOUND_RE_NAL_FORMAL/INFORMAL/CONNECTIVE` | "날 것으로 X됩니다/된다/되며" regex (늘어날, 기록날 등) |
| `_P15E_FORECAST_VERB_MARKERS` | 현재 연도 과거 월 탐지용 예측 동사 15종 |
| `_detect_current_year_past_month_as_forecast()` | 현재 연도 + 과거 월 + 예측 동사 조합 탐지 |
| `_enforce_current_year_month_settlement()` | Step1: 동사 교정 (15A/15B + 15E regex). Step2: `[전망]` 제거 |

**단위 테스트:** 11/11 PASS

**실출력 HOLD 원인:**
1. "증가한 것으로 추정됩니다" — "한 것으로" 패턴 regex 미매치
2. "파악됩니다" 동사 — Phase 15D/15E 탐지 사각지대. `[전망]` 잔존

---

## 현재 generator.py 레이어 구조

```
[Phase 10]  슬롯 분기 + 이력 fingerprint (_SLOT_ANALYST_CONTEXTS, _build_history_context)
[Phase 11]  Fingerprint 엔진 (_make_theme_fingerprint, _make_axes_fingerprint, _make_ticker_buckets)
[Phase 12]  증거 밀도 (_build_numeric_highlight_block, _score_post_quality)
[Phase 13]  해석 지성 (_score_interpretation_quality, _check_temporal_consistency)
[Phase 14]  소스 정규화 + 생성 강제 (_normalize_source_for_generation, few-shot)
[Phase 14H] 타겟 블록 교체 (_enforce_interpretation_rewrite 재작성)
[Phase 14I] 헤징 억제 (_detect_interp_hedge_density, _extract_hedge_heavy_interp_blocks)
[Phase 15]  완료 연도 시제 교정 (_detect_completed_year_as_forecast, _enforce_tense_correction)
[Phase 15A] 복합 regex 추가 (_P15A_COMPOUND_RE_FORMAL/INFORMAL)
[Phase 15B] 연결어미 확장 (_P15B_COMPOUND_RE_CONNECTIVE)
[Phase 15C] Step3 시간 기준점 주입 + Post2 레이블 차단
[Phase 15D] 확정 어미 조건 [전망] 제거 (_strip_misapplied_jeonmang_tags)
[Phase 15E] 현재 연도 과거 월 동사+태그 통합 교정 (_enforce_current_year_month_settlement)
        ↓
[Phase 15F] ← 미구현 (다음 단계)
```

---

## 발행 이력 (이번 세션 실출력 검증 런)

| run_id | Post IDs | 테마 | 게이트 | 비고 |
|--------|----------|------|--------|------|
| 20260317_112105 | 143/144 | SK하이닉스 HBM + 양극재 | Phase 14I GO | 14I 검증 런 |
| 20260317_145007 | (15A 검증) | - | HOLD | 15A regex 검증 |
| 20260317_180244 | 158/159 | HBM4E + 양극재 수출 | PHASE15D_OUTPUT_HOLD | 15D 검증 런 |
| 20260317_190543 | 160/161 | HBM4E + 양극재 수출 | PHASE15E_OUTPUT_HOLD | 15E 검증 런 |

---

## 파일 변경 전체 목록 (이번 세션)

| 파일 | 주요 변경 | 관련 Phase |
|------|-----------|-----------|
| `generator.py` | Phase 10~15E 누적 약 +2,200 라인 | 10~15E |
| `main.py` | 슬롯 분기 + 게이트 블록 Phase 14→현행 | 10, 13, 14 |
| `scraper.py` | date_tier "unknown" 명시 (1줄) | 10 |
| `publish_history.json` | fingerprint 필드 추가 | 11 |
| `portfolio.json` | 누적 발행 이력 | 런마다 업데이트 |
| `docs/handoff_phase12.md` | Phase 12 상세 핸드오프 | 12 |
| `docs/handoff_phase13.md` | Phase 13 상세 핸드오프 | 13 |
| `docs/handoff_phase14.md` | Phase 14 상세 핸드오프 | 14 |
| `docs/handoff_phase15de.md` | Phase 15D-15E 핸드오프 | 15D-15E |
| `docs/handoff_phase10_to_15e.md` | 이 파일 (마스터 핸드오프) | 10~15E |
| `docs/REPORT_PHASE15*.md` | 각 Phase 구현/실출력 보고서 6종 | 15~15E |

---

## 잔존 이슈 및 다음 단계

### 즉시 처리 필요 (Phase 15F)

**문제:** `[전망]` + `{현재 연도}년 {과거 월}월` 조합이 동사 형태에 무관하게 잔존.
- "파악됩니다" — Phase 15D/15E 탐지 사각지대
- "증가한 것으로 추정됩니다" — Phase 15E 탐지는 되나 regex 미매치로 교정 실패

**Phase 15F 설계:**
```
조건: [전망] 직후 문장에 {run_year}년 {m}월 (m < run_month) 포함
예외: 순수 미래 동사 (할 것으로 전망됩니다 등) 존재 시 보류
위치: Phase 15E 이후 후처리
예상 코드량: 40~60라인
```

**프롬프트 파일 작성 위치:** `/Users/cjons/Documents/dev/macromalt/jobs/PROMPT_PHASE15F_*.md`

### 별도 트랙 (우선순위 낮음)

| 이슈 | 관련 Phase | 상태 |
|------|-----------|------|
| hedge_overuse Post1 FAIL 지속 (16/27 문장) | Phase 13/14I | 개선 중, 완전 해소 미완 |
| counterpoint_specificity FAIL | Phase 13 | 미완 |
| generic_wording WARN | Phase 12 | 허용 수준 |

---

## 인수자 체크리스트

- [ ] Phase 15F `PROMPT_PHASE15F_*.md` 작성
- [ ] `_strip_current_year_past_month_jeonmang()` 구현 (40~60라인)
- [ ] Post1/Post2 call site 연결
- [ ] 단위 테스트 (T1: 파악됩니다 케이스, T2: 증가한 것으로 추정됩니다, T3: 미래 동사 보존)
- [ ] 실출력 검증 후 GO/HOLD 판정
- [ ] hedge_overuse 별도 트랙 검토 (Phase 15F 완결 후)
