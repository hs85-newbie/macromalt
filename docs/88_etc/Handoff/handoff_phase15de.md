# Phase 15D–15E 핸드오프 — 시간 신뢰도 강화 (태그 제거 + 현재 연도 과거 월 교정)

작성일: 2026-03-17
세션 범위: Phase 15D 실출력 검증 → Phase 15E 구현 → Phase 15E 실출력 검증
최종 게이트: **PHASE15E_OUTPUT_HOLD**
다음 단계: **Phase 15F — 월 기반 강제 `[전망]` 제거 (동사 독립)**

---

## 세션 전체 작업 이력

### 1. Phase 15D 실출력 검증 (HOLD 확인)

**목적:** Phase 15D `_strip_misapplied_jeonmang_tags()`가 발행 본문에서 실제로 작동하는지 검증.

**실행 런:** run_id 20260317_180244, Post IDs 158/159

**결과:**

| 검증 항목 | 결과 |
|-----------|------|
| 2025년 SK하이닉스 `[전망]` 제거 | ✅ Phase 15D 성공 |
| 2026년 2월 양극재 `[전망]` + 예측 동사 | ❌ 미해결 |

**2026년 2월 실패 원인 (Post 159):**
```
[전망] 2026년 2월 국내 양극재 수출액은 4.1억 달러로 전월 대비 35% 증가하고,
수출량은 1.7만 톤으로 34% 늘어날 것으로 전망됩니다
```

세 가지 원인이 겹쳐 발생:
1. Phase 15A/15B regex: `([가-힣]+)할 것으로` — "늘어날"은 "날"로 끝나서 미매치
2. Phase 15D 조건: 확정 어미가 이미 있어야 `[전망]` 제거 가능 — 예측 어미 상태에서는 미작동
3. Phase 15 연도 범위: `completed_years = range(run_year-3, run_year)` — 2026년 제외

**참고 보고서:** `docs/REPORT_PHASE15D_REAL_OUTPUT_VALIDATION.md`

---

### 2. Phase 15E 구현 (GO)

**목적:** 현재 연도(2026) 안의 과거 월(1~2월) 집계 데이터가 예측 어미 + `[전망]` 태그로 서술되는 문제를 동사 + 태그 동시 교정.

**Commit:** `0645e9d` / `e7f0bee`

**추가된 구성요소:**

| 구성 요소 | 위치 (generator.py) | 역할 |
|-----------|--------------------|----|
| `_P15E_COMPOUND_RE_NAL_FORMAL` | ~line 2481 | "날 것으로 추정/전망됩니다" 교정 regex |
| `_P15E_COMPOUND_RE_NAL_INFORMAL` | ~line 2484 | "날 것으로 X된다" 교정 regex |
| `_P15E_COMPOUND_RE_NAL_CONNECTIVE` | ~line 2487 | "날 것으로 X되며/되고" 교정 regex |
| `_P15E_FORECAST_VERB_MARKERS` | ~line 2492 | 현재 연도 과거 월 탐지용 예측 동사 목록 (15종) |
| `_detect_current_year_past_month_as_forecast()` | ~line 2505 | Track A/C: 위반 탐지 |
| `_enforce_current_year_month_settlement()` | ~line 2578 | Track B/C: 동사 교정 + `[전망]` 제거 |

**Call sites:**
- Post1 흐름: Phase 15D 호출 직후 `_enforce_current_year_month_settlement()` 호출
- Post2 흐름: 동일
- `p13_scores["month_settlement"]` 키로 로그 수집

**단위 테스트:** 11/11 PASS
- `늘어날 것으로 전망됩니다` → `늘어난 것으로 집계됐습니다` ✅
- `기록할 것으로 추정됩니다` → `기록한 것으로 집계됐습니다` ✅
- 현재 월(3월) / 미래 월(4월) 보존 ✅
- Phase 15D 호환 ✅
- Idempotency ✅

**참고 보고서:** `docs/REPORT_PHASE15E_CURRENT_YEAR_PAST_MONTH_SETTLEMENT_FIX.md`

---

### 3. Phase 15E 실출력 검증 (HOLD)

**실행 런:** run_id 20260317_190543, Post IDs 160/161
- Post1: https://macromalt.com/…심층분석…양극재-수출-6/
- Post2: https://macromalt.com/…캐시의-픽…양극재-수출/

