# REPORT_PHASE14H_REAL_OUTPUT_VALIDATION

작성일: 2026-03-17 | run_id: 20260317_090356

---

## 1. Run Audit

| 항목 | 결과 |
|---|---|
| 신규 런 실행 | ✅ YES — `run_id: 20260317_090356` |
| 신규 발행 성공 | ✅ YES — Post ID 140, 141 |
| 검증 기준 | 신규 URL 전용 (이전 런 미사용) |
| 기술적 블로킹 | 없음 |

**신규 발행 URL:**
- Post1 (ID 140): `https://macromalt.com/심층분석-호르무즈-해협-리스크-완화-기대감-속-개별/`
- Post2 (ID 141): `https://macromalt.com/캐시의-픽-현대위아-외-신사업-모멘텀과-시장-불확/`

**⚠ 핵심 관찰: 타겟 재작성 루프 미실행**

```
Post1: weak_hits=2 (임계값 3 미만) → 재작성 패스 스킵
Post2: weak_hits=2 (임계값 3 미만) → 재작성 패스 스킵
```

Phase 14H 타겟 교체 메커니즘은 이번 런에서 **한 번도 실행되지 않았다.**
따라서 이번 검증은 "타겟 교체가 작동하는가"를 직접 테스트할 수 없다.
이번 런은 Phase 14 기본 생성 품질만 측정한다.

**Phase 13 진단 결과 (런 로그):**
```
Post1: hedge_overuse=FAIL(14회/19문장=74%), weak_interp=WARN(2건), counterpoint=PASS
Post2: hedge_overuse=PASS(13회/58문장=22%), weak_interp=WARN(2건), counterpoint=FAIL(0마커)
Post1/Post2 연속성: WARN (배경 재설명 1건)
```

---

## 2. Sample Source Audit

| 샘플 | 소스 타입 | 전체/부분 | 현재 런 | 신뢰도 |
|---|---|---|---|---|
| Post1 (ID 140) | 신규 발행 URL 전체 본문 | 전체 | ✅ | 제한 없음 |
| Post2 (ID 141) | 신규 발행 URL 전체 본문 | 전체 | ✅ | 제한 없음 |

---

## 3. Executive Judgment

**타겟 재작성 핫픽스가 실제 기사 품질을 개선했는가?**

이번 런에서는 hotfix가 트리거되지 않아 직접 판단 불가.

**전체 시스템 품질 기준으로 판단할 때:**
이번 두 기사는 Phase 13 실출력 검증(HOLD) 및 Phase 14 실출력 검증(HOLD)보다 **더 나쁘다**.

- Post1: [해석] 레이블이 붙은 7개+ 문장 모두 "이는 X로 파악됩니다/보입니다" 형식의 교과서 인과
- Post1: 헤징 비율 74% (19문장 중 14회) — 역대 가장 심각한 hedge_overuse
- Post2: 반론 조건 마커 0개 — 카테고리 나열만
- Post2: Post1 매크로 설정 재설명 (FM5 회귀)
- 추출된 뼈대(spine): "이는 시장 전반의 불확실성을 줄이고, 투자 심리를 개선하는 요인으로 작용하는 것으로 파악됩니다." — 의미 없는 범용 문장

**결론:** 전진하기에 충분하지 않다. 새로운 실패 모드가 드러났다.

---

## 4. Sample-by-Sample Review

### Post1 — 심층분석: 호르무즈 해협 리스크 완화 기대감 속, 개별 기업의 실적 및 신사업 모멘텀 부각

**개선된 점:**
- 없음. 이전 Phase 14 런의 Post1보다 실질적으로 후퇴.
- 호르무즈 해협이라는 뉴스 기반 구체적 훅은 있음.

**여전히 실패하는 점:**

