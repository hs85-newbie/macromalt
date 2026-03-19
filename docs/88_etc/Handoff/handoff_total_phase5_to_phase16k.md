# macromalt 통합 핸드오프 — Phase 5 ~ Phase 16K (Phase 16 계열 종료)

작성일: 2026-03-19
기준 커밋: `5faa571`
커버 범위: Phase 5 ~ Phase 16K
다음 단계: **Phase 17** — Post2 opener 섹션명 각도 강제 + Gemini JSON 파싱 견고성

> **이 문서는 Phase 16K 종료 기준 단일 참조 인수자 문서입니다.**
> 이전 통합 핸드오프(`handoff_consolidated_to_phase15e.md`)를 대체합니다.
> 다음 채팅에서 이 파일 하나만 읽으면 전체 맥락 복원 가능합니다.

---

## 1. 프로젝트 개요

**macromalt**: 한국 주식시장 투자 분석 콘텐츠 자동 생성·발행 파이프라인.

증권사 리서치 + 뉴스 + DART 공시를 수집하여 두 종류의 기사를 LLM으로 생성 후 WordPress에 자동 발행.

- **Post1**: `[심층분석]` — 매크로 경제 심층 분석 (거시 메커니즘 중심)
- **Post2**: `[캐시의 픽]` — 종목 리포트 (픽 바스켓 논리 중심)

### 3단계 파이프라인

```
Step 1  — Gemini 2.5 Flash (temp 0.2, 3,000 tok)
           뉴스 + 리서치 PDF + DART 공시 원문 → 구조화 JSON (테마 + 사실 데이터)

Step 2a — GPT-4o (temp 0.7, 5,000 tok)
           JSON → Post1 HTML 초고

Step 2b — GPT-4o (temp 0.65, 6,000 tok)
           JSON → Post2 HTML 초고

Step 3  — Gemini 2.5 Flash (temp 0.1 Verifier / 0.3 Reviser)
           HTML 초고 → 팩트체크 → 이슈 발견 시 수정본 채택 → WordPress 발행
```

### 주요 파일

| 파일 | 역할 |
|------|------|
| `generator.py` | LLM 호출, 프롬프트 상수, 후처리 전체 (Phase 10~16J 누적, ~+4,000라인) |
| `scraper.py` | 뉴스/리서치 수집, DART API, PDF 파싱, 한경컨센서스 세션 |
| `publisher.py` | WordPress REST API 발행 |
| `main.py` | 슬롯 분기, 게이트 판정, 파이프라인 오케스트레이션 |
| `publish_history.json` | Fingerprint 기반 발행 이력 (최근 5건) |
| `portfolio.json` | 누적 발행 기록 (170건+) |

### 파일/디렉토리 구조

| 항목 | 경로 |
|------|------|
| 실출력 검증 보고서 | `docs/88_etc/REPORT/` |
| 핸드오프 문서 | `docs/88_etc/Handoff/` |
| 프롬프트/작업 지시 | `jobs/` |
| 정책 문서 | `docs/10_policies/MACROMALT_PHASE_EXECUTION_POLICY.md` |

---

## 2. Phase 진행 일람 (전체)

