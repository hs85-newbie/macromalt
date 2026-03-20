# REPORT_PHASE19_LOG_ENHANCEMENT.md

작성일: 2026-03-20
Phase: **Phase 19 — Track 1 로그 보강 실행 보고**
범위: T1-1 slot/post_type 보강 / T1-2 PICKS offset 추가 / T1-3 권장 필드 4종 직접 로그화
데이터 기준: generator.py 코드 변경 실행 기준 (신규 발행 샘플은 Track 2에서 수행)

---

## 1. 작업 개요

Phase 18 CONDITIONAL GO로 이관된 로그 보강 5건 중 코드 수정으로 해결 가능한 3건을 실행했다.

| Track | 항목 | 방식 | 상태 |
|---|---|---|---|
| T1-1 | `slot/post_type=unknown` 해소 | `verify_draft()` 시그니처 수정 + 호출부 2곳 수정 | ✅ 완료 |
| T1-2 | PICKS offset 로그 추가 | `_log_parse_failed_event()` 내 자동 탐지 로직 추가 | ✅ 완료 |
| T1-3 | 권장 필드 4종 직접 로그화 | `_log_parse_failed_event()` 내 자동 계산 로직 추가 | ✅ 완료 |
| T2-1 | TYPE_D 추가 샘플 확보 | 신규 발행 실행 필요 | ⏳ 대기 |
| T2-2 | 신규 TYPE 즉시 실전 검증 | 발생 시 적용 | ⏳ 대기 |

---

## 2. T1-1 — `slot/post_type=unknown` 해소

### 원인

`verify_draft(draft: str)` 함수가 `slot`, `post_type` 파라미터를 받지 않아, PARSE_FAILED 발생 시 `_log_parse_failed_event()` 호출 시점에 `slot="unknown"`, `post_type="unknown"`으로 하드코딩됨.

### 수정 내용

**① `verify_draft()` 시그니처 변경** (line ~5493)

```python
# Before
def verify_draft(draft: str) -> dict:

# After (Phase 19 T1-1)
def verify_draft(draft: str, *, slot: str = "unknown", post_type: str = "unknown") -> dict:
```

**② `_log_parse_failed_event()` 호출부 수정** (verify_draft 내부)

```python
# Before
_log_parse_failed_event(
    run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
    slot="unknown",
    post_type="unknown",
    ...
)

# After (Phase 19 T1-1)
_log_parse_failed_event(
    run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
    slot=slot,       # ← 파라미터 값 전달
    post_type=post_type,  # ← 파라미터 값 전달
    ...
)
```

**③ Post1 호출부 수정** (line ~5701)

```python
# Before
verify_result = verify_draft(draft)

# After (Phase 19 T1-1)
verify_result = verify_draft(draft, slot=slot, post_type="post1")
```

**④ Post2 호출부 수정** (line ~5953)

```python
# Before
verify_result = verify_draft(draft)

# After (Phase 19 T1-1)
verify_result = verify_draft(draft, slot=slot, post_type="post2")
```

### 완료 기준 대조

| 기준 | 상태 |
|---|---|
| 신규 PARSE_FAILED 로그에서 `slot != unknown` | ✅ 코드 반영 완료 — 다음 PARSE_FAILED 발생 시 실제 슬롯명 기록 |
| 신규 PARSE_FAILED 로그에서 `post_type != unknown` | ✅ `"post1"` 또는 `"post2"` 값으로 고정 |
| 최소 1건 이상 샘플 로그로 확인 | ⏳ 신규 발행 실행 후 확인 (Track 2) |

---

## 3. T1-2 — PICKS offset / locator 로그 추가

### 수정 내용

`_log_parse_failed_event()` 내부에 PICKS 구간 자동 탐지 로직 추가.

```python
# Phase 19 T1-2: PICKS 구간 offset 탐지
_picks_markers = ["<!-- PICKS:", "<!-- picks:", "<!-- PICKS -->",
                  "<!-- picks -->", "PICKS:", "picks:"]
picks_section_offset: int = -1
for _marker in _picks_markers:
    _pos = (raw_output or "").find(_marker)
    if _pos >= 0:
        picks_section_offset = _pos
        break
```

로그 엔트리에 추가:
```python
"picks_section_offset": picks_section_offset,  # -1 = 구간 미발견 (TYPE_D 발생 조건)
```

### 해석 원칙

- `picks_section_offset == -1`: PICKS 주석 구간 미발견 → TYPE_D 탐지 조건과 일치. 구간 locator 없음.
- `picks_section_offset >= 0`: PICKS 주석 존재. 해당 오프셋 기준 전후 문맥 분석 가능.