1. **[해석] = "이는 X로 파악됩니다" 공식 일관 반복:**
   - `"유가 하락은 인플레이션 압력을 줄이고...증시에 긍정적인 영향을 미치는 것으로 파악됩니다"` — FM1 교과서
   - `"글로벌 공급망 안정화 기대감은 기술주...개선하는 것으로 보입니다"` — 범용
   - `"오스코텍은 신약 개발 능력...기업 가치 평가에 긍정적인 영향을 받을 수 있습니다"` — 자명
   - `"이는 거시 경제 지표에 부정적인 영향을 미치며...부담으로 작용할 가능성이 있는 것으로 보입니다"` — FM1

2. **hedge_overuse 74%:** 19문장 중 14회 파악됩니다/보입니다. 모든 [해석] 레이블 문장이 헤징 어미로 끝남.

3. **분석 척주 없음:** 뼈대로 추출된 문장이 "불확실성 줄고 투자심리 개선" — 의미 없음. GPT가 `<!-- SPINE: -->` 주석을 생성하지 않아 최악의 폴백이 선택됨.

4. **섹션 간 연결 없음:** 상아프론테크, 오스코텍, 현대위아가 병렬 나열. 왜 이 세 종목이 "개별 기업 모멘텀" 논지를 함께 구성하는지 논리적 연결 없음.

**점수표 — Post1:**

| 차원 | 점수 | 근거 |
|---|---|---|
| targeted_rewrite_effectiveness | 1 | 핫픽스 미실행 — 판단 불가/해당 없음 |
| weak_interpretation_reduction | 1 | [해석] 전체가 "이는 X로 파악됩니다" 공식 |
| fact_forecast_separation | 3 | `[전망]` NH 경고에 사용, 팩트는 직접 서술 |
| hedge_control | 1 | 74% hedge_overuse — 심각 |
| counterpoint_specificity | 3 | 조건 있음("일시적일 경우") + 인플레 재점화 연쇄 |
| analytical_spine | 1 | 뼈대 없음, 병렬 팩트 나열 |
| post1_post2_continuity | N/A | Post1 자체 평가 |
| investor_usefulness | 2 | 호르무즈 훅은 구체적, 해석이 아무것도 주지 않음 |
| premium_tone | 1 | 헤징 과포화 AI 요약문 |
| temporal_trustworthiness | 3 | 날짜 오류 없음, 전망 레이블 사용 |
| numeric_trustworthiness | 3 | 5% 유가 하락, 2% 반도체 지수 구체적 |
| non_genericity | 2 | 호르무즈 훅 특화, 해석은 어떤 날에도 쓸 수 있음 |

**편집 총평:** 읽을 가치 없음. 헤징으로 포장된 자명한 결론들. Phase 14 이전 수준으로 회귀.

---

### Post2 — 캐시의 픽: 현대위아 외 — 신사업 모멘텀과 시장 불확실성

**개선된 점:**
- 없음.

**여전히 실패하는 점:**

1. **Post1 매크로 재설명 (FM5):** 도입부에서 "호르무즈 해협 리스크 완화로 인해 시장 전반의 불확실성이 줄어들고, 투자 심리가 개선될 것으로 보입니다" — Post1 첫 [해석] 문장을 그대로 반복. Phase 13 로그도 "배경 재설명 1건 감지 — WARN" 확인.

2. **[해석] = "이는 X로 파악됩니다" 전 종목 동일 패턴:**
   - `"이는 현대위아의 지속적인 신사업 확장과 연결된 결과로 파악됩니다"` — FM1
   - `"이는 현대위아가 글로벌 차량 부품 시장에서의 경쟁력을 높이는 요인으로 작용할 수 있습니다"` — FM1
   - `"이는 회사의 신사업 모멘텀이 실적으로 연결되고 있는 것으로 보입니다"` — FM1
   - `"이는 상아프론테크의 지속적인 기술 혁신이 시장에서의 경쟁력을 강화하는 요인으로 작용할 수 있습니다"` — FM1

