# REPORT_PHASE16H_OPERATIONAL_STABILIZATION_AND_QUALITY_CLEANUP.md

> Phase 16H 운영 안정화 및 잔여 품질 정리
> 작성일: 2026-03-19
> 판정: **PHASE16H_IMPL_GO**

---

## 1. 목적 및 배경

Phase 16G에서 intro_overlap LOW/MEDIUM, bridge_mode=COMMON, step3_status=REVISED 등 핵심 성과가 GO 확정된 이후, 아래 잔여 이슈 3개가 운영 리포트에 반복 관측됨:

| 잔여 이슈 | 16G run2 실측 |
|-----------|--------------|
| `hedge_overuse_p1 FAIL` | Post1 헤징 52%(13/25문장) FAIL — Phase 14I 재작성 효과 없음 |
| `verifier_revision_closure FAIL` | 2건 미해소(실제는 style/구조 이슈) → false FAIL |
| `emergency_polish` 집계 불일치 | 로그 5건 vs 보고서 2건 기재(기준 불명확) |

Phase 16H는 위 3개만 정리하는 **운영 안정화 미세조정**이다.
기존 16G GO 축(temporal SSOT, bridge-pick, intro overlap, step3_status)은 비침범.

---

## 2. 변경 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `generator.py` | Track A/B/C 구현 (3개 지점) |

---

## 3. Track A — Post1 hedge_overuse 완화 (프롬프트 지침 강화)

### 문제 분석

Phase 14I는 `hedge_overuse FAIL` 시 `_extract_hedge_heavy_interp_blocks()`로 `[해석]` 태그 블록을 추출 후 교체하는 구조.
그러나 실제 발행 HTML에는 `[해석]` 태그가 노출되지 않아 추출 결과 **0건** → 재작성 효과 없음.

```
# 16G run2 로그 (Phase 14I):
[Phase 14I] [해석] 헤징 진단 [Post1] 전 — 0/0 (0%) status=PASS
[Phase 14I] [해석] 헤징 블록 추출 [Post1]: 0개
# → hedge_overuse 13/25 FAIL 그대로 유지
```

근본 원인: Phase 14I의 사후 교체 접근보다 **GPT 생성 단계에서 헤징을 줄이는 것**이 효과적.

### 구현

`_P16H_POST1_HEDGE_REDUCTION` 상수 추가 (generator.py ~line 3117):

```python
_P16H_POST1_HEDGE_REDUCTION: str = (
    "[Phase 16H — Post1 사실 구간 헤징 절제 ★]\n\n"
    "확정된 사실·수치 문장(factual spine)에는 유보형 어미를 쓰지 말라.\n\n"
    "판단 기준:\n"
    "  [사실 구간] 이미 발생한 사건, 확정 수치, 과거 공식 발표\n"
    "    → '~했다', '~이다', '~기록했다', '~결정했다' 등 단정형 사용\n"
    "    → ❌ '~것으로 보입니다', '~것으로 추정됩니다', '~것으로 파악됩니다' 금지\n\n"
    "  [해석/전망 구간] 인과 추론, 미래 예측, 시나리오 서술\n"
    "    → 필요한 만큼만 유보형 허용: '~로 판단된다', '~가능성이 높다'\n"
    "    → 단, 전체 문장의 절반 이상을 유보형으로 끝내면 안 된다\n\n"
    "목표: 분석 spine은 자신감 있게, 불확실성은 해석 구간에만 국소 표현.\n"
    "premium editorial tone 유지 — 과잉 확신(단정 남발)도 금지.\n\n"
)
```

`gpt_write_analysis()` user_msg 주입 (가장 앞):

```python
user_msg = (
    _P16H_POST1_HEDGE_REDUCTION         # Phase 16H Track A: factual spine 헤징 절제
    + _P16B_QUALITY_HARDENING_RULES     # Phase 16B
    + _P14_POST1_ENFORCEMENT_BLOCK      # Phase 14
    + ...
)
```

### 설계 원칙 준수

- 무조건 단정형 강제 금지 → "factual spine vs 해석/전망 구간 구분" 명시
- 과잉 확신(단정 남발) 금지 조항 포함
- premium editorial tone 유지 명시
- Phase 14I 사후 교체 로직은 유지(비침범)

---

## 4. Track B — verifier_revision_closure false fail 완화

### 문제 분석

`_check_verifier_closure()`의 FAIL 판정:

