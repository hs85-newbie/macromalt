# macromalt 통합 핸드오프 — Phase 5 ~ Phase 17 (Phase 17 종료)

작성일: 2026-03-20
기준 커밋: `3d3b317`
커버 범위: Phase 5 ~ Phase 17
다음 단계: **Phase 18** — verifier_revision_closure 안정화 + fallback 경로 정책 정교화

> **이 문서는 Phase 17 종료 기준 단일 참조 인수자 문서입니다.**
> 이전 통합 핸드오프(`handoff_total_phase5_to_phase16k.md`)를 대체합니다.
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
| `generator.py` | LLM 호출, 프롬프트 상수, 후처리 전체 (~6,563라인, Phase 17 포함) |
| `scraper.py` | 뉴스/리서치 수집, DART API, PDF 파싱, 한경컨센서스 세션 |
| `publisher.py` | WordPress REST API 발행 |
| `main.py` | 슬롯 분기, 게이트 판정, 파이프라인 오케스트레이션 |
| `publish_history.json` | Fingerprint 기반 발행 이력 (최근 5건) |
| `portfolio.json` | 누적 발행 기록 (180건+) |
| `styles/tokens.py` | WordPress 스타일 토큰 중앙 관리 (Pre-Phase 17 스타일 분리) |
| `styles/wordpress/` | base.css / typography.css / components.css |
| `theme/child-theme/style.css` | WP child theme 스타일 |

### 파일/디렉토리 구조

| 항목 | 경로 |
|------|------|
| 실출력 검증 보고서 | `docs/88_etc/REPORT/` |
| 핸드오프 문서 | `docs/88_etc/Handoff/` |
| 프롬프트/작업 지시 | `jobs/` |
| 정책 문서 | `docs/10_policies/MACROMALT_PHASE_EXECUTION_POLICY.md` |
| 스타일 토큰 | `styles/tokens.py`, `styles/wordpress/` |

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
| **16K** | `5faa571` | 03-19 | 실출력 검증 최종 — Phase 16 계열 종료 판정 | CONDITIONAL GO |
| **Pre-17** | `09da629` | 03-19 | WordPress 스타일 분리 트랙 (tokens.py, CSS 분리) | GO |
| **17** | `9702458` | 03-19 | Post2 opener pick-angle 강제 + PARSE_FAILED 런타임 분류 | **핵심 범위 기준 GO** |
| **17 보고서** | `3d3b317` | 03-20 | Phase 17 보고서 문구 보정 + Phase 17 공식 클로즈 | — |

**→ Phase 17 공식 종료. 다음: Phase 18**

---

## 3. generator.py 현재 레이어 구조 (~6,563라인)