**Phase 15E 로그 요약:**

| Post | Phase 15D | Phase 15E 탐지 | Phase 15E 교정 |
|------|-----------|---------------|---------------|
| Post1 | `[전망]` 1건 제거 ✅ | 위반 1건 탐지 ✅ | 패턴 미매치 — 실패 ❌ |
| Post2 | 이슈 없음 ✅ | 탐지 미발동 ⚠ | 교정 불필요 (but `[전망]` 잔존) ❌ |

**잔존 실패 케이스:**

| 위치 | 문장 | 실패 유형 |
|------|------|-----------|
| Post1 양극재 섹션 | `수출량은 1.7만 톤으로 34% 증가한 것으로 추정됩니다` | "한 것으로" 패턴 regex 미매치 |
| Post1 양극재 섹션 | `[전망] 수출 단가는 24달러/kg로 1% 상승한 것으로 파악됩니다` | "파악됩니다" Phase 15D/15E 사각지대 |
| Post2 도입부 | `[전망] 2026년 2월 양극재 수출액이 전월 대비 35% 증가했으며 ... 파악됩니다` | "파악됩니다" Phase 15E 탐지 미발동 |

**참고 보고서:** `docs/REPORT_PHASE15E_REAL_OUTPUT_VALIDATION.md`

---

## 현재 상태 스냅샷

### Generator.py Phase 15 레이어 구조

```
[Phase 15A/15B] 완료 연도(2023–2025) "할 것으로 X됩니다" 동사 교정
        ↓
[Phase 15C]     Step3 시간 기준점 프롬프트 주입 + Post2 내부 레이블 차단
        ↓
[Phase 15D]     확정 어미 확인 후 완료 연도/확정 기간 [전망] 제거
        ↓
[Phase 15E]     현재 연도 과거 월 "날/할 것으로" 동사 교정 + [전망] 제거
        ↓
[Phase 15F]     ← 미구현 (다음 단계)
```

### Phase 게이트 현황

| Phase | 구현 | 실출력 |
|-------|------|--------|
| 11 | GO | GO |
| 12 | GO | GO |
| 13 | GO | HOLD (유지) |
| 14I | GO | GO (타겟 범위) |
| 15 | GO | HOLD → 15A/15B로 개선 |
| 15A/15B | GO | GO |
| 15C | GO | GO |
| 15D | GO | HOLD → 15E로 부분 개선 |
| **15E** | **GO** | **HOLD** |
| 15F | 미구현 | — |

---

## 다음 단계: Phase 15F

### 문제 정의

Phase 15D와 15E는 모두 특정 동사 형태에 의존한다. GPT가 다음 동사를 사용할 때 사각지대 발생:

| 동사 | Phase 15D | Phase 15E | 결과 |
|------|-----------|-----------|------|
| `집계됐습니다` | ✅ 확정 | — | `[전망]` 제거 ✅ |
| `기록됐습니다` | ✅ 확정 | — | `[전망]` 제거 ✅ |
| `늘어날 것으로 전망됩니다` | ❌ | ✅ 탐지+교정 | ✅ |
| `기록할 것으로 추정됩니다` | ❌ | ✅ 탐지+교정 | ✅ |
| **`파악됩니다`** | **❌** | **❌ 탐지 미발동** | **`[전망]` 잔존** |
| **`증가한 것으로 추정됩니다`** | **❌** | **✅ 탐지, ❌ 미매치** | **`[전망]` + 추정 잔존** |

### Phase 15F 설계 원칙

**핵심 규칙:** `[전망]` 태그 직후 문장에 `{run_year}년 {past_month}월` 문자열이 있으면, 동사 형태에 무관하게 `[전망]` 제거.

**예외 조건 (오적용 방지):** 동일 문장에 순수 미래 동사(`할 것으로 전망됩니다`, `할 것으로 예상됩니다`, `할 것으로 보입니다`)가 있으면 제거 보류.

**설계:**
```python
def _strip_current_year_past_month_jeonmang(
    content: str,
    run_year: int = 2026,
    run_month: int = None,
    label: str = "",
) -> tuple:
    """Phase 15F: 동사 형태 독립 — 현재 연도 과거 월 앞 [전망] 태그 강제 제거.

    조건: [전망] 직후 문장에 {run_year}년 {m}월 (m < run_month) 포함
    예외: 순수 미래 동사 존재 시 보류
    Phase 15D/15E 이후 후처리 단계로 동작
    """
```

