# PHASE18_AXIS_D_REPEAT_STABILITY_TEMPLATE

## 목적

본 문서는 **Phase 18 Axis D — 반복 안정성 검증** 실행용 템플릿이다.
Axis D의 목적은 다음 4가지를 실제 추가 샘플 발행 기준으로 검증하는 것이다.

1. **Post2 opener 반복 안정성 유지 여부**
2. **generic opener 금지 규칙의 재오염 여부**
3. **TYPE_D 재발 시 opener 품질과 fallback 정책이 동시에 유지되는지 여부**
4. **Axis C에서 지정한 로그 보강 항목(`slot/post_type`, PICKS offset 등)의 반영 여부**

이번 축은 구조 개편 Phase가 아니다.
이번 축은 **운영 안정화 검증**이며, 실발행본 기준 반복 안정성을 확인하는 검증 축이다.

---

## 1. 범위

### 포함 범위
- 추가 샘플 발행본 수집
- opener/H3 반복 안정성 점검
- fallback_used / PARSE_FAILED 재발 여부 확인
- TYPE_D 재발 시 closure / publish 판정 일관성 점검
- 로그 보강 항목 반영 여부 확인

### 제외 범위
- pick-angle opener 구조 재설계
- TYPE_A~E 분류 체계 변경
- fallback 정책 방향 자체 재논의
- Post1/Post2 구조 대개편

---

## 2. 불변 유지 항목

이번 Axis D에서 아래 항목은 변경 금지다.

1. **pick-angle opener 구조 유지**
2. **generic opener 금지 규칙 유지**
3. **PARSE_FAILED TYPE_A~E 분류 체계 유지**
4. **Axis B fallback 정책 방향 유지**
5. **실발행본 + 공개 URL 기준 검증 원칙 유지**

---

## 3. 입력 자료

반드시 아래 자료를 함께 참조한다.

- `REPORT_PHASE17_POST2_OPENER_AND_PARSE_FAILED.md`
- `REPORT_PHASE18_AXIS_A_CLOSURE_COLLECTION.md`
- `REPORT_PHASE18_AXIS_B_FALLBACK_POLICY.md`
- `REPORT_PHASE18_AXIS_C_PARSE_FAILED_RESPONSE_RULES.md`

필요 시 함께 참조:
- Phase 18 kickoff 문서
- Axis A/B/C 실행 템플릿
- 최신 발행 로그 / verifier 로그 / reviser 로그 / PARSE_FAILED 구조화 로그

---

## 4. 샘플 수집 기준

### 최소 샘플 수
- **최소 5건**

### 권장 샘플 수
- **7~10건**

### 샘플 구성 원칙
- 가능한 한 최근 발행본 중심
- Post2 위주
- opener 구조가 실제로 생성된 케이스 우선
- 가능하면 서로 다른 슬롯/테마/종목군 포함
- fallback_used=True 케이스가 다시 발생하면 반드시 포함

---

## 5. 핵심 검증 질문

Axis D는 아래 질문에 답해야 한다.

1. opener는 추가 샘플에서도 계속 pick-angle 구조를 유지하는가?
2. generic opener 금지 규칙은 반복 발행에서도 유지되는가?
3. opener 첫 문장은 계속 메인 픽 또는 핵심 섹터를 직접 호출하는가?
4. fallback_used=True 또는 TYPE_D가 다시 발생할 경우에도 opener 품질은 유지되는가?
5. `slot/post_type=unknown` 문제는 해소되었는가?
6. PICKS 구간 offset 등 로그 보강 항목은 반영되었는가?
7. closure / publish / fallback 판정은 Axis B/C 정책과 일관되게 작동하는가?

---

## 6. 수집 표준 양식 (D-1)

아래 표를 샘플별로 채운다.

| 샘플 | Post ID | 발행 시각 | URL | opener H3 | opener 첫 문장 | 메인 픽/핵심 섹터 포함 | generic opener 금지 준수 | opener PASS | 기준1 PASS | 기준5 PASS | source PASS | verifier closure | fallback_used | parse_failed_type | publish_blocked | slot 정상 기록 | post_type 정상 기록 | PICKS offset 기록 | 비고 |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

## 7. opener 반복 안정성 점검 (D-2)

샘플 전체 기준으로 아래 항목을 집계한다.

### 필수 집계 항목
- opener PASS 비율
- generic opener 금지 준수 비율
- opener 첫 문장 내 메인 픽/핵심 섹터 포함 비율
- opener 첫 문장 macro recap 시작 비율
- opener H3 패턴 다양성 여부
- opener와 메인 픽 섹션 연결 자연성 여부

### 집계 표

| 항목 | 결과 | 비율 | 비고 |
|---|---:|---:|---|
| opener PASS |  |  |  |
| generic opener 금지 준수 |  |  |  |
| opener 첫 문장 픽/섹터 포함 |  |  |  |
| macro recap 시작 0건 여부 |  |  |  |
| H3 다양성 확보 |  |  |  |
| opener→메인픽 연결 자연성 |  |  |  |

---

## 8. TYPE_D / fallback 재발 감시 (D-3)

재발 여부를 별도로 기록한다.

### 재발 집계 표