### 완료 기준 대조

| 기준 | 상태 |
|---|---|
| TYPE_D 재발 로그에서 문제 구간 locator 확인 가능 | ✅ 코드 반영 완료. `picks_section_offset=-1` 기록 예정. |
| raw snapshot과 함께 offset 확인 가능 | ✅ 동일 log_entry에 `raw_output_snapshot`과 함께 기록됨. |

---

## 4. T1-3 — 권장 필드 4종 직접 로그화

### 수정 내용

`_log_parse_failed_event()` 내부에 4개 필드 자동 계산 로직 추가.

```python
# opener_pass: pick-angle H3 패턴 존재 + 금지 opener 6종 미포함
_has_pick_angle = bool(re.search(r"왜\s+지금\s+\S+인가|을\s+먼저\s+봐야\s+하는\s+이유", _raw))
_has_banned_opener = any(p in _raw for p in _opener_banned)
opener_pass: bool = _has_pick_angle and not _has_banned_opener

# criteria_5_pass: 권유성 표현 부재
_criteria5_banned = ["매수", "유망", "담아야", "사야", "투자 추천", "강력 추천"]
criteria_5_pass: bool = not any(p in _raw for p in _criteria5_banned)

# criteria_1_pass: 30일 초과 시점 단독 사용 간이 지표
_criteria1_risk = bool(re.search(r"지난\s*해|작년|전년\s*동기", _raw))
criteria_1_pass: bool = not _criteria1_risk

# source_structure_pass: 참고 출처 블록 존재
_source_markers = ["참고 출처", "📊", "증권사 리서치", "뉴스 기사"]
source_structure_pass: bool = any(m in _raw for m in _source_markers)
```

### 판정 정밀도 주의사항

| 필드 | 판정 방식 | 정밀도 | 비고 |
|---|---|---|---|
| `opener_pass` | regex + 금지 패턴 탐지 | **높음** | pick-angle 패턴 직접 탐지 |
| `criteria_5_pass` | 금지 표현 부재 | **높음** | 권유성 6종 키워드 탐지 |
| `criteria_1_pass` | 시점 어휘 간이 탐지 | **간이** | "지난해/작년/전년동기" 기반 — 오탐 가능. 보완 판정용. |
| `source_structure_pass` | 출처 마커 탐지 | **높음** | 참고 출처/📊 블록 탐지 |

**NOTE**: `criteria_1_pass`는 간이 지표로, 정밀 판정은 verifier가 담당. 로그 기록 용도로만 사용.

### 완료 기준 대조

| 기준 | 상태 |
|---|---|
| 로그만으로 4개 필드 상태 확인 가능 | ✅ 코드 반영 완료. warning 로그에 전체 필드 출력됨. |
| 신규 샘플 3건 이상에서 기록 확인 | ⏳ 신규 발행 실행 후 확인 (Track 2) |

---

## 5. 로그 보강 전/후 비교표

### Phase 17 (Before)

```
[Phase 17] PARSE_FAILED 런타임 이벤트
  run_id=20260319_180909
  slot=unknown                   ← 미기록
  post_type=unknown              ← 미기록
  failure_type=TYPE_D
  parse_stage=Step3:verifier:json_parse
  failed_section=verifier_response
  fallback_used=True
  publish_blocked=False
  (picks_section_offset 없음)   ← 미기록
  (opener_pass 없음)             ← 미기록
  (criteria_1_pass 없음)        ← 미기록
  (criteria_5_pass 없음)        ← 미기록
  (source_structure_pass 없음)  ← 미기록
```

### Phase 19 (After)

```
[Phase 19] PARSE_FAILED 런타임 이벤트
  run_id=<YYYYMMDD_HHMMSS>
  slot=morning                   ← 실제 슬롯명
  post_type=post2                ← post1 또는 post2
  failure_type=TYPE_D
  parse_stage=Step3:verifier:json_parse
  failed_section=verifier_response
  fallback_used=True
  publish_blocked=False
  picks_section_offset=-1        ← PICKS 구간 위치 (미발견 시 -1)
  opener_pass=True               ← pick-angle 구조 유지 여부
  criteria_1_pass=True           ← 시점 혼합 간이 판정
  criteria_5_pass=True           ← 권유성 표현 부재 여부
  source_structure_pass=True     ← 참고 출처 블록 존재 여부
```

### 필드 보강 현황 요약