3. **반론 조건 마커 0개 (counterpoint FAIL):**
   - 현대위아: `"유가 변동성과 지정학적 리스크의 장기화 가능성은...리스크로 작용할 수 있습니다"` — 카테고리 2개, 조건·결과 없음
   - 상아프론테크: `"글로벌 경제의 불확실성과 소재사업 성과의 지속 가능성"` — 카테고리 2개, 무조건
   - XLE: 약간 구체적이나 여전히 조건 부재

4. **뼈대 전달 실패:** Post1 spine = "이는 시장 전반의 불확실성을 줄이고..." — 이 generic spine이 Post2에 전달됐고, Post2는 이 generic frame에서 시작하여 generic continuation.

**점수표 — Post2:**

| 차원 | 점수 | 근거 |
|---|---|---|
| targeted_rewrite_effectiveness | 1 | 핫픽스 미실행 |
| weak_interpretation_reduction | 1 | 전 종목 "이는 X로 파악됩니다" 동일 공식 |
| fact_forecast_separation | 3 | `[전망]` 2026년 매출 적용, 과거 실적 직접 서술 |
| hedge_control | 2 | Post2 전체 hedge_ratio 22%로 PASS이지만 [해석] 블록은 포화 |
| counterpoint_specificity | 1 | 조건 마커 0개 — FAIL |
| analytical_spine | 1 | 종목 나열 구조, 논증 없음 |
| post1_post2_continuity | 1 | Post1 매크로 설정 재설명 — WARN 감지 |
| investor_usefulness | 2 | 종목 수치 존재, 해석 깊이 없음 |
| premium_tone | 1 | AI 종목 목록 생성 수준 |
| temporal_trustworthiness | 4 | `[전망]` 레이블 2026 실적 정확 처리 |
| numeric_trustworthiness | 3 | 8.8조 원, 4.3%, 49%, 407% — 출처 있음 |
| non_genericity | 2 | 종목 수치는 특화, 해석은 어느 종목에도 적용 가능 |

**편집 총평:** 3개 종목을 AI가 동일 공식으로 기계적으로 설명한 목록. Phase 13 이전 수준.

---

## 5. Failure-Mode Regression Check

| FM | 판정 | 근거 |
|---|---|---|
| FM1. [해석] = 교과서 인과 | **REGRESSED** | Phase 14 이전 런보다 심각. "이는 X로 파악됩니다" 공식 Post1 7회, Post2 4회. |
| FM2. 팩트 문장 헤징 | **REGRESSED** | Post1 hedge_overuse 74% — 역대 최악. [해석] 레이블 문장에 파악됩니다/보입니다 포화. |
| FM3. 반론 = 카테고리 | **NOT IMPROVED** | Post2 counterpoint 조건 마커 0개 FAIL. Post1 약간의 조건 있으나 논지 충돌 없음. |
| FM4. 기사 뼈대 약함 | **REGRESSED** | 이전 Phase 14 런 Post1은 실질 논증 구조 있었음. 이번은 병렬 팩트 나열. |
| FM5. Post2가 Post1 반복 | **REGRESSED** | 시스템 로그 "배경 재설명 1건 감지". Post2 도입부가 Post1 첫 [해석] 반복. |
| FM6. 시간/수치 신뢰 | **PARTIALLY IMPROVED** | `[전망]` 레이블 사용 정확. 숫자 출처 있음. |
| FM7. 범용 시황문 | **REGRESSED** | 호르무즈 훅 외 모든 해석이 "어떤 날에도 쓸 수 있는" 수준. |
| FM8. rewrite 실행 후 hits 불변 | **NOT TESTABLE** | weak_hits=2로 핫픽스 미실행. 직접 검증 불가. |

---

## 6. Cross-Sample Diagnosis

### 잔존 시스템 병목 (우선순위 순)

**병목 1 (긴급): `파악됩니다/보입니다` 헤징 어미가 [해석] 레이블 문장을 지배함.**

