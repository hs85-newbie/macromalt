# PHASE19_TRACK2_RUNTIME_VALIDATION_TEMPLATE.md

작성일: 2026-03-20  
대상: 개발 에이전트 전달용  
Phase: **Phase 19 — Track 2 실전 검증 템플릿**

---

## 0. 목적

이번 템플릿의 목적은 Phase 19 Track 1에서 반영한 로그 보강 3개 항목이 **실전 발행/실전 PARSE_FAILED 상황에서 실제로 정상 기록되는지** 검증하는 것이다.

Track 2의 핵심 범위:
1. **TYPE_D 추가 샘플 확보**
2. **신규 TYPE(A/B/C/E/UNKNOWN) 발생 시 Axis C 규칙 즉시 검증**
3. **15개 필드 보강 로그가 실제 런타임에서 정상 기록되는지 확인**
4. **Axis B/C 정책과 실제 closure / publish 판정이 일치하는지 검증**

이번 Track 2는 구조 개편이 아니다.
- pick-angle opener 구조 변경 금지
- generic opener 금지 규칙 변경 금지
- PARSE_FAILED TYPE_A~E/UNKNOWN 분류 체계 변경 금지
- fallback WARN 허용 상한 원칙 변경 금지

---

## 1. 입력 범위

### 1-1. 필수 수집 범위
- 신규 발행 샘플 실행 결과
- 실제 발행본
- 공개 URL
- PARSE_FAILED 로그 발생분
- 정상 발행 로그 발생분

### 1-2. 최소 실행 수
아래 둘 중 하나를 충족해야 한다.

- **우선 경로 A**: PARSE_FAILED 1건 이상 실제 발생
- **대체 경로 B**: 정상 발행 3건 이상에서 `slot/post_type` 포함 보강 로그 확인

### 1-3. 대표 케이스 우선순위
1. TYPE_D 재발 케이스
2. 신규 TYPE 최초 관측 케이스
3. 정상 발행 케이스

---

## 2. 실전 실행 수집표

| run_id | Post ID | slot | post_type | 공개 URL | 발행 여부 | parse_failed_type | fallback_used | closure | publish_blocked |
|---|---:|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |

---

## 3. 15개 필드 로그 검증

아래는 Phase 19 Track 1에서 보강한 필드를 포함한 실전 로그 검증표다.

| 항목 | 기대값 | 실제값 | 정상 여부 | 비고 |
|---|---|---|---|---|
| run_id | 존재 |  |  |  |
| slot | `unknown` 아님 |  |  |  |
| post_type | `post1` or `post2` |  |  |  |
| failure_type | TYPE명 또는 없음 |  |  |  |
| parse_stage | 존재 |  |  |  |
| failed_section_name | 존재 |  |  |  |
| raw_output_snapshot | 존재 |  |  |  |
| normalized_output_snapshot | 존재 |  |  |  |
| fallback_used | bool |  |  |  |
| publish_blocked | bool |  |  |  |
| picks_section_offset | -1 또는 숫자 |  |  |  |
| opener_pass | bool |  |  |  |
| criteria_1_pass | bool |  |  |  |
| criteria_5_pass | bool |  |  |  |
| source_structure_pass | bool |  |  |  |

### 3-1. 필수 판정
- `slot != unknown`
- `post_type != unknown`
- `raw_output_snapshot` / `normalized_output_snapshot` 존재
- `picks_section_offset` 기록됨
- 권장 필드 4종(`opener_pass`, `criteria_1_pass`, `criteria_5_pass`, `source_structure_pass`) 기록됨

---

## 4. TYPE_D 재발 검증

TYPE_D가 다시 발생했다면 아래 표를 채운다.

| 항목 | 결과 | 근거 |
|---|---|---|
| parse_failed_type = TYPE_D |  |  |
| slot != unknown |  |  |
| post_type != unknown |  |  |
| opener_pass = True |  |  |
| criteria_1_pass = True |  |  |
| criteria_5_pass = True |  |  |
| source_structure_pass = True |  |  |
| closure = WARN |  |  |
| publish_blocked = False |  |  |
| Axis B/C 정책 일치 |  |  |

### 4-1. TYPE_D 판정 규칙
다음 조건을 모두 만족하면 **정상 정책 적용**으로 본다.

```text
IF TYPE_D
AND slot != unknown
AND post_type != unknown
AND opener_pass == True
AND criteria_1_pass == True
AND criteria_5_pass == True
AND source_structure_pass == True
THEN closure = WARN
AND publish_blocked = false
```

