# PHASE19_KICKOFF_DEV_AGENT_FINAL

## 0. 문서 메타

- 작성일: 2026-03-20
- 대상 Phase: Phase 19
- 전제: Phase 18 Integrated Close-out 결과를 그대로 인계받는다.
- 성격: 구조 개편 Phase가 아니라 **운영 로그 보강 + `PARSE_FAILED` 반복 강건성 검증** Phase

---

## 1. 범위 선언

이번 Phase 19의 범위는 다음 2개 축으로 고정한다.

1. **운영 로그 보강**
2. **`PARSE_FAILED` 반복 강건성 검증**

이번 Phase 19에서 반드시 확인할 것:
- `slot/post_type=unknown` 현상 해소
- PICKS offset / locator 로그 추가
- `opener_pass`, `기준1_pass`, `기준5_pass`, `source_structure_pass` 직접 로그화
- `TYPE_D` 재발 시 동일 정책이 안정적으로 적용되는지 확인
- 신규 TYPE_A/B/C/E/UNKNOWN 발생 시 Axis C 규칙이 실전에서 유효한지 확인

이번 Phase 19에서 다루지 않는 것:
- Post2 opener 구조 재설계
- generic opener 금지 규칙 변경
- TYPE_A~E 분류 체계 재정의
- 스타일/UI/SEO/수익화 트랙
- 새 리서치/글쓰기 정책 개편

---

## 2. Phase 18 인계 요약

Phase 18 Close-out 결론:
- **운영 안정화 범위 기준 CONDITIONAL GO**
- opener 5/5 PASS
- generic opener 위반 0건
- 기준1 / 기준5 전건 PASS
- `fallback_used=True` 1건 (Post 187)
- `TYPE_D` 1건 실전 관측
- `publish_blocked=True` 0건

Phase 18에서 남긴 핵심 이월 5건:
1. `slot/post_type=unknown` 코드 보강
2. PICKS offset 로그 추가
3. 권장 필드 4종 직접 로그화
4. `TYPE_D` 추가 샘플 확보
5. TYPE_A/B/C/E/UNKNOWN 최초 발생 시 즉시 실전 검증

---

## 3. 작업 우선순위

### Track 1 — 로그 보강 (우선)

#### T1-1. `slot/post_type=unknown` 해소

목표:
- `_log_parse_failed_event()` 호출 시점에 slot / post_type 값이 정상 전달되도록 보강한다.

완료 기준:
- 신규 `PARSE_FAILED` 로그에서 `slot != unknown`
- 신규 `PARSE_FAILED` 로그에서 `post_type != unknown`
- 최소 1건 이상 샘플 로그로 확인

#### T1-2. PICKS offset / locator 로그 추가

목표:
- `failed_section_name` 또는 별도 필드에 PICKS 구간의 section locator / offset 정보를 남긴다.

완료 기준:
- TYPE_D 재발 또는 재현 로그에서 문제 구간 locator 확인 가능
- raw/normalized snapshot과 함께 offset 또는 section key 확인 가능

#### T1-3. 권장 필드 4종 직접 로그화

직접 로그화 대상:
- `opener_pass`
- `기준1_pass`
- `기준5_pass`
- `source_structure_pass`

완료 기준:
- 보고서 수동 판독 없이 로그만으로 4개 필드 상태를 읽을 수 있음
- 신규 샘플 최소 3건 이상에서 기록 확인

---

### Track 2 — `PARSE_FAILED` 반복 강건성 검증

#### T2-1. `TYPE_D` 추가 샘플 확보

목표:
- `TYPE_D`와 동일하거나 유사한 fallback 경로가 재발할 때 Axis B/C 정책이 일관 적용되는지 확인한다.

완료 기준:
- `TYPE_D` 추가 샘플 확보 또는 재현 테스트 결과 확보
- 각 케이스에 대해 아래 항목 기록:
  - `closure`
  - `publish_blocked`
  - `fallback_used`
  - `opener_pass`
  - `기준1_pass`
  - `기준5_pass`
  - `source_structure_pass`