```
[Phase 10]   슬롯 분기 + fingerprint
             _SLOT_ANALYST_CONTEXTS, _build_history_context()
             detect_slot() → morning/evening/us_open/default

[Phase 11]   Fingerprint 반복 완화 엔진
             _make_theme_fingerprint() — macro 10종 keyword 매핑
             _make_axes_fingerprint()  — sub_axes 11종
             _make_ticker_buckets()    — 섹터 버킷 8종

[Phase 16J]  theme repeat 진단 (Phase 11 재사용, ~line 224)
             _p16j_check_theme_repeat(current_theme) → {is_repeat, repeat_count, theme_fp, matched_slots}

[Phase 12]   증거 밀도 & 품질 강화
             _build_numeric_highlight_block() — 핵심 수치 Gemini 입력 앞 주입
             _score_post_quality()            — 5개 지표 rule-based 진단

[Phase 13]   해석 지성 + 시간/수치 신뢰성
             _score_interpretation_quality()  — weak_interp / hedge_overuse / counterpoint_spec
             _check_temporal_consistency()
             _check_numeric_sanity()
             _P13_POST2_CONTINUITY_RULE (~line 937) — ⚠ Phase 17 개편 반영됨

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

[Phase 15C]  Step3 시간 기준점 주입 + Post2 레이블 차단 (~line 2300)
             _P15C_STEP3_TEMPORAL_GROUNDING (→ Phase 16에서 동적 블록으로 교체)
             _P15C_POST2_LABEL_BAN

[Phase 15D]  확정 어미 조건 [전망] 제거 (~line 2371)
             _strip_misapplied_jeonmang_tags()
             _P15D_CONFIRMED_VERB_MARKERS — 확정 어미 19종

[Phase 15E]  현재 연도 과거 월 통합 교정 (~line 2467)
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
             step3_status enum: PASS/REVISED/FAILED_NO_REVISION/PARSE_FAILED

[Phase 16H]  운영 안정화
             hedge 절제 프롬프트 보강
             verifier_revision_closure false fail 완화
             emergency_polish 집계 "N종 M건" 단일화

[Phase 16J]  PARSE_FAILED 표준화 + opener 다양화 (~line 3210, 5220, 5324, 5736)
             _P16J_POST2_SAME_THEME_OPENER             — 동일 theme opener 강제 상수
             verify_draft() log 강화                  — [Phase 16J] 태그 + 4-state enum 주석
             gpt_write_picks() same_theme_hint 파라미터 추가

[Phase 17A]  Post2 opener pick-angle 강제 (~line 3217~3290)
             _P17_POST2_OPENER_ENFORCEMENT             — opener 강제 상수 (★★ 최우선 주입)
               ├─ H3 금지 패턴 6종 (generic theme explainer)
               ├─ H3 허용 패턴 5종 (pick-angle)
               ├─ 첫 문장 강제 규칙 (픽명 포함 / macro recap 금지 / 핵심 변수 1개+)
               └─ gpt_write_picks() user_msg 최우선(첫 번째) 위치 주입 (~line 5316)
             _P13_POST2_CONTINUITY_RULE (~line 937/943/945)
               └─ "오늘 이 테마를 보는 이유" → Phase 17 개편 반영 + ⚠ 금지 명시
             GEMINI_VERIFIER_SYSTEM (~line 4888/4935)
               └─ opener 점검 항목 20~25번 추가
             GEMINI_REVISER_SYSTEM (~line 4969/5020)
               └─ opener 보정 규칙 항목 9 추가

[Phase 17B]  PARSE_FAILED 런타임 분류 체계 (~line 5347~5460)
             _classify_parse_failed(raw, normalized) → TYPE_A~TYPE_E / TYPE_UNKNOWN
               ├─ TYPE_A: H2/H3 태그 전무
               ├─ TYPE_B: 금지 opener 패턴 포함 (6종)
               ├─ TYPE_C: 오픈/클로즈 태그 수 차이 >5
               ├─ TYPE_D: PICKS 주석 누락 (>500자)
               ├─ TYPE_E: normalized < raw 60%
               └─ TYPE_UNKNOWN: 위 분류 외
             _log_parse_failed_event(run_id, slot, post_type, ...) (~line 5382)
               └─ 10필드 구조화 로그: run_id/slot/post_type/failure_type/parse_stage/
                  failed_section_name/raw_output_snapshot/normalized_output_snapshot/
                  fallback_used/publish_blocked
             verify_draft() PARSE_FAILED 처리 강화 (~line 5456)
               └─ logger.warning 단독 → _log_parse_failed_event() 호출로 교체
```

---

## 4. p16b_guard 현재 구조 (Phase 17 기준)

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

### step3_status 4-state enum (Phase 16J 표준, Phase 17 유지)

| 상태 | 발생 조건 | 수정 시도 | 발행 경로 |
|------|----------|----------|----------|
| `PASS` | Step3 이슈 없음 | 없음 | GPT 초안 원본 |
| `REVISED` | Step3 이슈 발견 → 수정 성공 | 있음 (성공) | Gemini 수정본 |
| `FAILED_NO_REVISION` | 수정 API 실패 (503/timeout) | 있음 (실패) | GPT 초안 원본 |
| `PARSE_FAILED` | Gemini 응답 JSON 파싱 불가 | **없음** | GPT 초안 원본 (fallback) |

---

## 5. 주요 상수/함수 위치 요약 (generator.py, Phase 17 기준)

