# REPORT_PHASE18_AXIS_D_REPEAT_STABILITY.md

작성일: 2026-03-20
Phase: **Phase 18 — Axis D 1차 실행**
범위: opener 반복 안정성 · generic opener 재오염 감시 · TYPE_D/fallback 재발 · 로그 보강 반영 점검
데이터 기준: Phase 17 샘플 발행 5건 (Post 177 / 179 / 183 / 185 / 187)
참조 문서:
- REPORT_PHASE17_POST2_OPENER_AND_PARSE_FAILED.md
- REPORT_PHASE18_AXIS_A_CLOSURE_COLLECTION.md
- REPORT_PHASE18_AXIS_B_FALLBACK_POLICY.md
- REPORT_PHASE18_AXIS_C_PARSE_FAILED_RESPONSE_RULES.md

---

## D-1. 샘플 수집 표 — 실발행본 기준 5건

| # | Post ID | 발행 시각 | opener H3 | opener 첫 문장 | 픽/섹터 포함 | generic 금지 준수 | opener PASS | 기준1 | 기준5 | source | closure | fallback | parse_failed_type | publish_blocked | slot 정상 | post_type 정상 | PICKS offset |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **177** | 2026-03-19 17:36:21 | 왜 지금 삼성전자인가 | 삼성전자는 글로벌 기술 이벤트에 대한 실적 민감도가 높은 종목으로 파악된다. | ✅ | ✅ | PASS | PASS | PASS | PASS | **FAIL** | False | 없음 | False | ✅ morning | ⚠️ 미기재 | ❌ 없음 |
| 2 | **179** | 2026-03-19 18:01:38 | 왜 지금 Energy Select Sector SPDR Fund인가 | [해석] Energy Select Sector SPDR Fund(XLE)는 중동의 지정학적 리스크 심화와 고유가 지속으로 인해 단기적인 수혜를 볼 수 있는 종목으로 파악된다. | ✅ | ✅ | PASS | PASS | PASS | PASS | **PASS** | False | 없음 | False | ✅ evening | ⚠️ 미기재 | ❌ 없음 |
| 3 | **183** | 2026-03-19 18:03:55 | 왜 지금 SK이노베이션인가 | SK이노베이션은 중동 지역의 지정학적 리스크 심화와 고유가 상황에서 관련 테마에 대한 노출도를 높일 수 있는 기업이다. | ✅ | ✅ | PASS | PASS | PASS | PASS | **WARN** | False | 없음 | False | ✅ morning | ⚠️ 미기재 | ❌ 없음 |
| 4 | **185** | 2026-03-19 18:06:19 | 왜 지금 S-Oil인가 | S-Oil은 중동 지정학적 리스크에 따른 고유가 압력 해석이 먼저 붙는 종목으로 파악된다. | ✅ | ✅ | PASS | PASS | PASS | PASS | **FAIL** | False | 없음 | False | ✅ us_premarket | ⚠️ 미기재 | ❌ 없음 |
| 5 | **187** | 2026-03-19 18:09:15 | 왜 지금 S-Oil인가 | S-Oil은 중동 지정학적 리스크로 인한 고유가 압력이 지속되는 현 시점에서 정유 섹터의 수혜가 예상되는 종목이다. | ✅ | ✅ | PASS | PASS | PASS | PASS | **WARN** | **True** | **TYPE_D** | False | ❌ unknown | ❌ unknown | ❌ 없음 |

**발행 URL 목록**