### 4-2. 비정상 케이스
아래는 즉시 이슈로 기록한다.
- TYPE_D인데 `slot/post_type`가 여전히 unknown
- TYPE_D인데 권장 필드 4종 중 누락 존재
- TYPE_D인데 closure가 WARN이 아님
- TYPE_D인데 publish_blocked 판정이 Axis B/C 문서와 불일치

---

## 5. 신규 TYPE 실전 검증

TYPE_A/B/C/E/UNKNOWN 중 하나라도 최초 발생하면 아래 표를 채운다.

| 케이스 | parse_failed_type | 기대 closure | 기대 publish | 실제 closure | 실제 publish | Axis C 일치 여부 | 비고 |
|---|---|---|---|---|---|---|---|
| 샘플 1 |  |  |  |  |  |  |  |
| 샘플 2 |  |  |  |  |  |  |  |

### 5-1. 기대값 매핑
- TYPE_A → 기본 FAIL / 차단
- TYPE_B → FAIL 또는 WARN / reviser 보정 결과에 따라 분기
- TYPE_C → FAIL / 차단
- TYPE_D → WARN / 조건부 허용
- TYPE_E → FAIL 또는 WARN / normalized 완결성 점검
- TYPE_UNKNOWN → FAIL 검토 / 반복 시 차단 검토

---

## 6. 정상 발행 대체 검증

PARSE_FAILED가 발생하지 않은 경우에도 Track 2를 진행할 수 있다.
이 경우 정상 발행 3건 이상에서 아래를 확인한다.

| Post ID | slot 기록 | post_type 기록 | opener_pass | criteria_1_pass | criteria_5_pass | source_structure_pass | 공개 URL | 비고 |
|---:|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |

### 6-1. 대체 경로 성공 기준
- 정상 발행 3건 이상 확보
- `slot/post_type` 전건 정상 기록
- 권장 필드 4종 전건 기록
- 공개 URL 전건 확보
- opener 회귀 없음

---

## 7. opener 안정성 동시 확인

Track 2는 로그 검증뿐 아니라 opener 안정성도 함께 확인한다.

| Post ID | opener H3 | opener PASS | generic opener 위반 | 첫 문장 픽/섹터 포함 | macro recap 시작 여부 | 비고 |
|---:|---|---|---|---|---|---|
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

### 7-1. 실패 조건
- generic opener 재발
- opener 첫 문장에 픽/섹터 누락
- macro recap 시작 재발

---

## 8. 판정 기준

### 8-1. GO
- Track 1 보강 필드가 실전 로그에서 정상 기록됨
- PARSE_FAILED 또는 정상 발행 대체 경로 기준 충족
- opener 회귀 없음
- Axis B/C 정책과 실제 판정 불일치 없음
- 공개 URL 확보 실패 없음

### 8-2. CONDITIONAL GO
- 주요 보강은 실전 확인됐으나 표본 수가 아직 적음
- TYPE_D 또는 신규 TYPE 검증이 1건 수준에 머무름
- 운영 모니터링이 필요한 소수 이슈 존재

### 8-3. HOLD
- `slot/post_type=unknown`이 다시 발생
- 15개 필드 중 핵심 필드 누락
- opener 회귀 발생
- Axis B/C 정책과 실제 closure/publish 판정 불일치
- 공개 URL 확보 실패 또는 publish_blocked 필요한 케이스 오허용

---

## 9. 최종 보고 형식

### 9-1. 요약표
| 항목 | 결과 |
|---|---|
| 실행 샘플 수 |  |
| 실발행본 수 |  |
| 공개 URL 수 |  |
| PARSE_FAILED 발생 수 |  |
| TYPE_D 재발 수 |  |
| 신규 TYPE 발생 수 |  |
| slot unknown 재발 |  |
| post_type unknown 재발 |  |
| opener 회귀 |  |
| 최종 판정 |  |

### 9-2. 3줄 결론
1.  
2.  
3.  

### 9-3. 다음 단계
- GO면: **PHASE19_CLOSEOUT_TEMPLATE.md** 또는 통합 close-out 보고로 연결
- CONDITIONAL GO면: 추가 샘플 또는 Phase 20 모니터링 템플릿으로 연결
- HOLD면: Track 1 코드 재보정으로 롤백

---

## 10. 제출물

반드시 아래를 포함한다.
1. 실제 발행본 요약
2. 공개 URL
3. 실전 로그 스냅샷 또는 핵심 필드 캡처
4. 15개 필드 검증표
5. TYPE_D 또는 신규 TYPE 검증 결과
6. opener 안정성 확인표
7. 최종 판정