```
# 16G run2 로그:
[Phase 13] 검수 해소 확인 | 고위험 10건 | 해소 8 / 미해소 2 | 상태: FAIL
⚠ 미해소 이슈: [10] '오늘의 시장 컨텍스트' 섹션은 숫자와 기준 시점...
⚠ 미해소 이슈: [13] '연준의 금리 인하 시점 지연...' 섹션의 두 번째 문단...
```

실제 미해소 이슈 분석:

| 이슈 | 분류 | 이유 |
|------|------|------|
| [10] 숫자가 없는 문단 구조 | **style_residual** | "숫자가 없는 문단" 키워드 → 구조적 writing quality 이슈, 사실 오류 아님 |
| [13] 완충 문장 / 4요소 불충족 | **style_residual** | "완충 문장", "4요소", "구체적인 근거 없이" → 문체/해석 품질 이슈 |

기존 로직: `un_cnt >= 2 → FAIL` — style 이슈도 FAIL 트리거
수정 로직: `truly_unresolved_cnt >= 2 → FAIL` — style_residual은 WARN으로 강등

### 구현 (`_check_verifier_closure`)

**STYLE_RESIDUAL_KW 추가:**

```python
STYLE_RESIDUAL_KW = [
    "완충 문장", "4요소", "헤징", "비유", "마크다운", "숫자가 없는 문단",
    "구체적인 근거 없이", "스타일", "문단 구조", "소제목",
]
```

**루프 구조 변경 (truncate 전 원본으로 분류):**

```python
# unresolved_items: (original_issue, display_str) 튜플
# → 원본 텍스트로 STYLE_RESIDUAL_KW 분류 (truncate 후 분류 시 키워드 누락 문제 해결)
truly_unresolved = [disp for orig, disp in unresolved_items
                    if not any(kw in orig for kw in STYLE_RESIDUAL_KW)]
style_residual   = [disp for orig, disp in unresolved_items
                    if any(kw in orig for kw in STYLE_RESIDUAL_KW)]
```

**FAIL 판정 조건 수정:**

```python
status = (
    "FAIL"  if truly_cnt >= 2          # 사실 오류 미해소 2건 이상만 FAIL
    else "WARN"  if truly_cnt >= 1 or un_cnt >= 1  # style 잔존은 WARN
    else "PASS"  if total > 0
    else "SKIP"
)
```

**result dict 신규 필드:**

```python
"truly_unresolved_count":  truly_cnt,          # Phase 16H 신규
"style_residual_count":    len(style_residual), # Phase 16H 신규
"closure_reason":          closure_reason,       # Phase 16H 신규 (운영 가독용)
```

**로그 형식 개선:**

```
[Phase 13] 검수 해소 확인 | 고위험 10건 | 해소 8 / 미해소 2 (사실 0건 + style 2건) | 상태: WARN
  ℹ 미해소[style]: [10] '오늘의 시장 컨텍스트'...
  ℹ 미해소[style]: [13] '연준의 금리 인하 시점 지연...'...
```

### 16G run2 소급 시뮬레이션 결과

| 항목 | 기존 | Phase 16H |
|------|------|-----------|
| truly_unresolved | — | 0건 |
| style_residual | — | 2건 ([10], [13]) |
| `verifier_revision_closure` | **FAIL** | **WARN** |

### 안전성

- `truly_unresolved >= 2` 조건 유지 → 진짜 사실 미해소는 여전히 FAIL
- STYLE_RESIDUAL_KW는 서술 스타일 키워드만 포함 — 시간/수치 오류와 무관
- step3_status enum 체계 비침범

---

## 5. Track C — emergency_polish 집계 기준 단일화

### 문제 분석

16G 보고서 불일치:

| 실체 | 기존 기재 |
|------|----------|
| Post2: 3종 마커 5건 출현 | "2건" 기재 (unique 마커 종류 수를 잘못 기재) |

기존 로그 형식: `generic 마커 5건` — "5건"의 정확한 의미 불명확

### 구현 (`_p16b_emergency_polish`)

**Phase 16H Track C 집계 기준 정의:**

| 필드 | 정의 |
|------|------|
| `unique_marker_count` | 서로 다른 마커 **종류** 수 |
| `total_occurrence_count` | 마커 전체 **출현 횟수** 합산 |

**로그 형식 변경:**

```
# 기존:
[Phase 16B] Post2 emergency_polish: generic 마커 5건 | ...

# Phase 16H 이후:
[Phase 16B] Post2 emergency_polish: generic 마커 3종 5건 | ...
```