| Phase | 커밋 | 날짜 | 핵심 목적 | 판정 |
|-------|------|------|-----------|------|
| 5-A~D | `d7994ef` | 03-13 | DART 연동, PDF enrich, WP 자동 발행 | GO |
| 6 | `c526d46` | 03-13 | 한경 세션, 사업보고서 파싱, DART XML 수정 | GO |
| 7~9 | `fe36a27` | 03-13 | 실 발행 검증 3회, 투자 권유 억제 | GO |
| 10 | `5409bd9` | 03-16 | 슬롯 분기 + 이력 반복 완화 | GO |
| 11 | `077f647` | 03-16 | Fingerprint 기반 반복 완화 엔진 | GO |
| 12 | `25a7cfc` | 03-16 | 증거 밀도 & 글쓰기 품질 강화 | GO |
| 13 | `9416537` | 03-16 | 해석 지성 + 시간/수치 신뢰성 | HOLD→GO |
| 14/14H/14I | `da817d5` | 03-17 | 생성 강제 + 타겟 블록 교체 + 헤징 억제 | GO |
| 15A/15B | `39548b1`/`d97f0b2` | 03-17 | 완료 연도 시제 교정 | GO |
| 15C | `798d3a6` | 03-17 | Step3 시간 기준점 주입 + Post2 레이블 차단 | GO |
| 15D | `b3f1f89` | 03-17 | `[전망]` 오주입 태그 후처리 제거 | GO |
| 15E | `0645e9d` | 03-17 | 현재 연도 과거 월 통합 교정 | GO |
| **16** | `81ba0ea` | 03-17 | Temporal SSOT 레이어 구축 | GO |
| **16A** | `536744d` | 03-17 | 실출력 검증 1차 — SSOT 효과 확인 | GO |
| **16B** | `f4f0e6a` | 03-18 | emergency_polish / intro_overlap / generic 진단 | GO |
| **16C** | `3ede40e` | 03-18 | 실출력 검증 2차 — Post2 각도 분리 미달 | HOLD |
| **16D** | `cfb8240` | 03-18 | Post2 macro 재서술 억제 + 픽 브릿지 강제 | GO |
| **16E** | `93bef0b` | 03-18 | 실출력 검증 3차 — bridge mismatch 발견 | CONDITIONAL GO |
| **16F** | `6c1bde8` | 03-18 | bridge-pick 정합성 강화 + step3_status 표준화 | GO |
| **16G** | `bb44fa0` | 03-18 | 실출력 검증 4차 — intro_overlap HIGH→LOW | GO |
| **16H** | `f957e42` | 03-18 | hedge 절제 + closure false fail 완화 + polish 집계 단일화 | GO |
| **16I** | `83b2c5e` | 03-19 | 실출력 검증 5차 — Track A/B/C 효과 확인 | CONDITIONAL GO |
| **16J** | `a20cfca` | 03-19 | PARSE_FAILED 표준화 + Theme Rotation 규칙 보강 | GO |
| **16K** | `5faa571` | 03-19 | 실출력 검증 최종 — Phase 16 계열 종료 판정 | **CONDITIONAL GO** |

**→ Phase 16 계열 종료. 다음: Phase 17**

---

## 3. generator.py 현재 레이어 구조

