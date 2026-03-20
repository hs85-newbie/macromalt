# PHASE19_NORMAL_PATH_PASS_FIELDS_LOGGING_DEV_INSTRUCTION.md

작성일: 2026-03-20  
Phase: **Phase 19 — 정상 발행 경로 4개 pass 필드 로그화 개발 지시문**  
상태: 실행 지시용 최종본

---

## 0. 목적

이번 작업의 목적은 **정상 발행 경로에서도 아래 4개 pass 필드를 운영 로그에 직접 남기도록 보강**하는 것이다.

대상 4개 필드:
1. `opener_pass`
2. `criteria_1_pass`
3. `criteria_5_pass`
4. `source_structure_pass`

현재 구조에서는 위 4개 필드가 `PARSE_FAILED` 발생 시 `_log_parse_failed_event()` 경로에서만 기록된다.
그 결과, Phase 19는 실제 발행 4건 / 공개 URL 4건 / slot/post_type 정상화 / final_status=GO 2회 연속까지 확보했음에도,
정상 발행 경로에서의 **직접 로그 증적 부족** 때문에 최종 GO 전환이 지연되고 있다.

이번 작업은 이 구조적 제약을 제거하기 위한 것이다.

---

## 1. 왜 지금 이 작업을 하는가

현재 확인된 상태:
- 실발행 4건과 공개 URL 4건은 이미 확보됨
- `slot != unknown`, `post_type != unknown` 문제는 해소됨
- generic opener 재발 없음
- HOLD 사유 없음
- 그러나 Route B 최종 충족을 막는 유일한 잔여 조건은 정상 발행 경로에서 4개 pass 필드가 로그로 남지 않는 점이다

즉, 이번 작업은 새 기능 추가가 아니라 **운영 증적 완성**이다.

---

## 2. 이번 작업의 성격

이번 작업은 다음 성격으로 한정한다.

- **운영 로그 보강**
- **정상 발행 경로 증적화**
- **Route B 최종 GO 전환 가능 상태 만들기**

이번 작업은 아래를 포함하지 않는다.

- opener 구조 재수정
- verifier/reviser 기준 재설계
- fallback 정책 변경
- PARSE_FAILED TYPE 체계 변경
- 발행 본문 스타일 수정
- 리서치 소스 정책 변경

---

## 3. 불변 유지 항목

아래 항목은 이번 작업에서 변경 금지다.

1. pick-angle opener 구조
2. generic opener 금지 규칙
3. Axis B fallback WARN 허용 정책
4. Axis C TYPE_A~TYPE_UNKNOWN 대응 규칙
5. `slot`, `post_type`, `picks_section_offset` 기존 로그 구조
6. 공개 URL 기준 검증 원칙
7. 기준1 / 기준5 기존 판정 원칙

---

## 4. 변경 목표

정상 발행 경로에서 아래 조건을 만족해야 한다.

### 4-1. 정상 경로 로그에 4개 필드 직접 기록
정상 발행 시점에도 아래가 반드시 로그에 남아야 한다.

- `opener_pass`
- `criteria_1_pass`
- `criteria_5_pass`
- `source_structure_pass`

### 4-2. 기록 위치 통일
가능하면 `PARSE_FAILED` 로그와 정상 발행 로그가 **같은 naming / 같은 bool 의미 / 같은 계산 방식**을 유지하도록 통일한다.

### 4-3. 계산 중복 최소화
현재 이미 계산 중인 필드는 재활용하고,
불필요한 중복 계산이나 규칙 불일치가 생기지 않도록 한다.

### 4-4. run 단위 확인 가능성 확보
다음 generator 실행 1회만으로도 아래가 즉시 확인 가능해야 한다.

- slot
- post_type
- 4개 pass 필드
- final_status
- 공개 URL

---

## 5. 구현 지시

### 5-1. 로그 스키마 확장
정상 발행 경로 로그에 아래 4개 필드를 추가하라.

```text
opener_pass
criteria_1_pass
criteria_5_pass
source_structure_pass
```

### 5-2. 값 정의 고정
값 정의는 기존 Phase 19 Track 1 정의를 그대로 따른다.

- `opener_pass`
  - pick-angle regex 만족
  - 금지 opener 6종 부재
- `criteria_5_pass`
  - 권유성 표현 6종 부재
- `criteria_1_pass`
  - 시점 혼합 간이 탐지 기준 PASS
- `source_structure_pass`
  - 참고 출처 / 리서치 / 뉴스 / 구조 블록 존재

주의:
- 이번 작업에서 기준식 자체를 다시 바꾸지 마라.
- 기존 계산과 로그 기록 위치만 맞춰라.

### 5-3. 기록 타이밍
아래 두 시점 중 최소 1곳, 가능하면 둘 다 고려하라.

권장 시점:
1. verifier 최종 판정 직후
2. publish 직전 또는 publish 직후 최종 summary 로그 작성 시점

원칙:
- 실제 발행 성공/실패와 함께 남겨야 한다.
- 최종 URL 확보 여부와 함께 묶어 볼 수 있어야 한다.