| 상수/함수 | 위치(근사) | 역할 |
|-----------|-----------|------|
| `_p16j_check_theme_repeat()` | ~line 224 | theme repeat 진단 |
| `_P13_POST2_CONTINUITY_RULE` | ~line 937 | Post2 continuity 규칙 (Phase 17 개편 반영) |
| `_P16B_POST2_ANGLE_DIVERSIFICATION` | ~line 3200 | Post2 각도 다양화 (기본) |
| `_P16J_POST2_SAME_THEME_OPENER` | ~line 3210 | 동일 theme Post2 opener 강제 (조건부) |
| **`_P17_POST2_OPENER_ENFORCEMENT`** | **~line 3220** | **★★ Post2 opener pick-angle 강제 (Phase 17 신규)** |
| `_p16b_emergency_polish()` | ~line 3230 | generic 마커 진단 |
| `_P16D_POST2_CONTINUITY_HARDENING` | ~line 3180 | Post2 매크로 재서술 금지 |
| `_P16D_POST2_BRIDGE_REQUIREMENT` | ~line 3190 | 브릿지 강제 |
| `GEMINI_VERIFIER_SYSTEM` | ~line 4888 | verifier 시스템 프롬프트 (20~25번 항목 추가) |
| `GEMINI_REVISER_SYSTEM` | ~line 4969 | reviser 시스템 프롬프트 (항목 9 추가) |
| `gpt_write_picks()` | ~line 5220 | Post2 생성 (_P17_POST2_OPENER_ENFORCEMENT 최우선 주입) |
| **`_classify_parse_failed()`** | **~line 5355** | **★ PARSE_FAILED TYPE_A~E 분류 (Phase 17 신규)** |
| **`_log_parse_failed_event()`** | **~line 5382** | **★ 10필드 구조화 로그 (Phase 17 신규)** |
| `verify_draft()` | ~line 5324 | Step3 팩트체크 + PARSE_FAILED 처리 강화 |
| `generate_stock_picks_report()` | ~line 5736 | Post2 파이프라인 오케스트레이션 |
| Post1 `p16b_guard` | ~line 5598 | Post1 진단 dict |
| Post2 `p16b_guard` | ~line 5878 | Post2 진단 dict |

---

## 6. 품질 게이트 현황 (Phase 17 종료 기준)

### opener 구조 지표 (Phase 17 신규)

| 지표 | 목표 | Phase 17 결과 |
|------|------|--------------|
| "오늘 이 테마를 보는 이유" 패턴 | 0건 | **0건 ✅** |
| generic opener H3 | 0건 | **0건 ✅** |
| opener 첫 문장 macro recap 시작 | 0건 | **0건 ✅** |
| opener 첫 문장 픽명/섹터명 포함 | 100% | **5/5 ✅** |
| opener 첫 문장 핵심 변수 포함 | 100% | **5/5 ✅** |

### PARSE_FAILED 지표 (Phase 17 신규)

| 지표 | 결과 |
|------|------|
| TYPE_A~E 분류 체계 | ✅ 구현 완료 |
| 10필드 구조화 로그 | ✅ 구현 완료 |
| 실전 발생 및 분류 확인 | ✅ Post 187 TYPE_D 실제 작동 |
| fallback_used=True / publish_blocked=False | ✅ 정상 동작 |

### 기존 정량 지표 (Phase 16K→17 유지)

| 지표 | 기준 | 현재 상태 |
|------|------|----------|
| `intro_overlap` | MEDIUM 이하 (≤30%) | ✅ LOW 수준 유지 |
| `step3_status` | PASS/REVISED 정상 | ✅ REVISED (5건 중 4건) / PARSE_FAILED (1건, TYPE_D) |
| `bridge_diag.found` | True | ✅ found=True |
| `emergency_polish` | WARN 허용 (관찰 모드) | ✅ PASS |
| `verifier_revision_closure` | PASS 목표 | ⚠ FAIL/WARN 잔존 (Phase 18 이관) |
| `counterpoint_specificity_p2` | PASS | ⚠ FAIL 지속 (Phase 18 이관) |

### 비회귀 SSOT

| 항목 | 상태 |
|------|------|
| temporal SSOT (Phase 15D/15E/15F) | ✅ 비회귀 |
| `[전망]` 태그 오주입 | ✅ 없음 |
| 완료 연도 시제 위반 | ✅ 없음 |
| `step3_status` 표준 enum | ✅ 4개 상태 유지 |
| "오늘 이 테마를 보는 이유" 재등장 | ✅ 0건 |

---

## 7. intro_overlap 계산 방식 (Phase 16 이후 불변)

