# REPORT_PHASE18_INTEGRATED_CLOSEOUT.md

## 0. 문서 메타

- **작성일**: 2026-03-20
- **Phase**: Phase 18 — Integrated Close-out
- **기준 문서**:
  - `REPORT_PHASE18_AXIS_A_CLOSURE_COLLECTION.md`
  - `REPORT_PHASE18_AXIS_B_FALLBACK_POLICY.md`
  - `REPORT_PHASE18_AXIS_C_PARSE_FAILED_RESPONSE_RULES.md`
  - `REPORT_PHASE18_AXIS_D_REPEAT_STABILITY.md`
  - Phase 17 보고서: `REPORT_PHASE17_POST2_OPENER_AND_PARSE_FAILED.md`

---

## 1. Close-out 범위 선언

이번 Phase 18의 범위는 **구조 개편이 아니라 운영 안정화**다.

이번 Close-out에서 판정하는 것:
1. closure FAIL/WARN 케이스의 원인 분해가 충분히 끝났는가
2. fallback 허용/차단 정책이 운영 가능한 수준으로 정리되었는가
3. `PARSE_FAILED` 유형별 대응 규칙과 closure 매핑이 문서화되었는가
4. opener 반복 안정성이 실제 발행본 기준으로 유지되는가

이번 Close-out에서 다루지 않는 것:
- Post2 opener 구조 재설계
- generic opener 금지 규칙 자체 변경
- TYPE_A~E 분류 체계 재정의
- 스타일/UI/SEO/수익화 트랙

---

## 2. 입력 자료 요약

### 2-1. 사용 보고서 목록

| 축 | 문서 | 판정 | 핵심 결과 |
|---|---|---|---|
| Axis A | `REPORT_PHASE18_AXIS_A_CLOSURE_COLLECTION.md` | **CONDITIONAL GO** | closure FAIL/WARN 4건 수집·분류 완료. C2(reviser 미수렴) 3건 공통 패턴 확인. |
| Axis B | `REPORT_PHASE18_AXIS_B_FALLBACK_POLICY.md` | **CONDITIONAL GO** | Post 187 기준 WARN 허용 정책 7개 조건 명문화. TYPE_D 추가 샘플 필요. |
| Axis C | `REPORT_PHASE18_AXIS_C_PARSE_FAILED_RESPONSE_RULES.md` | **CONDITIONAL GO** | TYPE_A~UNKNOWN 전 유형 대응 규칙 문서화. closure 매핑·의사코드 완성. |
| Axis D | `REPORT_PHASE18_AXIS_D_REPEAT_STABILITY.md` | **CONDITIONAL GO** | opener 5/5 PASS. generic 위반 0건. TYPE_D 정책 1회 적용 일치. |

### 2-2. 실발행 검증 범위

| 항목 | 값 |
|---|---|
| 실발행본 수 | **5건** (Post 177 / 179 / 183 / 185 / 187) |
| 공개 URL 확보 수 | **5건** (전건 확보) |
| 검증 기준 | 실제 발행본 + 공개 URL 기준 |
| 기준1 점검 | **PASS** — 5건 전체, 최근 7일 중심 자료 구성. 30일 초과 근거 단독 사용 없음. |
| 기준5 점검 | **PASS** — 5건 전체, 권유성 표현("매수", "유망", "담아야 한다") 0건. |

---

## 3. Axis A~D 통합 요약

### 3-1. 축별 판정 요약 표