정책 상한:
- `fallback_used=True` 케이스는 **PASS 승격 금지**
- 동일 유형 안정 재현 3회 전까지 **WARN 상한 유지**

#### T2-2. 신규 TYPE 즉시 실전 검증

대상:
- TYPE_A
- TYPE_B
- TYPE_C
- TYPE_E
- TYPE_UNKNOWN

실행 원칙:
- 새 TYPE 발생 시 Axis C 의사코드/대응 규칙을 즉시 적용한다.
- 허용/차단 결정과 실제 결과가 규칙과 일치하는지 문서화한다.

완료 기준:
- 신규 TYPE 발생 시 케이스별 검증 표 작성
- 규칙과 실제 동작 불일치 여부 판정
- 불일치 시 원인 분리 후 후속 수정안 제출

---

## 4. 불변 유지 항목

다음 항목은 이번 Phase 19에서 변경 금지다.

- pick-angle opener 구조
- generic opener 금지 규칙
- `PARSE_FAILED` TYPE_A~E / UNKNOWN 분류 체계
- 실발행본 + 공개 URL 검증 원칙
- fallback WARN 허용 상한 원칙

---

## 5. 보고서 작성 기준

이번 Phase 19 보고서는 반드시 **실제 발행본 / 공개 URL / 로그 증적** 기반으로 작성한다.

필수 포함 항목:
1. 신규 발행본 수
2. 공개 URL 수
3. `PARSE_FAILED` 발생 건수와 TYPE 분포
4. `slot/post_type=unknown` 해소 여부
5. PICKS offset 로그 반영 여부
6. 권장 필드 4종 직접 로그화 반영 여부
7. `TYPE_D` 재발 여부 및 정책 일치 여부
8. 신규 TYPE 발생 여부 및 대응 결과
9. opener PASS / 기준1 / 기준5 결과
10. 최종 판정: GO / CONDITIONAL GO / HOLD 중 1개만 선택

권장 포함 항목:
- raw / normalized snapshot 예시
- 대표 케이스 로그 전문
- 정책 일치 / 불일치 비교표

---

## 6. 판정 기준

### GO

다음을 모두 만족할 때만 GO:
- `slot/post_type=unknown` 해소 완료
- PICKS offset 로그 반영 완료
- 권장 필드 4종 직접 로그화 완료
- opener 반복 안정성 유지
- 기준1 / 기준5 위반 없음
- `TYPE_D` 추가 샘플 또는 반복 검증에서 정책 일치 확인
- 신규 TYPE 발생 시 규칙 불일치 없음

### CONDITIONAL GO

다음을 만족하면 CONDITIONAL GO:
- 발행 품질과 opener 안정성은 유지됨
- 기준1 / 기준5 위반 없음
- 로그 보강 일부 또는 반복 샘플 축적이 남아 있음
- HOLD 사유는 없음

### HOLD

다음 중 하나라도 해당 시 HOLD:
- generic opener 재오염 발생
- 기준1 또는 기준5 위반 발생
- `TYPE_UNKNOWN` 반복으로 차단 기준 도달
- 허용되면 안 되는 fallback 우회 발행 확인
- 로그 보강 실패로 핵심 원인 추적 불가

---

## 7. 제출 산출물

반드시 제출할 것:
1. Phase 19 실행 보고서 MD 1부
2. 로그 보강 전/후 비교표
3. 신규 샘플 또는 재현 케이스 표
4. 대표 `PARSE_FAILED` 케이스 로그 스냅샷
5. 최종 판정 및 다음 Phase 인계 항목

---

## 8. 최종 지시

이번 Phase 19의 목적은 구조 개선이 아니다.
핵심은 **운영 로그 가시성 확보**와 **`PARSE_FAILED` 정책의 반복 강건성 검증**이다.

따라서 우선순위는 아래 순서로 둔다.
1. 로그 보강
2. `TYPE_D` 반복 검증
3. 신규 TYPE 실전 대응 검증
4. 종합 판정

실행 후 실제 발행본, 공개 URL, 로그 증적과 함께 보고하라.