### 5-4. Post1 / Post2 공통 적용
정상 경로 4개 필드 로그화는 Post1 / Post2 모두에 동일하게 적용한다.

필수:
- `post_type=post1`에서도 기록
- `post_type=post2`에서도 기록
- slot도 함께 기록

### 5-5. 로그 포맷 예시
최소 예시는 아래와 같다.

```json
{
  "run_id": "20260320_xxxxxx",
  "slot": "default",
  "post_type": "post2",
  "final_status": "GO",
  "public_url": "https://macromalt.com/...",
  "opener_pass": true,
  "criteria_1_pass": true,
  "criteria_5_pass": true,
  "source_structure_pass": true
}
```

### 5-6. 기존 PARSE_FAILED 경로와 충돌 금지
- `_log_parse_failed_event()` 기존 15개 필드 구조는 유지한다.
- 동일 필드명이 PARSE_FAILED 경로와 정상 경로에서 서로 다른 의미를 가지면 안 된다.
- bool 의미가 일치해야 한다.

---

## 6. 권장 구현 방식

아래 중 하나를 택해라.

### 권장안 A
**공통 summary payload 함수**를 만든다.

예:
- `_build_quality_log_payload(...)`
- 정상 경로 / PARSE_FAILED 경로 모두 이 함수를 통해 공통 필드를 생성
- 경로별 추가 필드만 개별 append

장점:
- 정의 불일치 방지
- 향후 Phase 20 이후에도 재사용 가능
- Route A / B 증적 포맷 통일 가능

### 허용안 B
현재 정상 경로 로그 작성부에 4개 필드만 직접 추가한다.

장점:
- 변경 폭이 작음
- 빠른 반영 가능

단점:
- 추후 동일 필드 의미 불일치 위험 존재

판단:
- 시간이 허용되면 권장안 A
- 빠른 종결이 최우선이면 허용안 B

---

## 7. 금지 사항

아래는 이번 작업에서 하지 마라.

1. `PARSE_FAILED`가 발생해야만 증적이 남는 구조를 유지한 채 종료 판단하지 말 것
2. 정상 경로에서 필드를 계산만 하고 로그에 남기지 않는 상태를 그대로 두지 말 것
3. Route B 판정 기준을 다시 완화하지 말 것
4. “정상 발행이니까 로그 없어도 된다”는 식으로 보고하지 말 것
5. opener / 기준1 / 기준5 / 출처 구조 판정식을 이번 작업 범위에서 임의로 바꾸지 말 것
6. 공개 URL 없이 GO 주장하지 말 것

---

## 8. 완료 기준

이번 작업은 아래를 모두 만족해야 완료로 본다.

### 코드 완료 기준
- 정상 발행 경로에 4개 pass 필드 로그 반영 완료
- Post1 / Post2 모두 적용 완료
- 기존 PARSE_FAILED 로그와 의미 충돌 없음

### 실행 완료 기준
- 신규 run 1회 이상 수행
- 실발행본 및 공개 URL 확보
- 정상 발행 로그에서 아래 확인
  - `slot != unknown`
  - `post_type != unknown`
  - `opener_pass`
  - `criteria_1_pass`
  - `criteria_5_pass`
  - `source_structure_pass`

### 보고 완료 기준
아래를 포함한 보고서 제출:
1. 변경 파일 목록
2. 수정 위치 요약
3. 로그 before / after 비교
4. 신규 run_id
5. 공개 URL
6. 대표 로그 2건 이상
7. 최종 판정
   - GO / CONDITIONAL GO / HOLD

---

## 9. 권장 테스트 시나리오

### 시나리오 A — 정상 발행 run
- Post1 / Post2 모두 정상 발행
- final_status=GO
- 4개 pass 필드 로그 확인
- 공개 URL 확인

### 시나리오 B — opener 유지 확인
- Post2 opener가 pick-angle 유지
- generic opener 재발 없음
- `opener_pass=True` 로그와 실제 본문 일치 확인

### 시나리오 C — 기준1 / 기준5 일치 확인
- `criteria_1_pass=True`
- `criteria_5_pass=True`
- 실제 발행 본문 수동 확인과 로그 판정이 충돌 없는지 확인

---

## 10. 산출물

반드시 아래를 제출하라.

1. **개발 반영 보고서 MD**
   - 파일명 예: `REPORT_PHASE19_NORMAL_PATH_PASS_FIELDS_LOGGING.md`

2. **신규 run 검증 보고 MD**
   - 파일명 예: `REPORT_PHASE19_ROUTE_B_COMPLETION.md`

3. **대표 로그 스냅샷**
   - Post1 1건
   - Post2 1건

4. **최종 판정**
   - GO / CONDITIONAL GO / HOLD

---

## 11. 최종 목표

이번 작업의 최종 목표는 단순 로그 추가가 아니다.

**정상 운영 경로 자체를 증적화해서, 오류 발생을 기다리지 않고도 Phase 19를 닫을 수 있는 상태를 만드는 것**이다.

즉:
- Route A는 보조 경로로 유지
- Route B를 정상 운영 증적으로 완결
- Phase 19 최종 GO 전환을 가능하게 할 것

이 목표에 맞게 구현하고 보고하라.