| 축 | 최종 판정 | 핵심 성과 | 미완 항목 | 다음 단계 필요 |
|---|---|---|---|---|
| **Axis A** | CONDITIONAL GO | closure FAIL/WARN 원인 4종(C1~C4) 분류 완료. C2(reviser 미수렴) 3건 공통 패턴 특정. 즉시 수정 대상 없음 확인. | 미해소 이슈 유형 세분화 로그 미구축. "Post2 기준 별도 FAIL" 로직 세부 미확인. | 추가 샘플에서 C1/C2 재분류 데이터 필요 |
| **Axis B** | CONDITIONAL GO | fallback 허용 7개 AND 조건 명문화. POST 187 WARN 허용 적용 확인. 차단 조건 7개 명시. closure 매핑 5단계 정리. | TYPE_D 추가 샘플 1건만 관측. WARN→PASS 승격 조건 미검증(3회 안정 재현 미달). | TYPE_D 재발 시 동일 정책 재적용 확인 필요 |
| **Axis C** | CONDITIONAL GO | TYPE_A~UNKNOWN 전 6유형 대응 규칙 문서화. closure 자동 부여 매핑표. 의사코드 3종. publish 허용/차단 결정표 완성. | 실전 관측 TYPE_D 1건만. TYPE_A/B/C/E/UNKNOWN 미관측(예방적 규칙). slot/post_type 로그 보강 미완. | 신규 TYPE 발생 시 해당 유형 규칙 실전 검증 필요 |
| **Axis D** | CONDITIONAL GO | opener 5/5 PASS (100%). generic 위반 0건. TYPE_D fallback 케이스에서 Axis B/C 정책 일관 적용. 기준1/5 5건 전체 PASS. | slot/post_type=unknown 코드 보강 미완. PICKS offset 미추가. 권장 필드 4종 직접 로그화 미완. TYPE_D 추가 샘플 없음. | 로그 보강 후 신규 발행 재검증 필요 |

### 3-2. 축별 핵심 결론 1문장 요약

- **Axis A**: closure FAIL/WARN의 주요 원인은 reviser 미수렴(C2) 3건이며, 발행 품질 직접 영향은 없으나 이슈 유형 세분화 로그가 필요하다.
- **Axis B**: fallback은 7개 AND 조건 충족 시 WARN 기반으로 제한 허용하며, 기준 위반 또는 구조 손실 동반 시 차단하는 정책이 문서화되었다.
- **Axis C**: PARSE_FAILED TYPE_A~UNKNOWN 전 유형에 대한 대응 규칙과 closure 매핑이 완성되었으나, 실전 관측은 TYPE_D 1건에 한정된다.
- **Axis D**: opener 반복 안정성은 5/5 (100%) PASS이며, TYPE_D fallback 케이스에서도 pick-angle 구조가 완전 유지되었다.

---

## 4. 핵심 검수 기준 통합 대조

### 4-1. 운영 정책 기준 대조

| 항목 | 결과 | 근거 |
|---|---|---|
| 실제 발행본 기준 검증 수행 | ✅ | 5건 전체 실발행본 기준 검증. 초안·URL·본문 전문 포함. |
| 공개 URL 확보 | ✅ 5/5 | Post 177~187 공개 URL 5건 전건 확보. |
| 기준1 위반 반복 없음 | ✅ 0건 | 5건 발행본 기준 시점 혼합 위반 관찰 없음. (Post 187은 fallback 경로 사용했으나 기준1 유지.) |
| 기준5 위반 반복 없음 | ✅ 0건 | 5건 발행본 기준 권유성 표현 재등장 없음. |
| source/date 반영 유지 | ✅ | 5건 전체 참고 출처 블록(증권사 리서치/뉴스/기타) 정상 포함. |
| 숫자-논리 연결 유지 | ✅ | 각 발행본에 매출/영업이익/PER/부채비율 등 구체 수치 포함. 수치-논리 연결 구조 유지. |
| opener 반복 안정성 유지 | ✅ 100% | pick-angle 5/5. generic 위반 0건. macro recap 0건. |
| fallback 경로 통제 가능 | ✅ | Axis B 정책 명문화. Post 187 WARN 허용 적용 일치. 30일 임계치 3건 미달(현재 1건). |
| `PARSE_FAILED` 대응 규칙 문서화 | ✅ | Axis C — TYPE_A~UNKNOWN 전 유형 대응 규칙·의사코드·매핑표 완성. |

### 4-2. opener 안정성 요약