| Post ID | URL |
|---:|---|
| 177 | https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-%ec%82%bc%ec%84%b1%ec%a0%84%ec%9e%90-%ec%99%b8-%ec%a4%91%eb%8f%99-%eb%a6%ac%ec%8a%a4%ed%81%ac%ec%99%80-%ea%b8%80%eb%a1%9c%eb%b2%8c-%ea%b8%b0%ec%88%a0/ |
| 179 | https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-energy-select-sector-spdr-fund-%ec%99%b8-%ec%a4%91%eb%8f%99-%eb%a6%ac%ec%8a%a4%ed%81%ac%ec%99%80-%ea%b3%a0%ec%9c%a0%ea%b0%80-%ec%86%8d-%ed%88%ac/ |
| 183 | https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-sk%ec%9d%b4%eb%85%b8%eb%b2%a0%ec%9d%b4%ec%85%98-%ec%99%b8-%ec%a4%91%eb%8f%99-%eb%a6%ac%ec%8a%a4%ed%81%ac%ec%99%80-%ea%b3%a0%ec%9c%a0%ea%b0%80/ |
| 185 | https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-s-oil-%ec%99%b8-%ec%a4%91%eb%8f%99-%eb%a6%ac%ec%8a%a4%ed%81%ac%ec%99%80-%ea%b3%a0%ec%9c%a0%ea%b0%80-%ec%95%95%eb%a0%a5/ |
| 187 | https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-s-oil-%ec%99%b8-%ec%a4%91%eb%8f%99-%eb%a6%ac%ec%8a%a4%ed%81%ac%ec%99%80-%ec%97%90%eb%84%88%ec%a7%80-%ec%84%b9%ed%84%b0/ |

---

## D-2. opener 반복 안정성 집계

### 5건 핵심 검증 질문 대응

| # | 검증 질문 | 결과 |
|---|---|---|
| Q1 | opener는 추가 샘플에서도 계속 pick-angle 구조를 유지하는가? | **✅ 5/5 유지** |
| Q2 | generic opener 금지 규칙은 반복 발행에서도 유지되는가? | **✅ 0건 위반** |
| Q3 | opener 첫 문장은 계속 메인 픽 또는 핵심 섹터를 직접 호출하는가? | **✅ 5/5** |
| Q4 | TYPE_D 재발 시(Post 187)에도 opener 품질은 유지되는가? | **✅ PASS — "왜 지금 S-Oil인가"** |
| Q5 | `slot/post_type=unknown` 문제는 해소되었는가? | **❌ 미해소** — Post 187 still unknown |
| Q6 | PICKS 구간 offset 등 로그 보강 항목은 반영되었는가? | **❌ 미반영** — Phase 18 기간 내 신규 발행 미수행 |
| Q7 | closure/publish/fallback 판정은 Axis B/C 정책과 일관되게 작동하는가? | **✅ 일관** — Post 187 WARN 허용 정책 적용 |

### 집계 표

| 항목 | 결과 | 비율 | 비고 |
|---|---:|---:|---|
| opener PASS | 5건 | **100%** | 전원 pick-angle 구조 유지 |
| generic opener 금지 준수 | 5건 위반 없음 | **100%** | 6종 금지 패턴 0건 |
| opener 첫 문장 픽/섹터 포함 | 5건 | **100%** | 픽명 첫 단어 또는 첫 문장 내 명시 |
| macro recap 시작 0건 여부 | 0건 | **0%** | macro recap 시작 없음 ✅ |
| H3 다양성 확보 | 4종 H3 사용 | 양호 | 삼성전자/XLE/SK이노베이션/S-Oil — S-Oil은 2건 중복 (서로 다른 슬롯) |
| opener→메인픽 연결 자연성 | 5건 | **100%** | 각 opener 섹션이 메인 픽 섹션으로 자연 이행 확인 |

### opener 첫 문장 전문 발췌 (5건)

**#1 — Post 177 (삼성전자)**
> 삼성전자는 글로벌 기술 이벤트에 대한 실적 민감도가 높은 종목으로 파악된다. 엔비디아 GTC에서 AI 반도체 수요 확대가 예상되는 가운데, 삼성전자는 이 분야의 주요 플레이어로 평가된다. [해석] 이러한 수요 증가는 삼성전자의 반도체 부문 실적에 긍정적 영향을 미칠 가능성이 있다.

→ ✅ 픽명 첫 단어 / 핵심 변수: 실적 민감도 / macro recap 없음

**#2 — Post 179 (XLE)**
> [해석] Energy Select Sector SPDR Fund(XLE)는 중동의 지정학적 리스크 심화와 고유가 지속으로 인해 단기적인 수혜를 볼 수 있는 종목으로 파악된다. [해석] 에너지 섹터의 주요 종목들에 분산 투자하여 리스크를 완화하는 전략이기 때문이다. 이는 개별 에너지 기업의 변동성보다 섹터 전체의 상승 모멘텀을 활용하려는 전략에 가깝다.