```
기준: Post1 intro 300자 / Post2 intro 600자
방식: char-level 4-gram overlap
공식: shared_ngrams / max(ng1_count, ng2_count)
구간: LOW < 15% / MEDIUM 15~30% / HIGH ≥ 30%
실패 기준 (post1_post2_continuity): n-gram ≥ 3 OR bg_repeat ≥ 2
```

---

## 8. Phase 17 핵심 성과 요약

| 트랙 | 내용 | 결과 |
|------|------|------|
| Track A: opener 구조 개편 | generic H3 → pick-angle H3 강제. `_P17_POST2_OPENER_ENFORCEMENT` 신규 상수, verifier 20~25번, reviser 항목 9 | ✅ 5/5 PASS |
| Track B: PARSE_FAILED 런타임 | `_classify_parse_failed()` + `_log_parse_failed_event()` 신규 구현. Post 187에서 TYPE_D 실전 확인 | ✅ 실전 동작 확인 |
| Pre-17: 스타일 분리 | `styles/tokens.py`, `styles/wordpress/` CSS 3종, `theme/child-theme/style.css` | ✅ 분리 완료 |

### Phase 17 샘플 발행 결과 (5건)

| # | Post ID | 발행 시각 | opener H3 | step3_status | PARSE_FAILED |
|---|---------|-----------|-----------|--------------|--------------|
| 1 | 177 | 17:36:21 | 왜 지금 삼성전자인가 | REVISED | — |
| 2 | 179 | 18:01:38 | 왜 지금 Energy Select Sector SPDR Fund인가 | REVISED | — |
| 3 | 183 | 18:03:55 | 왜 지금 SK이노베이션인가 | REVISED | — |
| 4 | 185 | 18:06:19 | 왜 지금 S-Oil인가 | REVISED | — |
| 5 | 187 | 18:09:15 | 왜 지금 S-Oil인가 | **PARSE_FAILED** | TYPE_D (fallback 발행) |

---

## 9. Phase 17 잔여 이슈 (Phase 18 이관)

### 잔여 이슈 목록

| 이슈 | 내용 | 우선순위 |
|------|------|---------|
| verifier_revision_closure FAIL/WARN | 5건 중 FAIL 2건 / WARN 2건 잔존. 완전 안정화 미달 | 높음 |
| PARSE_FAILED TYPE_D 재발 가능성 | Post 187에서 PICKS 주석 누락으로 fallback 경로 사용 | 높음 |
| fallback 경로 정책 미정교화 | fallback_used=True 케이스별 대응 규칙 없음 | 중간 |
| PARSE_FAILED TYPE 다양화 | 현재 TYPE_D만 실전 확인. 타 유형 발생 시 대응 검증 필요 | 중간 |
| counterpoint_specificity_p2 FAIL | Phase 16 이후 지속. Phase 17에서도 미해소 | 낮음 |

---

## 10. Phase 18 착수 내용

### 필수 (Phase 17 잔여 이슈 해소)

#### 1) verifier_revision_closure FAIL/WARN 잔존 원인 분리

**문제**: 5건 중 FAIL 2건(Post 177, 185) / WARN 2건(Post 183, 187) 잔존.
verifier가 이슈를 발견하고 reviser가 수정했음에도 closure가 FAIL/WARN으로 남는 원인 분석 필요.

**접근 방법 후보**:
- A: closure 판정 로직 완화 기준 재검토 (false fail 가능성)
- B: reviser 수정 프롬프트 강화 (미해소 이슈 유형별 보정 규칙 추가)
- C: closure FAIL이지만 발행본 품질 실제 무관한 케이스 분리 → 정책 문서화

#### 2) fallback 발행 경로 정책 정교화

**문제**: PARSE_FAILED 시 GPT 초안 원본 발행. 현재는 publish_blocked=False 일괄 정책.
TYPE별로 발행 차단 여부를 다르게 적용할 필요 있음.

**접근 방법 후보**:
- TYPE_A (구조 전무): 발행 차단 검토
- TYPE_B (금지 패턴): 발행 차단 검토
- TYPE_C (HTML 파손): 발행 차단 검토
- TYPE_D (PICKS 주석 누락): 발행 허용 유지
- TYPE_E (reviser 과도 축소): 발행 허용 유지

#### 3) PARSE_FAILED 원인별 후속 대응 규칙 보강