```
[Phase 10]   슬롯 분기 + fingerprint
             _SLOT_ANALYST_CONTEXTS, _build_history_context()
             detect_slot() → morning/evening/us_open/default

[Phase 11]   Fingerprint 반복 완화 엔진
             _make_theme_fingerprint() — macro 10종 keyword 매핑
             _make_axes_fingerprint()  — sub_axes 11종
             _make_ticker_buckets()    — 섹터 버킷 8종

[Phase 16J]  theme repeat 진단 (Phase 11 재사용, line ~224)
             _p16j_check_theme_repeat(current_theme) → {is_repeat, repeat_count, theme_fp, matched_slots}

[Phase 12]   증거 밀도 & 품질 강화
             _build_numeric_highlight_block() — 핵심 수치 Gemini 입력 앞 주입
             _score_post_quality()            — 5개 지표 rule-based 진단

[Phase 13]   해석 지성 + 시간/수치 신뢰성
             _score_interpretation_quality()  — weak_interp / hedge_overuse / counterpoint_spec
             _check_temporal_consistency()
             _check_numeric_sanity()

[Phase 14]   소스 정규화 + 생성 강제
             _normalize_source_for_generation() — CONFIRMED/FORECAST/AMBIGUOUS
             _P14_FEWSHOT_BAD_GOOD_INTERP       — BAD→GOOD 5쌍

[Phase 14H]  타겟 블록 교체
             _enforce_interpretation_rewrite()  — [해석] 블록 단위 교체

[Phase 14I]  헤징 억제
             _P14I_INTERP_HEDGE_ENDINGS         — 헤징 어미 10개
             _detect_interp_hedge_density()

[Phase 15A]  완료 연도 복합 regex
             _P15A_COMPOUND_RE_FORMAL/INFORMAL

[Phase 15B]  연결어미 확장
             _P15B_COMPOUND_RE_CONNECTIVE

[Phase 15C]  Step3 시간 기준점 주입 + Post2 레이블 차단  (~line 2300)
             _P15C_STEP3_TEMPORAL_GROUNDING (→ Phase 16에서 동적 블록으로 교체)
             _P15C_POST2_LABEL_BAN

[Phase 15D]  확정 어미 조건 [전망] 제거  (~line 2371)
             _strip_misapplied_jeonmang_tags()
             _P15D_CONFIRMED_VERB_MARKERS — 확정 어미 19종

[Phase 15E]  현재 연도 과거 월 통합 교정  (~line 2467)
             _detect_current_year_past_month_as_forecast()
             _enforce_current_year_month_settlement()

[Phase 15F]  동사형 독립 [전망] 제거
             _strip_current_year_past_month_jeonmang(content, ssot, label)
             _P16_PURE_FUTURE_VERBS — 순수 미래 동사 예외 목록

[Phase 16]   Temporal SSOT 레이어
             _build_temporal_ssot(run_year, run_month) → SSOT dict
             _build_p16_generation_block(ssot)         → GPT context_text 주입 블록
             _build_p16_step3_block(ssot)              → Step3 시스템 프롬프트 블록
             GEMINI_VERIFIER_SYSTEM / GEMINI_REVISER_SYSTEM에 동적 주입

[Phase 16B]  출력 품질 진단 guard
             _p16b_emergency_polish()                  — generic 마커 진단
             _p16b_calc_intro_overlap()                — 4-gram overlap 계산
             p16b_guard dict                           — Post1/Post2 per-run 진단 딕셔너리

[Phase 16D]  Post2 macro 재서술 억제 + 픽 브릿지 강제
             _P16D_POST2_CONTINUITY_HARDENING          — Post2 매크로 재서술 금지
             _P16D_POST2_BRIDGE_REQUIREMENT            — 브릿지 구문 강제

[Phase 16F]  bridge-pick 정합성 + step3_status 표준화
             _p16f_check_bridge_alignment()            — bridge_diag 생성
             step3_status enum: PASS/REVISED/FAILED_NO_REVISION

[Phase 16H]  운영 안정화
             hedge 절제 프롬프트 보강
             verifier_revision_closure false fail 완화
             emergency_polish 집계 "N종 M건" 단일화

[Phase 16J]  PARSE_FAILED 표준화 + opener 다양화  (~line 3210, 5220, 5324, 5736)
             _P16J_POST2_SAME_THEME_OPENER             — 동일 theme opener 강제 상수
             verify_draft() log 강화                  — [Phase 16J] 태그 + 4-state enum 주석
             gpt_write_picks() same_theme_hint 파라미터 추가
```

---

## 4. p16b_guard 현재 구조 (Phase 16K 기준)

```python
# Post1 p16b_guard
{
    "step3_status":         str,    # PASS / REVISED / FAILED_NO_REVISION / PARSE_FAILED
    "fallback_triggered":   bool,   # step3_status == "FAILED_NO_REVISION"
    "parse_failed":         bool,   # step3_status == "PARSE_FAILED"  [Phase 16J]
    "emergency_polish":     dict,   # {status, unique_marker_count, total_occurrence_count, markers}
    "intro_overlap":        None,   # Post1에는 해당 없음
}

# Post2 p16b_guard
{
    "step3_status":         str,
    "fallback_triggered":   bool,
    "parse_failed":         bool,   # [Phase 16J]
    "emergency_polish":     dict,   # "N종 M건" 형식 [Phase 16H]
    "intro_overlap":        dict,   # {overlap_ratio, status, shared_ngram_count}
    "bridge_diag":          dict,   # {found, mode, picks}  [Phase 16F]
    "theme_repeat_diag":    dict,   # {is_repeat, repeat_count, theme_fp, matched_slots}  [Phase 16J]
}
```

### step3_status 4-state enum (Phase 16J 표준)

| 상태 | 발생 조건 | 수정 시도 | 발행 경로 |
|------|----------|----------|----------|
| `PASS` | Step3 이슈 없음 | 없음 | GPT 초안 원본 |
| `REVISED` | Step3 이슈 발견 → 수정 성공 | 있음 (성공) | Gemini 수정본 |
| `FAILED_NO_REVISION` | 수정 API 실패 (503/timeout) | 있음 (실패) | GPT 초안 원본 |
| `PARSE_FAILED` | Gemini 응답 JSON 파싱 불가 | **없음** | GPT 초안 원본 |

---

## 5. 주요 상수 위치 요약 (generator.py)

