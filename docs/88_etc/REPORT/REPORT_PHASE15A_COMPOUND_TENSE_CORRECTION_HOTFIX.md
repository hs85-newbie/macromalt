# REPORT_PHASE15A_COMPOUND_TENSE_CORRECTION_HOTFIX

**작성일:** 2026-03-17
**대상 파일:** `generator.py`
**Phase 상태:** 구현 GO — 9/9 단위 테스트 PASS

---

## 1. Changed Files

| 파일 | 변경 유형 | 변경 위치 |
|------|-----------|-----------|
| `generator.py` | 수정 | `_P15_TENSE_CORRECTION_MAP` 확장 (복합 패턴 23개 추가) |
| `generator.py` | 추가 | `_P15A_COMPOUND_RE_FORMAL`, `_P15A_COMPOUND_RE_INFORMAL`, `_P15A_FUTURE_STEM_RE` 상수 |
| `generator.py` | 추가 | `_has_mixed_tense_residue()` 함수 |
| `generator.py` | 수정 | `_enforce_tense_correction()` — regex 복합 교정 Step 0 + 잔여 재검사 Step 2 추가 |
| `docs/REPORT_PHASE15A_COMPOUND_TENSE_CORRECTION_HOTFIX.md` | 신규 | 본 보고서 |

---

## 2. Implementation Summary

### 2.1 Phase 15 HOLD 원인 재확인

Phase 15 실출력 검증에서 발견된 실패 사례:

```
원문:  "[전망] 2025년 삼성전자의 매출은 238조원으로 23조 6천억원을 기록할 것으로 추정됩니다"
교정후: "[전망] 2025년 삼성전자의 매출은 238조원으로 23조 6천억원을 기록할 것으로 집계됐습니다"
```

**문제:** `_P15_TENSE_CORRECTION_MAP`이 `"것으로 추정됩니다"` → `"것으로 집계됐습니다"` 패턴을 매칭했으나,
미래형 어간 `"기록할"`은 그대로 잔존 → 시제 혼재 상태 유지.

**근본 원인:**
- `_P15_TENSE_CORRECTION_MAP`에 `"기록할 것으로 예상됩니다"`, `"기록할 것으로 전망됩니다"` 패턴은 있었으나
  `"기록할 것으로 추정됩니다"` 패턴이 누락됨
- 더 큰 문제: 리스트 기반 교정 맵은 패턴을 명시적으로 열거해야 하므로 누락된 조합에는 무력화됨

### 2.2 Phase 15A 설계 원칙

**핵심 원칙:** 미래형 어간+어미를 묶어서 한 번에 교체 (복합 교정)

```
[어간]할 것으로 [추정|예상|전망|기대|관측]됩니다
→ [어간]한 것으로 집계됐습니다
```

이 패턴은 어간이 무엇이든 동일하게 적용 가능 → regex 엔진이 최적 도구.

### 2.3 구현 변경 사항

#### Change 1 — `_P15_TENSE_CORRECTION_MAP` 복합 패턴 23개 선행 추가

기존 맵 상단에 `# Phase 15A: 복합 패턴 최우선` 섹션 추가:

```python
("기록할 것으로 추정됩니다",       "기록한 것으로 집계됐습니다"),
("기록할 것으로 추정된다",         "기록한 것으로 집계됐다"),
("달성할 것으로 추정됩니다",       "달성한 것으로 집계됐습니다"),
("달성할 것으로 추정된다",         "달성한 것으로 집계됐다"),
("증가할 것으로 추정됩니다",       "증가한 것으로 집계됐습니다"),
("감소할 것으로 추정됩니다",       "감소한 것으로 집계됐습니다"),
("올릴 것으로 추정됩니다",         "올린 것으로 집계됐습니다"),
("확대할 것으로 추정됩니다",       "확대한 것으로 집계됐습니다"),
("기록할 것으로 기대됩니다",       "기록한 것으로 확인됐습니다"),
... (총 23개)
```

이 섹션은 리스트 순회 시 짧은 패턴(`"것으로 추정됩니다"`)보다 반드시 먼저 매칭됨.

#### Change 2 — Regex 복합 교정 엔진 상수 추가

```python
_P15A_COMPOUND_RE_FORMAL = re.compile(
    r"([가-힣]+)할(\s+것으로\s+)(추정|예상|전망|기대|관측)됩니다"
)
_P15A_COMPOUND_RE_INFORMAL = re.compile(
    r"([가-힣]+)할(\s+것으로\s+)(추정|예상|전망|기대|관측)된다"
)
_P15A_FUTURE_STEM_RE = re.compile(r"[가-힣]+할\s+것으로")
```