| 항목 | 결과 | 비고 |
|---|---|---|
| opener PASS 비율 | **5/5 (100%)** | Phase 17 pick-angle 구조 전혀 흔들리지 않음. |
| generic opener 위반 | **0건** | "오늘 이 테마를 보는 이유" 등 6종 금지 패턴 0건. |
| opener 첫 문장 픽/섹터 포함 | **5/5 (100%)** | 픽명이 첫 단어 또는 첫 문장 내 직접 명시. |
| macro recap 시작 | **0건** | 거시 배경 재서술로 시작한 opener 없음. |
| H3 다양성 | 4종 사용 (양호) | 삼성전자/XLE/SK이노베이션/S-Oil. S-Oil 2건은 서로 다른 슬롯. |
| fallback 케이스 opener 유지 | **✅ Post 187** | TYPE_D fallback 경로에서도 "왜 지금 S-Oil인가" pick-angle 완전 유지. |

### 4-3. fallback / PARSE_FAILED 요약

| 항목 | 결과 | 비고 |
|---|---|---|
| fallback_used=True 총건수 | **1건** | Post 187. 30일 임계치(3건) 미달. |
| 대표 fallback 케이스 | Post 187 (TYPE_D, WARN 허용) | F1+F2+F5 복합 분류. 품질 기준 전부 PASS. |
| `TYPE_D` 관측 수 | **1건** | PICKS 주석 구간 판독 실패 → JSON parse 불가 |
| `TYPE_UNKNOWN` 관측 수 | **0건** | 차단 임계치(2건) 미도달. |
| publish_blocked=True 발생 | **0건** | 5건 전건 정상 발행. |
| Axis B/C 정책 일치 여부 | **✅ 일치** | TYPE_D WARN 허용 의사코드 조건과 Post 187 실전 결과 완전 일치. |

---

## 5. 통합 해석

### 5-1. 이번 Phase 18에서 달성된 것

- **closure 원인 분리 완료**: FAIL/WARN 4건의 원인이 C1~C4로 분류됨. 공통 패턴(C2 reviser 미수렴 3건)이 특정됨. 발행 품질 직접 영향도 Low 확인.
- **fallback 정책 명문화 완료**: WARN 허용 7개 AND 조건 + 차단 7개 조건 + closure 매핑 5단계 + 운영 원칙 4개가 Axis B에 문서화됨. 운영자 단독 판단 가능 체계 구축.
- **PARSE_FAILED 대응 규칙 문서화 완료**: TYPE_A~UNKNOWN 전 6유형의 정의·탐지 조건·허용/차단 기준·재발 승격 규칙이 Axis C에 문서화됨. 의사코드 3종으로 코드 반영 준비 가능.
- **opener 반복 안정성 확인**: 5건 발행본 기준 opener PASS 100%. generic 위반 0건. TYPE_D fallback 경로에서도 opener 구조 완전 유지. Phase 17이 달성한 pick-angle 구조가 Phase 18 기간 내 회귀 없음.

### 5-2. 이번 Phase 18에서 여전히 남은 것

- **`slot/post_type=unknown` 미해소**: PARSE_FAILED 시 `_log_parse_failed_event()` 호출 시점에 slot/post_type 값이 정상 전달되지 않는 현상 미수정. 코드 보강 필요 (1순위).
- **PICKS 구간 offset/locator 미추가**: TYPE_D 재발 시 구간 정밀 분석을 위한 section locator 로그 미추가.
- **권장 로그 필드 4종 미직접 기록화**: opener_pass / 기준1_pass / 기준5_pass / source_structure_pass가 보고서 수동 확인으로만 검증 가능한 상태.
- **TYPE_D 추가 샘플 미확보**: WARN 허용 정책의 반복 강건성이 1건 기준으로만 확인됨. 3회 안정 재현 기준 WARN→PASS 승격 조건 검토 미개시.
- **TYPE_A/B/C/E/UNKNOWN 실전 관측 없음**: 예방적 규칙으로 문서화되었으나, 신규 유형 발생 시 규칙 실전 검증이 필요함.

### 5-3. 해석 충돌 방지 문장