| 상수/함수 | 위치(근사) | 역할 |
|-----------|-----------|------|
| `_p16j_check_theme_repeat()` | ~line 224 | theme repeat 진단 |
| `_P16B_POST2_ANGLE_DIVERSIFICATION` | ~line 3200 | Post2 각도 다양화 (기본) |
| `_P16J_POST2_SAME_THEME_OPENER` | ~line 3210 | 동일 theme Post2 opener 강제 (조건부) |
| `_p16b_emergency_polish()` | ~line 3230 | generic 마커 진단 |
| `_P16D_POST2_CONTINUITY_HARDENING` | ~line 3180 | Post2 매크로 재서술 금지 |
| `_P16D_POST2_BRIDGE_REQUIREMENT` | ~line 3190 | 브릿지 강제 |
| `gpt_write_picks()` | ~line 5220 | Post2 생성 (same_theme_hint 파라미터) |
| `verify_draft()` | ~line 5324 | Step3 팩트체크 + PARSE_FAILED 처리 |
| `generate_stock_picks_report()` | ~line 5736 | Post2 파이프라인 오케스트레이션 |
| Post1 `p16b_guard` | ~line 5598 | Post1 진단 dict |
| Post2 `p16b_guard` | ~line 5878 | Post2 진단 dict |

---

## 6. 품질 게이트 (Phase 16K 기준 현황)

### 정량 지표

| 지표 | 기준 | 현재 상태 |
|------|------|----------|
| `intro_overlap` | MEDIUM 이하 (≤30%) | ✅ 12.4% LOW |
| `post1_post2_continuity` | PASS (n-gram 중복 0) | ✅ PASS (0개) |
| `step3_status` | PASS/REVISED 정상 | ✅ REVISED |
| `bridge_diag.found` | True | ✅ found=True, mode=COMMON |
| `emergency_polish` | WARN 허용 (관찰 모드) | ✅ 1종~2종 WARN |
| `hedge_overuse_p1` | PASS 목표 | ⚠ WARN 50% (관찰 중) |
| `verifier_revision_closure` | PASS | ⚠ WARN (1 unresolved) |
| `counterpoint_specificity_p2` | PASS | ⚠ FAIL (지속적 이슈) |

### 비회귀 SSOT

| 항목 | 상태 |
|------|------|
| temporal SSOT (Phase 15D/15E/15F) | ✅ 비회귀 |
| `[전망]` 태그 오주입 | ✅ 없음 |
| 완료 연도 시제 위반 | ✅ 없음 |
| `step3_status` 표준 enum | ✅ 4개 상태 유지 |
| `publish_history.json` fingerprint | ✅ 정상 기록 |

---

## 7. intro_overlap 계산 방식

```
기준: Post1 intro 300자 / Post2 intro 600자
방식: char-level 4-gram overlap
공식: shared_ngrams / max(ng1_count, ng2_count)
구간: LOW < 15% / MEDIUM 15~30% / HIGH ≥ 30%
실패 기준 (post1_post2_continuity): n-gram ≥ 3 OR bg_repeat ≥ 2
```

---

## 8. Phase 16 계열 핵심 성과 요약

| Phase | 핵심 성과 |
|-------|----------|
| 16 | Temporal SSOT 레이어 — 시제 상태 단일 진실 공급원 |
| 16A | SSOT 실출력 검증 GO |
| 16B | emergency_polish / intro_overlap / generic 진단 체계 구축 |
| 16C | 실출력 검증 2차 — Post2 각도 분리 미달 확인 (HOLD) |
| 16D | Post2 macro 재서술 억제 + 픽 브릿지 강제 |
| 16E | 실출력 검증 3차 — bridge mismatch 발견 (CONDITIONAL GO) |
| 16F | bridge-pick 정합성 guard + step3_status 4-state enum |
| 16G | 실출력 검증 4차 — intro_overlap HIGH→LOW/MEDIUM (GO) |
| 16H | hedge 절제 + closure false fail 완화 + polish 집계 단일화 |
| 16I | 실출력 검증 5차 — Track A/B/C 효과 확인 (CONDITIONAL GO) |
| 16J | PARSE_FAILED 4번째 표준 상태 + theme repeat 진단 + opener 다양화 |
| 16K | 최종 실출력 검증 — **CONDITIONAL GO → Phase 16 계열 종료** |

---

## 9. Phase 17 우선순위 (다음 채팅에서 착수)

### 필수 (CONDITIONAL GO 잔여 이슈)