→ ✅ 픽명 첫 문장 내 명시 / 핵심 변수: 고유가 수혜 / macro recap 없음

**#3 — Post 183 (SK이노베이션)**
> SK이노베이션은 중동 지역의 지정학적 리스크 심화와 고유가 상황에서 관련 테마에 대한 노출도를 높일 수 있는 기업이다. [해석] 이번 주 유가 급등은 SK이노베이션의 정유 및 화학 부문에 강력한 상승 모멘텀을 제공할 수 있다. 이는 경쟁사 대비 높은 정제마진 민감도와 석유화학 제품 포트폴리오의 유가 연동성이 핵심이다.

→ ✅ 픽명 첫 단어 / 핵심 변수: 정제마진 민감도, 유가 연동성 / macro recap 없음

**#4 — Post 185 (S-Oil)**
> S-Oil은 중동 지정학적 리스크에 따른 고유가 압력 해석이 먼저 붙는 종목으로 파악된다. [전망] 현재 국제유가가 110달러를 돌파하면서, S-Oil은 정유 마진 확대에 따른 이익 개선이 예상된다. 2024년 매출액은 36조 1,819억원으로 전년 대비 2.6% 증가했으나, 영업이익은 68.9% 감소한 4,195억원을 기록하여 향후 실적 개선이 필요하다.

→ ✅ 픽명 첫 단어 / 핵심 변수: 고유가 압력, 정유 마진 / macro recap 없음

**#5 — Post 187 (S-Oil / TYPE_D fallback)**
> S-Oil은 중동 지정학적 리스크로 인한 고유가 압력이 지속되는 현 시점에서 정유 섹터의 수혜가 예상되는 종목이다. 이는 최근 7일 간 국제 유가가 급등하며 브렌트유가 110달러를 돌파한 상황에서 더욱 부각된다. S-Oil의 2024년 매출액은 전년 대비 2.6% 증가한 36조 1,817억 원을 기록했으며, 이는 국제 유가 상승에 따른 정유 제품 수요 증가와 직접 연결된다.

→ ✅ 픽명 첫 단어 / 핵심 변수: 고유가 압력, 정유 수혜 / macro recap 없음
→ ✅ **TYPE_D fallback 경로에서도 opener 구조 완전 유지** — Axis B/C 정책 기준 충족

---

## D-3. TYPE_D / fallback 재발 감시

### 재발 집계 표

| 항목 | 건수 | Post ID | 판정 |
|---|---:|---|---|
| fallback_used=True 재발 | **1건** | 187 | Axis B/C 정책상 WARN 허용 적용. 30일 내 임계치(3건) 미달. |
| TYPE_D 재발 | **1건** | 187 | 동일. 임계치 미달. |
| TYPE_UNKNOWN 발생 | **0건** | — | ✅ 차단 기준 미도달 |
| publish_blocked=True 발생 | **0건** | — | ✅ 전건 정상 발행 |

### 해석

- **TYPE_D 1건 + opener PASS**: Axis B/C 정책의 실전 적용 가능성 1회 확인.
  - Post 187: opener "왜 지금 S-Oil인가" 유지 + 기준1/5 PASS + source 유지 → WARN 허용 정상 적용.
  - Axis C 의사코드 `IF TYPE_D AND opener_pass AND 기준1/5 AND source_pass → WARN, publish_blocked=false` 실전 일치 ✅
- **TYPE_UNKNOWN 0건**: 임계치 차단 규칙 미발동. 분류 체계 안정.
- **재발 임계치 여유**: TYPE_D 1건 발생 / 30일 임계치 3건 → 현 시점 FAIL 승격 조건 미달.
- **주의**: TYPE_D가 1건이므로 "안정 확인"이 아니라 "1회 적용 확인" 수준. 추가 샘플 필요.

---

## D-4. 로그 보강 반영 점검

### 점검 표 (Phase 17 기준 → Phase 18 현재 코드 반영 여부)