**문제**: 분류/로그는 완성됐으나, 유형별 자동 대응 규칙 없음.

#### 4) opener 성공 상태 반복 실행 안정성 검증

**문제**: Phase 17 샘플 5건에서는 opener 구조 전환 5/5 달성.
추가 실행에서도 안정 유지되는지 검증 필요.

### 관찰 대상 (Phase 18 중 모니터링)

| 항목 | 현재 | 목표 |
|------|------|------|
| `verifier_revision_closure` | FAIL/WARN 잔존 | PASS 안정화 |
| PARSE_FAILED TYPE 분포 | TYPE_D만 확인 | 다양화 시 대응 검증 |
| opener pick-angle 유지율 | 5/5 (100%) | 추가 실행에서도 100% 유지 |
| `counterpoint_specificity_p2` | FAIL | PASS 목표 (장기) |

---

## 11. 최근 발행 이력

| Post ID | 슬롯 | 발행 시각 | step3_status | 비고 |
|---------|------|-----------|--------------|------|
| 177 | morning | 2026-03-19 17:36 | REVISED | Phase 17 샘플 1 |
| 179 | evening | 2026-03-19 18:01 | REVISED | Phase 17 샘플 2 |
| 183 | morning | 2026-03-19 18:03 | REVISED | Phase 17 샘플 3 |
| 185 | us_premarket | 2026-03-19 18:06 | REVISED | Phase 17 샘플 4 |
| 187 | default | 2026-03-19 18:09 | PARSE_FAILED (TYPE_D) | Phase 17 샘플 5, fallback 발행 |

**현재 portfolio.json 누적**: 180건+

---

## 12. 운영 표준 (불변 규칙)

### 프롬프트 파일

- 각 Phase 착수 전 `jobs/PROMPT_PHASE{N}_*.md` 또는 `MACROMALT_PHASE{N}_DEV_AGENT_FINAL.md` 작성
- 실출력 검증은 별도 검증 Phase로 분리

### 문서 제출 형식

1. **채팅 요약** — 핵심 판정 + 수치
2. **상세 보고서** — `docs/88_etc/REPORT/REPORT_PHASE{N}_*.md`
   - 보고서 기준: `PHASE17_REPORT_FULL_BODY_REQUIREMENT.md` (발행 본문 전문 포함 필수)
   - 문구 기준: `PHASE17_REPORT_WORDING_REPLACEMENT.md` (범위형 GO, 예외 명시)
3. **핸드오프** — `docs/88_etc/Handoff/handoff_total_phase5_to_phase{n}.md`

### git 커밋 규칙

- 구현 완료마다 커밋 (Phase 단위)
- 메시지 형식: `Phase {N}: {핵심 변경 1줄 요약}`
- 실출력 검증 보고서 + 핸드오프는 한 커밋에 포함

### 게이트 판정

- **GO**: 즉시 다음 Phase 진행
- **핵심 범위 기준 GO**: 주요 목표 달성, 일부 잔여 이슈 → 다음 Phase 이관 (Phase 17 기준)
- **CONDITIONAL GO**: 1~2개 마이너 이슈 → 후속 Phase에서 해소
- **HOLD**: 핵심 지표 미달 → 즉시 수정 후 재검증

---

## 13. 인수자 체크리스트 (Phase 18 착수 전)

- [ ] 이 문서를 기반으로 전체 맥락 파악
- [ ] `generator.py` Phase 17 섹션 확인
  - `_P17_POST2_OPENER_ENFORCEMENT` (~line 3220)
  - `_classify_parse_failed()` (~line 5355)
  - `_log_parse_failed_event()` (~line 5382)
  - `verify_draft()` PARSE_FAILED 처리 (~line 5456)
- [ ] `publish_history.json` 최신 이력 확인 (Post 187 PARSE_FAILED 이후 이력)
- [ ] Phase 18 Track 1: verifier_revision_closure FAIL/WARN 원인 분리 설계
- [ ] Phase 18 Track 2: fallback 발행 경로 TYPE별 정책 설계
- [ ] Phase 18 Track 3: PARSE_FAILED 원인별 후속 대응 규칙 설계
- [ ] Phase 18 Track 4: opener 안정 유지 추가 샘플 실행 계획 수립