#### 1) Post2 opener 섹션명 + 첫 문장 픽 각도 강제 전환

**문제**: Phase 16K 실출력에서 `_P16J_POST2_SAME_THEME_OPENER` 주입 후에도
Post2 첫 H2 섹션명이 "오늘 이 테마를 보는 이유"로 생성됨.
첫 문장이 "중동 지정학적 리스크가 고조되고 있습니다"로 거시 재서술 시작.

**목표**: 섹션명부터 픽 바스켓 논리 각도로 시작하도록 강제.
예시: "S-Oil과 XLE를 선택한 이유" / "정유주 바스켓의 공통 민감도" 등.

**접근 방법 후보**:
- A: `_P16J_POST2_SAME_THEME_OPENER`에 H2 섹션명 예시 명시
- B: Post2 생성 후처리에서 첫 H2 패턴 regex 감지 → 경고 또는 교정
- C: gpt_write_picks() system 프롬프트에 섹션명 금지 패턴 추가

#### 2) PARSE_FAILED 런타임 검증

**문제**: Phase 16K 실출력에서 PARSE_FAILED가 발생하지 않아 런타임 로그 검증 미실시.

**목표**:
- 다음 PARSE_FAILED 발생 시 → 로그/보고서/handoff 3-way 일치 확인
- 필요시 `parse_result = None` 강제 케이스로 인위적 테스트

### 관찰 대상 (Phase 17 중 모니터링)

| 항목 | 현재 | 목표 |
|------|------|------|
| `hedge_overuse_p1` | WARN 50% | PASS (<30%) |
| `verifier_revision_closure` | WARN 1건 | PASS |
| `counterpoint_specificity_p2` | FAIL | PASS |

### 확장 검토 (Phase 17 또는 후속)

5. **Gemini JSON 파싱 견고성**: PARSE_FAILED 근본 원인 제거 (응답 포맷 정규화 또는 retry)
6. **슬롯 theme rotation 강화**: Phase 11 STRONG 감지 범위 확대 (현재 D1 기준)
7. **스타일 분리 트랙**: `tokens.py`, `templates/` — `docs/20_tracks/wordpress_style/` 설계 완료

---

## 10. 최근 발행 이력 (Phase 16 계열)

| run_id | Post IDs | 게이트 | 비고 |
|--------|----------|--------|------|
| 20260319_151133 | 174/175 | GO | Phase 16K 검증 대상 run |
| (이전 runs) | 143~173 | 다수 GO | Phase 16A~16I 검증 포함 |

**현재 portfolio.json 누적**: 170건+

---

## 11. 운영 표준 (불변 규칙)

### 프롬프트 파일

- 각 Phase 착수 전 `jobs/PROMPT_PHASE{N}_*.md` 작성
- 실출력 검증은 `jobs/PROMPT_PHASE{N}K_*.md` (K = 검증 Phase)

### 문서 제출 형식

1. **채팅 요약** — 핵심 판정 + 수치
2. **상세 보고서** — `docs/88_etc/REPORT/REPORT_PHASE{N}_*.md`
3. **핸드오프** — `docs/88_etc/Handoff/handoff_phase{n}.md`

### git 커밋 규칙

- 구현 완료마다 커밋 (Phase 단위)
- 메시지 형식: `Phase {N}: {핵심 변경 1줄 요약}`
- 실출력 검증 보고서 + 핸드오프는 한 커밋에 포함

### 게이트 판정

- **GO**: 즉시 다음 Phase 진행
- **CONDITIONAL GO**: 1~2개 마이너 이슈 → 후속 Phase에서 해소
- **HOLD**: 핵심 지표 미달 → 즉시 수정 후 재검증

---

## 12. 인수자 체크리스트 (Phase 17 착수 전)

- [ ] 이 문서를 기반으로 전체 맥락 파악
- [ ] `generator.py` Phase 16J 섹션 (~line 224, ~3210, ~5220, ~5324, ~5736) 확인
- [ ] `publish_history.json` 최신 이력 확인 (theme_fp 연속 여부)
- [ ] Phase 17 Track 1: Post2 opener H2 섹션명 픽 각도 강제 설계
- [ ] Phase 17 Track 2: PARSE_FAILED 런타임 검증 (발생 시 또는 인위적 테스트)
- [ ] 실행 후 → REPORT + handoff 작성 → 커밋