| 항목 | 상태 | 적용 방식 | 비고 |
|---|---|---|---|
| slot 정상 기록 | **❌ 미해소** | 코드 보강 미진행 (Phase 18 기간 내 신규 발행 없음) | Post 187에서 `unknown` 확인. 보강 대상 1순위. |
| post_type 정상 기록 | **❌ 미해소** | 동일 | 동일. `unknown` 기록 잔존. |
| PICKS offset 기록 | **❌ 미반영** | 코드 반영 미진행 | Axis C 인계 항목. 구간 locator 미추가. |
| opener_pass 직접 로그화 | **❌ 미반영** | 보고서 수동 확인으로 대체 중 | 권장 항목. 자동화 시 필요. |
| 기준1/기준5/source 직접 로그화 | **❌ 미반영** | 동일 | 권장 항목. |
| parse snapshot 경로 유지 | **✅ 유지** | `_log_parse_failed_event()` 10필드 기록 정상 | raw/normalized snapshot 경로 정상 보존. |

### 현재 상황 평가

- **코드 반영 미완료**: Phase 18 Axis D 시점에서 신규 발행 샘플이 수행되지 않아, 코드 보강 후 실전 검증이 불가한 상태.
- **1순위 보강 항목(slot/post_type)**: 현재 코드에서 `_log_parse_failed_event()` 호출 시점에 slot/post_type 값이 전달되지 않는 현상이 Phase 17에서 확인됨. 코드 수정 후 재실행 필요.
- **판단 기준**: 로그 보강 항목은 실전 발행이 이루어진 후에만 반영 여부 확인 가능. 현 시점에서는 "보강 대상 확정" 단계로 기록.

---

## D-5. 예외 케이스 상세 기록

### Case D-5-1 — Post 187 (TYPE_D fallback / WARN)

- **Post ID**: 187
- **발행 시각**: 2026-03-19 18:09:15
- **URL**: https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-s-oil-%ec%99%b8-%ec%a4%91%eb%8f%99-%eb%a6%ac%ec%8a%a4%ed%81%ac%ec%99%80-%ec%97%90%eb%84%88%ec%a7%80-%ec%84%b9%ed%84%b0/
- **opener H3**: 왜 지금 S-Oil인가
- **opener 첫 2~3문장**:
  > S-Oil은 중동 지정학적 리스크로 인한 고유가 압력이 지속되는 현 시점에서 정유 섹터의 수혜가 예상되는 종목이다. 이는 최근 7일 간 국제 유가가 급등하며 브렌트유가 110달러를 돌파한 상황에서 더욱 부각된다. S-Oil의 2024년 매출액은 전년 대비 2.6% 증가한 36조 1,817억 원을 기록했으며, 이는 국제 유가 상승에 따른 정유 제품 수요 증가와 직접 연결된다.
- **verifier closure**: WARN
- **fallback_used**: True
- **parse_failed_type**: TYPE_D
- **publish_blocked**: False
- **발생 이슈**: Step3:verifier:json_parse 단계에서 Gemini 비정형 응답. TYPE_D 분류. reviser skip. GPT 초안 원본 fallback 발행.
- **Axis B/C 정책과의 일치 여부**: ✅ 일치 — TYPE_D + opener PASS + 기준1/5 PASS + source PASS → WARN 허용 조건 충족.
- **필요한 후속 조치**: slot/post_type=unknown 로그 보강. TYPE_D 재발 시 동일 정책 재적용 및 임계치 누적 관리.

---

### Case D-5-2 — Post 177 (closure FAIL / opener PASS)

- **Post ID**: 177
- **발행 시각**: 2026-03-19 17:36:21
- **URL**: https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-%ec%82%bc%ec%84%b1%ec%a0%84%ec%9e%90-%ec%99%b8-%ec%a4%91%eb%8f%99-%eb%a6%ac%ec%8a%a4%ed%81%ac%ec%99%80-%ea%b8%80%eb%a1%9c%eb%b2%8c-%ea%b8%b0%ec%88%a0/
- **opener H3**: 왜 지금 삼성전자인가
- **opener 첫 2~3문장**:
  > 삼성전자는 글로벌 기술 이벤트에 대한 실적 민감도가 높은 종목으로 파악된다. 엔비디아 GTC에서 AI 반도체 수요 확대가 예상되는 가운데, 삼성전자는 이 분야의 주요 플레이어로 평가된다. [해석] 이러한 수요 증가는 삼성전자의 반도체 부문 실적에 긍정적 영향을 미칠 가능성이 있다.