| 필드 | Phase 17 | Phase 19 | 개선 |
|---|---|---|---|
| run_id | ✅ | ✅ | — |
| slot | ❌ unknown | ✅ 실제값 | **해소** |
| post_type | ❌ unknown | ✅ post1/post2 | **해소** |
| failure_type | ✅ | ✅ | — |
| parse_stage | ✅ | ✅ | — |
| failed_section_name | ✅ | ✅ | — |
| raw_output_snapshot | ✅ | ✅ | — |
| normalized_output_snapshot | ✅ | ✅ | — |
| fallback_used | ✅ | ✅ | — |
| publish_blocked | ✅ | ✅ | — |
| **picks_section_offset** | ❌ 없음 | ✅ 자동 탐지 | **신규 추가** |
| **opener_pass** | ❌ 없음 | ✅ 자동 계산 | **신규 추가** |
| **criteria_1_pass** | ❌ 없음 | ✅ 간이 계산 | **신규 추가** |
| **criteria_5_pass** | ❌ 없음 | ✅ 자동 계산 | **신규 추가** |
| **source_structure_pass** | ❌ 없음 | ✅ 자동 탐지 | **신규 추가** |

---

## 6. Track 2 — PARSE_FAILED 반복 강건성 검증 (대기 중)

Track 2는 신규 발행 샘플 실행 후 수행한다.

| 항목 | 상태 | 조건 |
|---|---|---|
| T2-1: TYPE_D 추가 샘플 확보 | ⏳ 대기 | 신규 발행 실행 필요 |
| T2-2: 신규 TYPE 즉시 실전 검증 | ⏳ 대기 | TYPE_A/B/C/E/UNKNOWN 발생 시 |

**TYPE_D 재발 시 확인 항목 (Axis B/C 정책 적용)**

```
IF parse_failed_type == TYPE_D
AND slot != unknown           ← Phase 19 T1-1 보강 후 확인
AND post_type != unknown      ← 동일
AND opener_pass == True        ← Phase 19 T1-3 보강 후 확인
AND criteria_1_pass == True    ← 동일
AND criteria_5_pass == True    ← 동일
AND source_structure_pass == True  ← 동일
→ closure = WARN, publish_blocked = false  ← Axis B/C 정책 적용
→ 30일 임계치 누적 관리 (현재 1건)
```

---

## 7. 미변경 항목 확인

Phase 19에서 변경 금지 항목 이상 없음:

| 항목 | 상태 |
|---|---|
| pick-angle opener 구조 | ✅ 미변경 |
| generic opener 금지 규칙 | ✅ 미변경 |
| PARSE_FAILED TYPE_A~E/UNKNOWN 분류 체계 | ✅ 미변경 (`_classify_parse_failed()` 로직 동일) |
| 실발행본 + 공개 URL 검증 원칙 | ✅ 미변경 |
| fallback WARN 허용 상한 원칙 | ✅ 미변경 |

---

## 8. 최종 판정

### Track 1 판정: **GO**

T1-1 / T1-2 / T1-3 모두 코드 반영 완료. 다음 PARSE_FAILED 발생 시 15개 필드 전체 기록 가능한 상태.

### Phase 19 현재 판정: **CONDITIONAL GO**

**근거**:
- Track 1 로그 보강 코드 반영 완료 ✅
- Track 2 (TYPE_D 추가 샘플 / 신규 TYPE 실전 검증) 신규 발행 대기 중 ⏳
- HOLD 사유 없음 (opener 회귀, 기준1/5 위반, TYPE_UNKNOWN 폭발 등 없음)

**GO 전환 조건**:
- 신규 발행에서 PARSE_FAILED 발생 시 보강된 15개 필드 로그 1건 이상 확인
- 또는 3회 이상 정상 발행에서 slot/post_type 정상 기록 확인
- TYPE_D 추가 샘플 확보 시 Axis B/C 정책 적용 일치 확인

---

## 9. Phase 19 → Phase 20 인계 포인트

| 우선순위 | 항목 | 상태 |
|---|---|---|
| 1 | Track 2 신규 발행 실행 — 보강 로그 실전 확인 | ⏳ 대기 |
| 2 | TYPE_D 추가 샘플 확보 — WARN 허용 반복 강건성 검증 | ⏳ 대기 |
| 3 | 신규 TYPE 발생 시 Axis C 규칙 즉시 적용 검증 | 조건부 |
| 4 | `criteria_1_pass` 간이 지표 → 정밀 지표 개선 검토 | 모니터링 |
