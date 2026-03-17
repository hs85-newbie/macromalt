# REPORT_PHASE15E_CURRENT_YEAR_PAST_MONTH_SETTLEMENT_FIX

작성일: 2026-03-17
작성자: Claude Code
대상 파일: `generator.py`
Commit: `0645e9d`

---

## 1. Changed Files

| 파일 | 변경 유형 | 변경 규모 |
|------|-----------|-----------|
| `generator.py` | feat (추가) | +241 lines / -14 lines |

변경 내용 요약:
- Phase 15E 상수 3종 (`_P15E_COMPOUND_RE_NAL_*`) 추가
- `_P15E_FORECAST_VERB_MARKERS` 목록 추가
- `_detect_current_year_past_month_as_forecast()` 함수 추가
- `_enforce_current_year_month_settlement()` 함수 추가
- Post1 흐름 call site 추가 + `p13_scores["month_settlement"]` 추가
- Post2 흐름 call site 추가 + `p13_scores["month_settlement"]` 추가

---

## 2. Implementation Summary

### 2.1 문제 배경

Phase 15D 실출력 검증(REPORT_PHASE15D_REAL_OUTPUT_VALIDATION.md) 결과:

| 항목 | 결과 |
|------|------|
| 2025년 SK하이닉스 `[전망]` 태그 제거 | ✅ Phase 15D 해결 |
| 2026년 2월 양극재 `[전망]` 태그 + 예측 어미 | ❌ 미해결 — Phase 15E 범위 |

**실출력 실패 예시 (Post2, run_id 20260317_180244):**
```
[전망] 2026년 2월 국내 양극재 수출액은 4.1억 달러로 전월 대비 35% 증가하고,
수출량은 1.7만 톤으로 34% 늘어날 것으로 전망됩니다.
```

**실패 원인 분석:**
1. Phase 15A/15B regex: `([가-힣]+)할 것으로` — "늘어날"은 "날"로 끝나서 미매치
2. Phase 15D 탐지 조건: 확정 어미가 이미 존재해야 태그 제거 가능 — 어미가 아직 예측형이므로 미작동
3. Phase 15 연도 범위: `completed_years = range(run_year-3, run_year)` — 2026년 제외

→ **근본 원인:** 현재 연도(2026) 안의 과거 월(1~2월)은 기존 로직이 전혀 커버하지 않음

### 2.2 설계 원칙

| 원칙 | 구현 방식 |
|------|-----------|
| 시제 + 태그 동시 교정 | `_enforce_current_year_month_settlement()` 1회 호출로 동사+태그 일괄 처리 |
| 월 단위 안전 기준 | `run_month - 1` 이하 월만 settled로 판단 |
| 현재 월/미래 월 보존 | `run_month` 이상 → 탐지 제외 |
| Phase 15D 호환 | 기존 `_strip_misapplied_jeonmang_tags()` 호출 후 15E가 후처리 |
| 이중 교정 방지 | 이미 확정 어미인 경우 탐지 단계에서 early return |

### 2.3 추가된 핵심 컴포넌트

#### Track A — 현재 연도 과거 월 분류

**`_detect_current_year_past_month_as_forecast(content, run_year, run_month)`**

탐지 기준:
1. 현재 연도 (`run_year년`) 매칭
2. 이미 종료된 월 (`1월` ~ `run_month-1월`) 매칭
3. `_P15E_FORECAST_VERB_MARKERS` 중 하나 이상 포함

반환값: `{"violations": list, "violation_count": int, "status": str, "settled_periods": list}`

#### Track B — 동사 교정

**`_P15E_COMPOUND_RE_NAL_FORMAL/INFORMAL/CONNECTIVE`**

Phase 15A/15B가 `할 것으로 X됩니다` 형태를 커버한다면,
Phase 15E는 `날 것으로 X됩니다` 형태를 추가 커버:

```
늘어날 것으로 전망됩니다 → 늘어난 것으로 집계됐습니다
기록날 것으로 추정됩니다 → 기록난 것으로 집계됐습니다
(기록할 → 기록한 by 15A, 늘어날 → 늘어난 by 15E)
```

#### Track C — 태그 제거

**`_enforce_current_year_month_settlement()` Step 2:**

동사 교정 후 확정 어미가 이미 확보된 상태에서 `[전망]` 태그를 제거.
Phase 15D와 다른 점: 교정 이전 예측 어미 상태에서도 "현재 연도 과거 월" 확인만으로 제거 가능.

### 2.4 Call Sites

**Post1 흐름** (Phase 15D 직후):
```python
# ── Phase 15E: 현재 연도 과거 월 시제 + [전망] 태그 통합 교정 ─────────────
final_content, _p15e_log = _enforce_current_year_month_settlement(
    final_content, run_year=_run_year_int, label="Post1"
)
```

**Post2 흐름** (Phase 15D 직후):
```python
# ── Phase 15E: 현재 연도 과거 월 시제 + [전망] 태그 통합 교정 ─────────────
final_content, _p15e_log_p2 = _enforce_current_year_month_settlement(
    final_content, run_year=_p2_run_year_int, label="Post2"
)
```

---

## 3. Verification Results