- **verifier closure**: FAIL
- **fallback_used**: False
- **parse_failed_type**: 없음
- **publish_blocked**: False
- **발생 이슈**: verifier 26건 → reviser REVISED → 고위험 미해소 1건 → FAIL. closure FAIL이나 발행본 품질 기준1/5 위반 없음. fallback 없이 정상 경로.
- **Axis B/C 정책과의 일치 여부**: ✅ 일치 — PARSE_FAILED 없음. closure FAIL은 Axis A C2(reviser 미수렴) 유형으로 분류. 발행 허용 적절.
- **필요한 후속 조치**: reviser 미해소 이슈 유형 세분화 로그 강화. 발행 품질 직접 영향 없으므로 즉시 수정 불필요.

---

### Case D-5-3 — Post 185 (closure FAIL / opener PASS)

- **Post ID**: 185
- **발행 시각**: 2026-03-19 18:06:19
- **URL**: https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-s-oil-%ec%99%b8-%ec%a4%91%eb%8f%99-%eb%a6%ac%ec%8a%a4%ed%81%ac%ec%99%80-%ea%b3%a0%ec%9c%a0%ea%b0%80-%ec%95%95%eb%a0%a5/
- **opener H3**: 왜 지금 S-Oil인가
- **opener 첫 2~3문장**:
  > S-Oil은 중동 지정학적 리스크에 따른 고유가 압력 해석이 먼저 붙는 종목으로 파악된다. [전망] 현재 국제유가가 110달러를 돌파하면서, S-Oil은 정유 마진 확대에 따른 이익 개선이 예상된다. 2024년 매출액은 36조 1,819억원으로 전년 대비 2.6% 증가했으나, 영업이익은 68.9% 감소한 4,195억원을 기록하여 향후 실적 개선이 필요하다.
- **verifier closure**: FAIL (Post2 기준 별도 판정 — 14건, 고위험 미해소 1건)
- **fallback_used**: False
- **parse_failed_type**: 없음
- **publish_blocked**: False
- **발생 이슈**: verifier 14건 → reviser REVISED → 고위험 미해소 1건. "Post2 기준 별도 FAIL" 표현 주목. C1+C2 복합 가능성 (Axis A). 발행본 품질 위반 없음.
- **Axis B/C 정책과의 일치 여부**: ✅ 일치 — PARSE_FAILED 없음. FAIL이나 fallback 없음. 발행 허용.
- **필요한 후속 조치**: "Post2 기준 별도 FAIL" 로직 세부 확인. verifier C1 strictness 독립 여부 추가 샘플에서 검증.

---

## D-6. 판정 기준 대조

### GO 조건 체크

| # | GO 조건 | 달성 여부 | 비고 |
|---|---|---|---|
| 1 | opener PASS 100% | **✅ 100% (5/5)** | |
| 2 | generic opener 금지 위반 0건 | **✅ 0건** | |
| 3 | opener 첫 문장 픽/섹터 포함 100% | **✅ 100% (5/5)** | |
| 4 | TYPE_UNKNOWN 0건 | **✅ 0건** | |
| 5 | fallback/TYPE_D 재발 시 Axis B/C 정책 일관 처리 | **✅ Post 187 WARN 허용 적용 일치** | |
| 6 | `slot/post_type=unknown` 해소 완료 | **❌ 미해소** | 코드 반영 미완 |
| 7 | 로그 보강 핵심 항목 반영 완료 | **❌ 미반영** | 신규 발행 없어 검증 불가 |

**GO 달성 불가** — 조건 6·7 미충족

### CONDITIONAL GO 조건 체크

- [x] opener는 안정적이나 로그 보강 일부 미완 → **해당**
- [x] TYPE_D 재발 표본(1건)이 부족하여 정책 강건성 추가 확인 필요 → **해당**
- [x] fallback은 통제되나 승격/차단 경계 추가 샘플 필요 → **해당**

**→ CONDITIONAL GO 해당**

### HOLD 조건 체크