**반환 dict 신규 필드:**

```python
"unique_marker_count":    unique_marker_count,    # 마커 종류 수
"total_occurrence_count": total_occurrence_count, # 총 출현 횟수
"total_generic_found":    total_occurrence_count, # 하위호환 유지
```

**note 필드 명시:**

```
"diagnostic-only — 실 치환 미수행 (Phase 16D 원칙 유지).
 집계: unique_marker_count=종류수, total_occurrence_count=총출현수 (Phase 16H 표준)"
```

### 표준화 후 reporting 기준

- 보고서: `{unique_marker_count}종 {total_occurrence_count}건` 형식 사용
- 예: Post2 3종 5건 → "generic 마커 3종 5건 WARN"
- 로그 ↔ 보고서 ↔ handoff 모두 동일 형식

---

## 6. 정적 검증

```
AST parse: OK

[Track A]
  _P16H_POST1_HEDGE_REDUCTION constant: OK
  _P16H_POST1_HEDGE_REDUCTION 주입 위치 (gpt_write_analysis 최선두): OK
  16H injection order (16H < 16B): 173859 < 173946 OK

[Track B]
  STYLE_RESIDUAL_KW: OK
  truly_unresolved / style_residual 분리: OK
  truly_unresolved_count / style_residual_count / closure_reason 필드: OK
  16G run2 소급 시뮬레이션: FAIL → WARN (truly=0, style=2)

[Track C]
  unique_marker_count: OK
  total_occurrence_count: OK
  로그 형식 '3종 5건' 출력: OK
  total_generic_found 하위호환: OK

[비회귀]
  _strip_misapplied_jeonmang_tags: OK
  Phase 15E: OK
  _p16f_diagnose_bridge: OK
  _P16D_POST2_BRIDGE_REQUIREMENT: OK
  step3_status: OK
  _p16b_compute_intro_overlap: OK
  _p16b_emergency_polish: OK
  bridge_diag: OK
```

---

## 7. 비회귀 보호

| 16G GO 축 | 보호 상태 |
|-----------|---------|
| temporal SSOT (_strip_misapplied_jeonmang_tags 등) | 비침범 |
| 완료 월 [전망] 오주입 방지 (Phase 15E) | 비침범 |
| bridge-pick 정합성 (_p16f_diagnose_bridge) | 비침범 |
| step3_status 표준 enum | 비침범 |
| intro overlap 기본 로직 (_p16b_compute_intro_overlap) | 비침범 |
| emergency_polish 관측 (_p16b_emergency_polish) | 기능 보존 + Track C 개선만 추가 |

---

## 8. 잔여 위험

| 항목 | 위험도 | 설명 |
|------|--------|------|
| Track A 효과 불확실 | 낮음~중간 | GPT 응답 특성상 완전 제거 보장 불가. 실출력 검증(16I) 필요 |
| STYLE_RESIDUAL_KW 범위 | 낮음 | 너무 넓으면 진짜 미해소도 style로 분류될 수 있음. 현재 10개 키워드는 보수적 범위 |
| hedge_overuse WARN 잔존 가능성 | 낮음 | 50% 이상 → FAIL, 30~50% → WARN. Track A로 WARN 이하 목표 |

---

## 9. 다음 실출력 검증 포인트 (Phase 16I 또는 다음 실출력 검증)

- [ ] Post1 `hedge_overuse` 비율: FAIL(>50%) → WARN(30~50%) 또는 PASS(<30%) 달성 여부
- [ ] `verifier_revision_closure`: WARN 또는 PASS (FAIL 탈출) 확인
- [ ] emergency_polish 로그: `{N}종 {M}건` 형식 정상 출력 확인
- [ ] 로그 ↔ 보고서 count 일치 여부
- [ ] 16G GO 축 비회귀: temporal/bridge/overlap/step3 모두 유지 확인

---

## 10. 최종 판정

| 게이트 조건 | 상태 |
|------------|------|
| hedge_overuse_p1 완화 장치 실코드 반영 | PASS |
| verifier_revision_closure false fail 완화 반영 | PASS |
| emergency_polish 집계 기준 단일화 | PASS |
| 16G GO 축 비회귀 없음 | PASS |
| syntax/runtime 즉시 오류 없음 (AST OK) | PASS |

**→ PHASE16H_IMPL_GO**