| 항목 | 건수 | Post ID | 판정 |
|---|---:|---|---|
| fallback_used=True 재발 |  |  |  |
| TYPE_D 재발 |  |  |  |
| TYPE_UNKNOWN 발생 |  |  |  |
| publish_blocked=True 발생 |  |  |  |

### 해석 원칙
- **TYPE_D 재발 없음**: 정책 유지 가능성 확인
- **TYPE_D 재발 있음 + opener 유지**: Axis B/C 정책 실전 안정성 강화
- **TYPE_D 재발 있음 + opener 붕괴**: Axis B/C 정책 재점검 필요
- **TYPE_UNKNOWN 1건**: WARN 검토
- **TYPE_UNKNOWN 2건 이상**: 차단 검토 및 분류 체계 확장 필요

---

## 9. 로그 보강 반영 점검 (D-4)

Axis C 인계 항목이 실제 반영되었는지 확인한다.

### 점검 항목
1. `slot`이 더 이상 `unknown`으로 남지 않는가
2. `post_type`이 더 이상 `unknown`으로 남지 않는가
3. PICKS 구간 offset이 기록되는가
4. opener_pass / 기준1_pass / 기준5_pass / source_pass가 직접 로그에 남는가
5. parse_stage / failed_section_name / raw/normalized snapshot 경로가 유지되는가

### 점검 표

| 항목 | 상태 | 적용 방식 | 비고 |
|---|---|---|---|
| slot 정상 기록 |  |  |  |
| post_type 정상 기록 |  |  |  |
| PICKS offset 기록 |  |  |  |
| opener_pass 직접 로그화 |  |  |  |
| 기준1/기준5/source 직접 로그화 |  |  |  |
| parse snapshot 경로 유지 |  |  |  |

---

## 10. 예외 케이스 상세 기록 (D-5)

PASS가 아닌 샘플은 반드시 개별 섹션으로 남긴다.

### 기록 양식

#### Case D-5-X
- Post ID:
- 발행 시각:
- URL:
- opener H3:
- opener 첫 2~3문장:
- verifier closure:
- fallback_used:
- parse_failed_type:
- publish_blocked:
- 발생 이슈:
- Axis B/C 정책과의 일치 여부:
- 필요한 후속 조치:

---

## 11. 판정 기준 (D-6)

### GO
아래를 모두 만족하면 GO 가능.

1. opener PASS 100%
2. generic opener 금지 위반 0건
3. opener 첫 문장 픽/섹터 포함 100%
4. TYPE_UNKNOWN 0건
5. fallback/TYPE_D 재발 시에도 Axis B/C 정책대로 일관 처리
6. `slot/post_type=unknown` 해소 완료
7. 로그 보강 핵심 항목 반영 완료

### CONDITIONAL GO
아래 중 일부가 남아 있으면 CONDITIONAL GO.

- opener는 안정적이지만 로그 보강 일부 미완
- TYPE_D 재발 표본이 부족하여 정책 강건성 추가 확인 필요
- fallback은 통제되지만 승격/차단 경계의 추가 샘플 필요

### HOLD
아래 중 하나라도 해당하면 HOLD.

- generic opener 재발
- opener 첫 문장 픽/섹터 누락 반복
- 기준1 또는 기준5 위반 발행 발생
- TYPE_UNKNOWN 2건 이상
- fallback 경로에서 구조/출처 손실 동반
- publish_blocked가 필요한 케이스가 허용 발행됨

---

## 12. 최종 요약 (D-7)

아래 형식으로 최종 요약을 작성한다.

### D-7 요약
- 샘플 수:
- opener PASS:
- generic opener 위반:
- fallback 재발:
- TYPE_D 재발:
- TYPE_UNKNOWN:
- 로그 보강 완료 항목:
- 미완료 항목:
- 최종 판정: GO / CONDITIONAL GO / HOLD
- 다음 인계:

---

## 13. 제출 산출물

반드시 아래 산출물을 제출한다.

1. `REPORT_PHASE18_AXIS_D_REPEAT_STABILITY.md`
2. 샘플별 발행 본문 또는 최소 opener 전문
3. 발행 URL 목록
4. 예외 케이스 상세 기록
5. 로그 보강 반영 여부 표
6. 최종 판정 및 다음 단계 제안

---

## 14. 다음 단계 자동 연결 규칙

이번 Axis D 결과가 아래 조건을 만족하면, 별도 확인 없이 다음 템플릿으로 바로 진행한다.

### 자동 다음 단계 조건
- 최종 판정이 **GO** 또는 **CONDITIONAL GO**
- Axis D 보고서가 실발행본 기준으로 작성됨
- opener 반복 안정성 결과가 명확함
- fallback / TYPE_D / 로그 보강 상태가 문서에 정리됨

### 다음 자동 생성 대상
- `PHASE18_INTEGRATED_CLOSEOUT_TEMPLATE.md`

---

## 15. 작성 지시

리포트는 반드시 **실발행본 기준**으로 작성한다.
URL만 나열하지 말고, 보고서 자체만으로 검증 가능하도록 핵심 본문을 포함한다.
PASS만 적지 말고, 예외 케이스가 있으면 반드시 케이스별로 남긴다.
최종 판정은 과장하지 말고, 해결된 것과 남은 것을 분리해서 쓴다.