| HOLD 조건 | 해당 여부 |
|---|---|
| generic opener 재발 | ❌ 미해당 |
| opener 첫 문장 픽/섹터 누락 반복 | ❌ 미해당 |
| 기준1 또는 기준5 위반 발행 발생 | ❌ 미해당 |
| TYPE_UNKNOWN 2건 이상 | ❌ 미해당 |
| fallback 경로에서 구조/출처 손실 동반 | ❌ 미해당 |
| publish_blocked 필요한 케이스가 허용 발행됨 | ❌ 미해당 |

**HOLD 조건 전무**

---

## D-7. 최종 요약

### D-7 요약

| 항목 | 결과 |
|---|---|
| 샘플 수 | **5건** (Phase 17 전체 / 실발행본 / 공개 URL 5건 확보) |
| opener PASS | **5/5 (100%)** |
| generic opener 위반 | **0건** |
| fallback 재발 | **1건** (Post 187 — Axis B/C 정책 WARN 허용 적용) |
| TYPE_D 재발 | **1건** (Post 187 — 임계치 3건 미달) |
| TYPE_UNKNOWN | **0건** |
| 로그 보강 완료 항목 | parse snapshot 경로 유지 (10필드 정상) |
| 미완료 항목 | slot/post_type=unknown 해소 (1순위) / PICKS offset 미기재 / opener_pass·기준1·기준5·source 직접 로그화 미완 |
| **최종 판정** | **CONDITIONAL GO** |
| 다음 인계 | PHASE18_INTEGRATED_CLOSEOUT_TEMPLATE.md 자동 생성 조건 충족 |

### 최종 판정 근거 분리

**달성된 것**
- opener 반복 안정성 5/5 (100%) 확인 — Phase 17 pick-angle 구조 전혀 흔들리지 않음
- generic opener 금지 규칙 5건 연속 준수
- TYPE_D fallback 케이스에서 Axis B/C 정책 일관 적용 확인 (1회)
- 기준1/기준5 5건 전체 PASS
- 전건 실발행 + 공개 URL 5건 확보

**남은 것**
- `slot/post_type=unknown` 코드 보강 미완 (코드 수정 후 신규 발행에서 확인 필요)
- PICKS offset 로그 미추가
- TYPE_D 추가 샘플(최소 2건 더) 없어 WARN 허용 정책의 반복 강건성 미검증
- opener_pass / 기준1·기준5·source 직접 로그화 미완 (자동 검수 준비 미완)

---

## D-8. 다음 단계 자동 연결

### 자동 연결 조건 충족 여부

| 조건 | 결과 |
|---|---|
| 최종 판정이 GO 또는 CONDITIONAL GO | ✅ CONDITIONAL GO |
| Axis D 보고서가 실발행본 기준으로 작성됨 | ✅ 5건 실발행본 / URL 전건 포함 |
| opener 반복 안정성 결과가 명확함 | ✅ 100% PASS 명확 |
| fallback / TYPE_D / 로그 보강 상태 문서에 정리됨 | ✅ D-3 / D-4 / D-5 기록 |

**→ 자동 연결 조건 충족**
**→ `PHASE18_INTEGRATED_CLOSEOUT_TEMPLATE.md` 실행 가능**

---

## 참고: Phase 18 Axis A~D 판정 종합

| 축 | 판정 | 핵심 근거 | 주요 미완 항목 |
|---|---|---|---|
| **Axis A** (closure FAIL/WARN 수집) | CONDITIONAL GO | 4건 수집 / C2 reviser 미수렴 공통 패턴 확인 | 미해소 이슈 유형 세분화 로그 미구축 |
| **Axis B** (fallback 정책) | CONDITIONAL GO | WARN 허용 조건 정의 / Post 187 적용 확인 | Type_D 추가 샘플 필요 / WARN→PASS 미검증 |
| **Axis C** (PARSE_FAILED 대응 규칙) | CONDITIONAL GO | 전 유형 대응 규칙 문서화 / 의사코드 완성 | TYPE_D 1건 실전 관측 / 타 TYPE 미관측 / slot/post_type 보강 미완 |
| **Axis D** (opener 반복 안정성) | **CONDITIONAL GO** | opener 100% PASS / 정책 1회 적용 일치 | 로그 보강 미완 / TYPE_D 추가 샘플 없음 |