어간(group 1)을 캡처하여 교체 시 재사용: `m.group(1) + "한" + m.group(2) + "집계됐습니다"`

#### Change 3 — `_has_mixed_tense_residue()` 추가

교정 후 엄격 재검사 함수:

```python
def _has_mixed_tense_residue(sentence: str, completed_years: list) -> bool:
    """완료 연도 참조 + 미래형 어간이 공존하면 True"""
    has_completed_year = any(str(cy) + "년" in sentence for cy in completed_years)
    if not has_completed_year:
        return False
    return bool(_P15A_FUTURE_STEM_RE.search(sentence))
```

교정 후 `"기록할 것으로"` 등이 잔존할 경우 `True` → 로그에 경고 기록, `residue_check: "unresolved_residue"`.

#### Change 4 — `_enforce_tense_correction()` 흐름 재구성

**새 실행 순서:**

```
Step 0: _P15A_COMPOUND_RE_FORMAL.sub() + _P15A_COMPOUND_RE_INFORMAL.sub()
        → 전체 컨텐츠 regex 스캔 (어간+어미 동시 교체)
        → 교정이 발생했으면 재탐지 → PASS면 즉시 반환

Step 1: 재탐지 후 잔여 위반 문장별 _P15_TENSE_CORRECTION_MAP 순회
        (복합 패턴이 맵 상단에 있으므로 긴 패턴 우선 매칭)

Step 2: 각 교정 문장에 _has_mixed_tense_residue() 검사
        → 잔여 있으면 WARNING 로그 + correction_log에 "unresolved_residue" 기록

Step 3: post_correction_recheck — 최종 위반 건수 로그
```

### 2.4 Longest-Match-First 보장 방식

두 레이어로 longest-match-first 보장:

| 레이어 | 방법 | 보장 이유 |
|--------|------|-----------|
| Regex (Step 0) | `_P15A_COMPOUND_RE_FORMAL/INFORMAL` | 어간 패턴 전체를 캡처하므로 suffix-only 매칭 불가 |
| List Map (Step 1) | 복합 패턴을 맵 상단에 배치 + `break on first match` | 순서 보장 — 길고 구체적인 패턴이 먼저 시도됨 |

### 2.5 False Flattening 방지

- `_P15_PRELIMINARY_MARKERS`, `_P15_CONSENSUS_MARKERS`, `_P15_GUIDANCE_MARKERS` 예외 처리는 Phase 15에서 그대로 유지
- 잠정/컨센서스/가이던스 마커를 포함한 문장 → 탐지 시 `WARN` 분류 → 자동 교정 대상에서 제외
- Phase 15A regex 엔진은 탐지 단계가 아닌 교정 단계에서 동작 → 탐지 예외 처리가 먼저 필터링 후 교정 진행

---

## 3. Verification Results

### 3.1 단위 테스트 (9/9 PASS)

| # | 입력 패턴 | 기대 결과 | 실제 결과 | 판정 |
|---|-----------|-----------|-----------|------|
| 1 | `기록할 것으로 추정됩니다` (2025년) | `기록한 것으로 집계됐습니다` | ✓ | PASS |
| 2 | `달성할 것으로 추정된다` (2024년) | `달성한 것으로 집계됐다` | ✓ | PASS |
| 3 | `증가할 것으로 추정됩니다` (2024년) | `증가한 것으로 집계됐습니다` | ✓ | PASS |
| 4 | `기록할 것으로 예상됩니다` (2024년) — 기존 Phase 15 | `기록한 것으로 집계됐습니다` | ✓ (regex 처리) | PASS |
| 5 | `증가할 것으로 예상됩니다` (2027년) — 미래 연도 | 탐지 안 됨 | status=PASS | PASS |
| 6 | `_has_mixed_tense_residue` — 잔여 있음 | True | True | PASS |
| 7 | `_has_mixed_tense_residue` — 잔여 없음 | False | False | PASS |
| 8 | 잠정 마커 포함 → 자동 교정 제외 | status=WARN | status=WARN | PASS |
| 9 | 가이던스 마커 포함 → 자동 교정 제외 | status=WARN | status=WARN | PASS |

### 3.2 핵심 수정 케이스 전후 비교