**구현 우선순위:**
1. 현재 연도 과거 월 문자열(`2026년 1월`, `2026년 2월`) 탐지 — 이미 Phase 15E `settled_periods` 로직 재사용 가능
2. `[전망]` 태그가 해당 문자열을 포함한 문장 또는 직전에 있는지 확인
3. 순수 미래 동사 예외 처리
4. 제거 + 로그

**예상 효과:**
- `[전망] 수출 단가는 24달러/kg로 1% 상승한 것으로 파악됩니다` → 제거 ✅
- `[전망] 2026년 2월 양극재 수출액이 전월 대비 35% 증가했으며...` → 제거 ✅
- `[전망] 2분기부터 양극재 판가에 긍정적인 영향을 미칠 것으로 예상됩니다` → 미래 동사 예외 → 보존 ✅

---

## 변경된 파일 목록 (이번 세션)

| 파일 | 커밋 | 내용 |
|------|------|------|
| `generator.py` | `b3f1f89` | Phase 15D: `_strip_misapplied_jeonmang_tags()` 추가 + Post1/Post2 call site |
| `generator.py` | `0645e9d` | Phase 15E: 상수 3종 + `_detect_*` + `_enforce_*` 추가 + call site + p13_scores |
| `docs/REPORT_PHASE15D_JEONMANG_TAG_STRIP.md` | `4bd4474` | Phase 15D 구현 보고서 |
| `docs/REPORT_PHASE15D_REAL_OUTPUT_VALIDATION.md` | `d86c3fc` | Phase 15D 실출력 검증 (HOLD) |
| `docs/REPORT_PHASE15E_CURRENT_YEAR_PAST_MONTH_SETTLEMENT_FIX.md` | `e7f0bee` | Phase 15E 구현 보고서 (GO) |
| `docs/REPORT_PHASE15E_REAL_OUTPUT_VALIDATION.md` | `987d12f` | Phase 15E 실출력 검증 (HOLD) |
| `docs/handoff_phase15de.md` | 이 파일 | 핸드오프 |

---

## 코드 참조 위치 (generator.py)

```
~line 2371  # ── Phase 15D: Misapplied [전망] Tag Strip
~line 2403  def _strip_misapplied_jeonmang_tags(...)
~line 2467  # ── Phase 15E: Current-Year Past-Month Settlement Fix
~line 2481  _P15E_COMPOUND_RE_NAL_FORMAL
~line 2492  _P15E_FORECAST_VERB_MARKERS
~line 2505  def _detect_current_year_past_month_as_forecast(...)
~line 2578  def _enforce_current_year_month_settlement(...)
~line 4721  # Post1 Phase 15D call site
~line 4725  # Post1 Phase 15E call site
~line 4945  # Post2 Phase 15D call site
~line 4949  # Post2 Phase 15E call site
```

---

## 인수자를 위한 요약

1. **Phase 15E는 구현 GO, 실출력 HOLD 상태.**
   - "늘어날/증가할 것으로 전망됩니다" 클래스는 잡힌다.
   - "파악됩니다", "증가한 것으로 추정됩니다" 클래스는 아직 잡히지 않는다.

2. **다음 작업은 Phase 15F 하나만 구현하면 된다.**
   - `PROMPT_PHASE15F_MONTH_BASED_JEONMANG_STRIP.md` 작성 후 구현.
   - 기존 Phase 15D/15E 위에 동사 독립 강제 제거 레이어 1개 추가.
   - 예상 코드량: 40–60라인.

3. **Phase 13의 hedge_overuse, counterpoint_specificity FAIL은 별도 트랙 이슈.**
   - Phase 15F 범위 아님. 시간 신뢰도 우선 완결 후 접근 권장.

4. **프롬프트 파일 위치:** `/Users/cjons/Documents/dev/macromalt/jobs/`
5. **보고서 위치:** `/Users/cjons/Documents/dev/macromalt/docs/`
6. **메모리 파일:** `/Users/cjons/.claude/projects/-Users-cjons-Documents-dev-macromalt/memory/`