> 이번 Phase 18은 **운영 안정화 범위 기준**으로 판정한다. 구조 개편이 아니라, closure / fallback / `PARSE_FAILED` / opener 반복 안정성의 운영 가능성을 실제 발행본 기준으로 확인한 단계다.

> 따라서 이번 판정은 "전체 시스템이 완전 무결하다"는 의미가 아니라, **운영 정책에 따른 발행 가능성과 모니터링 대상이 분리된 상태**를 공식화하는 것이다.

---

## 6. 남은 이슈 및 모니터링 항목

### 6-1. 코드 보강 / 즉시 처리 필요 항목

| 항목 | 필요 여부 | 이유 | 우선순위 |
|---|---|---|---|
| `slot/post_type=unknown` 보강 | **필요** | PARSE_FAILED 재발 시 슬롯별 분포 분석 불가. 핵심 로그 필드 미기록 상태. | **1순위** |
| PICKS offset 로그 추가 | **필요** | TYPE_D 재발 시 구간 정밀 분석 가능성 확보. | 2순위 |
| opener_pass / 기준1_pass / 기준5_pass / source_pass 직접 로그화 | **권장** | 현재는 수동 확인. 자동 검수·집계 체계 준비. | 3순위 |
| TYPE_D 추가 샘플 확보 | **권장** | WARN 허용 정책 반복 강건성 검증. WARN→PASS 승격 조건 검토 기반 확보. | 4순위 |
| TYPE_UNKNOWN 발생 시 차단 플로우 재검증 | 발생 시 | 현재 미관측. 발생 즉시 Axis C 의사코드 차단 플로우 적용 후 검증. | 조건부 |

### 6-2. 운영 모니터링 유지 항목

| 항목 | 현재 상태 | 모니터링 기준 |
|---|---|---|
| TYPE_D 재발 여부 | 1건 관측 (30일 임계치 3건 미달) | 30일 내 3건+ 시 WARN → FAIL 승격 |
| TYPE_UNKNOWN 발생 여부 | 0건 (차단 임계치 2건 미달) | 2건+ 시 즉시 차단 검토 + 분류 체계 확장 |
| fallback 30일 누적 건수 | 1건 | 3건+ 시 파이프라인 구조 점검 착수 |
| closure FAIL/WARN 재발 패턴 | FAIL 2건 / WARN 2건 (C2 reviser 미수렴 공통) | 동일 원인 3건+ 누적 시 reviser 규칙 보강 착수 |
| opener 재오염 여부 | 0건 (Phase 17 이후 회귀 없음) | generic opener 재등장 1건이라도 즉시 원인 분리 |

---

## 7. 최종 판정 표

### 7-1. GO / CONDITIONAL GO / HOLD 대조

| 판정 | 해당 여부 | 근거 |
|---|---|---|
| **GO** | ❌ 미해당 | slot/post_type 로그 보강 미완. TYPE_D 추가 샘플(3회 안정 재현) 미달. 권장 필드 직접 로그화 미완. |
| **CONDITIONAL GO** | ✅ **해당** | 발행 품질 기준 위반 없음. opener 100% PASS. fallback 정책 명문화 완료. PARSE_FAILED 규칙 문서화 완료. 미완은 로그 보강 및 추가 샘플 수준으로 HOLD 사유 아님. |
| **HOLD** | ❌ 미해당 | generic opener 재발 없음. 기준1/5 위반 없음. TYPE_UNKNOWN 0건. publish_blocked 필요 케이스 우회 발행 없음. |

### 7-2. 최종 판정 문구

> **Phase 18 운영 안정화 범위 기준 CONDITIONAL GO**
>
> 근거:
> - 실제 발행본 기준으로 opener 안정성과 fallback / `PARSE_FAILED` 정책 적용은 확인되었다.
> - 다만 `slot/post_type=unknown`, PICKS offset, 직접 로그화, TYPE_D 추가 샘플 등 운영 보강 항목이 남아 있다.
> - 즉시 HOLD 사유는 없으나, 다음 Phase에서 로그 보강 및 반복 검증을 이어받아야 한다.