**Phase 15 HOLD 원인 케이스:**

```
입력:  "2025년 삼성전자의 매출은 238조원으로 23조 6천억원을 기록할 것으로 추정됩니다."
Phase 15 교정 결과: "...기록할 것으로 집계됐습니다"  ← 미래형 어간 잔존
Phase 15A 교정 결과: "...기록한 것으로 집계됐습니다" ← 어간+어미 동시 교체 완료
```

### 3.3 Phase 15 호환성 확인

- 기존 Phase 15 단위 테스트 (Tests 4, 8, 9) 모두 통과
- `_detect_completed_year_as_forecast()` 시그니처 변경 없음
- `_enforce_tense_correction()` 반환 타입 `tuple(str, list)` 유지
- `p13_scores["tense"]` 구조 변경 없음
- 파이프라인 wiring 코드 변경 없음

### 3.4 빌드 확인

```
venv/bin/python3 -c "import generator; print('Import OK')"
→ Import OK (경고 없음)
```

---

## 4. Risks / Follow-up

### 4.1 잔존 리스크

| 리스크 | 심각도 | 설명 |
|--------|--------|------|
| 한글 어간 범위 | 낮음 | `[가-힣]+할` 패턴은 매우 넓게 매칭됨. 비-한국어 컨텍스트나 복잡한 HTML에서 예상치 못한 매칭 발생 가능성 낮으나 존재 |
| [전망] 섹션 레이블 | 중간 | Phase 15 HOLD 케이스에서 `[전망]` 섹션 내 2025년 완료 실적이 기록된 것 자체는 생성 단계 프롬프트 문제. Phase 15A는 교정 레이어만 처리 — 섹션 레이블 개선은 Phase 16 범위 |
| 컨센서스/가이던스 WARN 미교정 | 낮음 | 잠정/컨센서스/가이던스 예외는 자동 교정에서 제외됨 — 실출력에서 뉘앙스 보존이 목표이므로 의도된 동작 |
| Regex 교정 후 문체 | 낮음 | regex 복합 교정 결과는 "기록한 것으로 집계됐습니다" 형태로 고정됨. 문맥에 따라 다른 어미(집계됐다 → 나타났다 등)가 더 자연스러울 수 있으나 신뢰성 우선 |

### 4.2 후속 권장 사항

1. **실출력 검증 재실행 (Phase 15A Real-Output Validation)**
   Phase 15A 구현 후 실제 런을 실행하여 "기록할" 어간 잔존 여부 최종 확인 필요.

2. **[전망] 섹션 레이블 문제**
   2025년 완료 실적이 `[전망]` 섹션에 등장하는 근본 원인은 생성 프롬프트 설계 문제.
   Phase 16 범위로 섹션 레이블 + 콘텐츠 일치 강제 검토 권장.

3. **복합 패턴 커버리지 확장 모니터링**
   `_has_mixed_tense_residue()` 경고 로그를 모니터링하여 커버되지 않는 어간 패턴 발견 시 맵 추가.

---

## 5. Final Gate JSON

```json
{
  "compound_pattern_priority": "PASS",
  "longest_match_first_ordering": "PASS",
  "compound_tense_correction": "PASS",
  "mixed_tense_residue_detection": "PASS",
  "post_correction_recheck": "PASS",
  "guidance_consensus_nuance_preservation": "PASS",
  "phase15_compatibility": "PASS",
  "public_signature_stability": "PASS",
  "import_build": "PASS",
  "final_status": "GO"
}
```

---

## 6. 검증 체크리스트

- [x] 복합 패턴 교정 동작 확인 (`기록할 것으로 추정됩니다` → `기록한 것으로 집계됐습니다`)
- [x] Longest-match-first 순서 보장 (regex 먼저, 리스트 맵 복합 패턴 상단 배치)
- [x] 단순 suffix 교체가 더 나은 복합 교정을 선점하지 않음 (Step 0 regex 우선)
- [x] 혼재 시제 잔여 unresolved로 처리 (`_has_mixed_tense_residue()` 검증)
- [x] 교정 후 재검사 동작 확인 (`post_correction_recheck` 로그 확인)
- [x] 가이던스/컨센서스 뉘앙스 보존 (Tests 8, 9 PASS)
- [x] Phase 15 호환성 유지 (기존 패턴 Tests 4, 8, 9)
- [x] 공개 함수 시그니처 안정성 유지
- [x] import/build PASS