Post1의 [해석] 문장 7개 중 6개가 "이는 X로 파악됩니다" 형식. 이것이 현재 시스템의 지배적 산출 패턴이다. Phase 14의 hedge prohibition 지시(`_P14_HEDGE_DIRECT_PROHIBITION`)가 일부 팩트 서술에서는 효과가 있지만 [해석] 레이블이 붙은 분석 주장에서는 여전히 이 공식이 기본 생성 패턴으로 사용된다. `_P14_FEWSHOT_BAD_GOOD_INTERP`가 보여주는 GOOD 예시들이 실제 생성에 충분히 영향을 주지 못하고 있다.

**병목 2: `<!-- SPINE: -->` 주석이 GPT에 의해 생성되지 않음.**

Post1 spine이 "이는 시장 전반의 불확실성을 줄이고..." (hedge + generic)로 추출된 이유: GPT가 `<!-- SPINE: -->` 주석을 생성하지 않아 폴백이 첫 [해석] 문장을 사용. 이 generic spine이 Post2에 전달되어 Post2 품질도 함께 하락. `_P14_ANALYTICAL_SPINE_ENFORCEMENT` 지시가 GPT 실제 생성에서 준수되지 않는다.

**병목 3: rewrite 트리거 기준 weak_hits >= 3이 너무 높을 수 있음.**

이번 런 weak_hits=2 (이전 런 weak_hits=4). 패턴 감지 기준이 keyword co-occurrence 기반이라 run마다 변동이 크다. 이번 런에서는 hedge_overuse가 74%였는데도 rewrite가 미실행. rewrite 트리거 기준에 hedge_overuse FAIL을 추가해야 한다.

---

## 7. Gate Decision

**PHASE14H_OUTPUT_HOLD**

---

## 8. Next Required Action

**다음 단일 최우선 조치: [해석] 레이블 문장에서 `파악됩니다/보입니다` 어미 사용을 GPT 생성 시 명시 금지.**

현재 `_P14_HEDGE_DIRECT_PROHIBITION`은 팩트 서술에 대한 금지를 명시하지만, [해석] 레이블이 붙은 분석 주장에서의 동일 어미 사용은 차단하지 못한다. GPT는 [해석] 태그 뒤에 거의 항상 "이는 X로 파악됩니다/보입니다" 공식을 사용한다.

구체적 수정: `_P14_HEDGE_DIRECT_PROHIBITION`에 다음을 추가한다:
- `[해석] 레이블 문장에서 '파악됩니다', '보입니다', '작용하는 것으로', '것으로 파악'` 사용 금지
- `[해석] = "이는 [A]의 [결과/요인]으로 파악됩니다"` 공식 명시 금지
- [해석] 문장은 반드시 "투자자 판단 기준 이동" 또는 "비자명적 함의" 형식으로만 허용

그리고 rewrite 트리거를 확장한다: `weak_hits >= 3` 외에 `hedge_overuse == "FAIL"` (hedge_ratio > 0.5)일 때도 타겟 블록 재작성을 실행.

---

## 9. Final Validation JSON

```json
{
  "fresh_run_executed": "PASS",
  "fresh_publish_succeeded": "PASS",
  "new_url_based_validation": "PASS",
  "targeted_rewrite_effectiveness": "FAIL",
  "weak_interpretation_reduction": "FAIL",
  "fact_forecast_separation": "WARN",
  "hedge_control": "FAIL",
  "counterpoint_specificity": "FAIL",
  "analytical_spine": "FAIL",
  "post1_post2_continuity": "FAIL",
  "investor_usefulness": "FAIL",
  "premium_tone": "FAIL",
  "temporal_trustworthiness": "WARN",
  "numeric_trustworthiness": "WARN",
  "non_genericity": "FAIL",
  "final_status": "HOLD"
}
```

---

*이전 보고서: [REPORT_PHASE14_TARGETED_REWRITE_HOTFIX.md](REPORT_PHASE14_TARGETED_REWRITE_HOTFIX.md)*