### 3.1 단위 테스트 (11/11 PASS)

| 테스트 | 케이스 | 결과 |
|--------|--------|------|
| T1 | 2026년 2월 + "늘어날 것으로 전망됩니다" → 탐지 | ✅ PASS |
| T2-a | "늘어날 것으로 전망됩니다" → 확정 어미 교정 | ✅ PASS |
| T2-b | T2 이후 `[전망]` 태그 제거 | ✅ PASS |
| T2-c | T2 결과가 자연스러운 확정 어미 포함 | ✅ PASS |
| T3-a | 2026년 2월 + "기록할 것으로 추정됩니다" → 교정 | ✅ PASS |
| T3-b | T3 이후 `[전망]` 제거 | ✅ PASS |
| T4 | 2026년 3월(현재 월) → 위반 탐지 안 함 | ✅ PASS |
| T5 | 2026년 4월(미래 월) → 위반 탐지 안 함 | ✅ PASS |
| T6 | 2025년 확정 실적 Phase 15D 호환 유지 | ✅ PASS |
| T7 | 이미 확정 어미 문장 → 변경 없음(idempotent) | ✅ PASS |
| T8 | 2026년 1월 + "늘어날 것으로 전망됩니다" → 탐지 | ✅ PASS |

### 3.2 교정 전후 비교

**교정 전 (실출력 실패 케이스):**
```
[전망] 2026년 2월 국내 양극재 수출액은 4.1억 달러로 전월 대비 35% 증가하고,
수출량은 1.7만 톤으로 34% 늘어날 것으로 전망됩니다.
```

**교정 후:**
```
2026년 2월 국내 양극재 수출액은 4.1억 달러로 전월 대비 35% 증가하고,
수출량은 1.7만 톤으로 34% 늘어난 것으로 집계됐습니다.
```

### 3.3 빌드 / import 확인

```
import generator → OK (경고 없음, SyntaxError 없음)
```

---

## 4. Risks / Follow-up

### 4.1 알려진 제한

| 항목 | 내용 |
|------|------|
| "날" 어간 오탐 가능성 | "끝날 것으로 예상됩니다" 등 비집계 문장도 교정될 수 있음. 현재 탐지 조건(현재 연도 과거 월 명시)이 완화 역할. |
| 확정 어미 다양성 | "집계됐습니다"로 고정 교정. 원문 뉘앙스("기록됐습니다") 보존 미흡 가능. |
| 1월 run_month 엣지케이스 | run_month=1이면 settled_periods=[], 교정 불필요. early return 처리 완료. |
| HTML 태그 내 위치 | `[전망]` 태그가 HTML 속성 내에 있는 경우 미커버 (실제 발생 시 Phase 15D/15E 공통 이슈). |

### 4.2 후속 과제

- **실출력 재검증**: 다음 run에서 Post2 양극재 문단이 교정되는지 실 데이터로 확인
- **Step3 Verifier 프롬프트 개선**: Verifier가 "2026년 2월 이미 발표됐으므로 전망 불필요" 판단을 자체적으로 내릴 수 있도록 프롬프트 보강 (Phase 16 후보)
- **동사 교정 다양성**: "기록했습니다", "증가했습니다" 등 원문 맥락 반영 교정으로 발전 가능

---

## 5. Final Gate JSON

```json
{
  "current_year_past_month_classification": "PASS",
  "settled_month_jeonmang_removal": "PASS",
  "settled_month_future_verb_correction": "PASS",
  "combined_monthly_fix_readability": "PASS",
  "future_month_forecast_preservation": "PASS",
  "phase15d_compatibility": "PASS",
  "public_signature_stability": "PASS",
  "import_build": "PASS",
  "final_status": "GO"
}
```

---

## 부록 A: 테스트 로그 발췌

```
T1  PASS  2026년 2월 '늘어날 것으로 전망됩니다' → 위반 탐지
T2  PASS  '늘어날 것으로 전망됩니다' → confirmed 어미 교정
T2  PASS  '[전망]' 태그 제거
T2  PASS  결과가 자연스러운 확정 어미 포함
T3  PASS  '기록할 것으로 추정됩니다' → 교정
T3  PASS  '[전망]' 제거
T4  PASS  2026년 3월(현재 월) → 위반으로 탐지 안 함
T5  PASS  2026년 4월(미래 월) → 위반으로 탐지 안 함
T6  PASS  2025년 확정 실적 '[전망]' Phase 15D 제거 유지
T7  PASS  이미 확정 어미 문장 → 변경 없음
T8  PASS  2026년 1월 → 위반 탐지

결과: 11 PASS / 0 FAIL / 11 총계
```

## 부록 B: Phase 15 계보

| Phase | 범위 | 상태 |
|-------|------|------|
| 15A/15B | 완료 연도(2023–2025) `할 것으로 X됩니다` 패턴 교정 | GO |
| 15C | Step3 시간 기준점 주입 + Post2 내부 레이블 노출 차단 | GO |
| 15D | 완료 연도 확정 어미 확인 후 `[전망]` 태그 제거 | GO (실출력 HOLD) |
| **15E** | **현재 연도 과거 월 동사 + 태그 통합 교정** | **GO** |