---

## 8. Phase 18 Close-out 선언

> **Phase 18은 운영 안정화 범위 기준 CONDITIONAL GO로 종료한다.**
>
> Axis A~D의 핵심 목적은 달성했으나, 일부 로그 보강과 반복 샘플 축적이 남아 있어 다음 Phase에서 이어받는다.
>
> 현재 상태는 발행 품질을 저해하는 HOLD 사유가 아니라, 운영 모니터링 및 정책 강건성 보강 사유로 본다.

### Phase 18 달성 항목 (4건)

| # | 항목 | 상태 |
|---|---|---|
| 1 | closure FAIL/WARN 원인 분리 | ✅ 완료 (C1~C4 분류, C2 공통 패턴 특정) |
| 2 | fallback 발행 경로 정책 명문화 | ✅ 완료 (허용 7조건, 차단 7조건, 매핑 5단계) |
| 3 | PARSE_FAILED 유형별 대응 규칙 문서화 | ✅ 완료 (TYPE_A~UNKNOWN, 의사코드 3종) |
| 4 | opener 반복 안정성 확인 | ✅ 완료 (5/5 PASS, 회귀 0건) |

### Phase 18 이월 항목 (5건 → Phase 19)

| # | 항목 | 이월 사유 |
|---|---|---|
| 1 | `slot/post_type=unknown` 코드 보강 | 신규 발행 없어 검증 불가 |
| 2 | PICKS offset 로그 추가 | 코드 반영 미진행 |
| 3 | 권장 필드 4종 직접 로그화 | 코드 반영 미진행 |
| 4 | TYPE_D 추가 샘플 확보 | 1건만 관측, 반복 강건성 미달 |
| 5 | TYPE_A/B/C/E/UNKNOWN 실전 검증 | 미발생 유형 — 발생 시 즉시 검증 |

---

## 9. Phase 19 인계 포인트

### 9-1. 인계 항목 (우선순위 정렬)

| 우선순위 | 항목 | 설명 |
|---|---|---|
| **1** | `slot/post_type=unknown` 해소 | `_log_parse_failed_event()` 호출 시점에 slot/post_type 값 정상 전달 코드 수정 |
| **2** | PICKS offset 로그 추가 | `failed_section_name`에 구간 locator 추가. TYPE_D 재발 정밀 분석 기반 마련 |
| **3** | 권장 필드 4종 직접 로그화 | opener_pass / 기준1_pass / 기준5_pass / source_structure_pass 로그 직접 포함 |
| **4** | TYPE_D 추가 샘플 확보 | WARN 허용 정책 반복 강건성 검증. 3회 재현 시 WARN→PASS 승격 조건 검토 개시 |
| **5** | 타 TYPE 최초 발생 시 즉시 규칙 검증 | TYPE_A/B/C/E/UNKNOWN 발생 즉시 Axis C 규칙 적용 및 실전 검증 |

### 9-2. Phase 19 시작 문장

> Phase 19는 Phase 18에서 남긴 운영 로그 보강과 `PARSE_FAILED` 반복 강건성 검증을 우선 수행한다. 구조 개편이 아니라, 정책-로그-반복 샘플 축을 통한 운영 안정성 확정 단계로 이어간다.

---

## 10. 최종 제출 체크리스트

- [x] Axis A~D 보고서 4종 참조 반영
- [x] 실발행본 수(5건) 및 공개 URL 수(5건) 기재
- [x] 기준1/기준5 판정 기재 (전건 PASS)
- [x] opener 안정성 수치 기재 (5/5, 100%)
- [x] fallback / `PARSE_FAILED` 수치 기재 (1건, TYPE_D)
- [x] 남은 이슈(5건)와 운영 모니터링 항목(5건) 분리
- [x] 최종 판정: **CONDITIONAL GO** (1개만 선택)
- [x] Phase 18 Close-out 선언 문구 삽입
- [x] Phase 19 인계 포인트 기재 (5개 항목, 우선순위 정렬)
