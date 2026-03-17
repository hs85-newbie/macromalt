# Phase 13 핸드오프 — 해석 지성 & 시간/수치 신뢰성 강화

## 배경

Phase 12까지의 문제: 구조 규칙은 있으나 글이 여전히 범용 AI 요약문 수준.
- [해석]/[전망] 태그가 존재하나 교과서 인과관계만 전달
- 모든 문장에 헤징 어미 기계적 반복
- 반론이 카테고리 이름(변동성, 불확실성) 수준
- Post2 도입부가 Post1 매크로 설정을 반복
- Gemini verifier가 시간/수치 이슈를 탐지해도 Step3 수정 후 동일 문제가 통과

Phase 13의 목표: GPT에게 "해석하라"는 지시에서 "좋은 해석의 기준"으로 업그레이드.

---

## 변경 파일

| 파일 | 변경 내용 |
|---|---|
| `generator.py` | SECTION A-3 삽입 (P13 상수 + 진단 함수 6개), gemini_analyze/gpt_write_analysis/gpt_write_picks 프롬프트 주입, generate_deep_analysis/generate_stock_picks_report P13 진단 배선 |
| `main.py` | Phase 13 게이트 블록 교체 (Phase 12 키 유지 + 신규 9개 키 추가), 배너 Phase 13으로 변경 |
| `docs/handoff_phase13.md` | 이 파일 |

---

## Track A — 해석 지성

### A1. 비자명성 기준 (`_P13_INTERPRETATION_STANDARD`)

**[해석] 레이블이 성립하려면 다음 중 하나 이상 충족 필요:**
- (a) 이 시점·이 데이터 조합에서만 나오는 특수한 함의
- (b) 상식적으로 연결되지 않는 두 변수 간의 비자명적 연결
- (c) 상충 신호들 사이의 긴장을 해소하는 판단
- (d) 오늘이 같은 테마의 다른 날과 왜 다른지 구체적 설명
- (e) 투자자의 판단 기준·섹터 선호·시나리오 가중치에 영향을 주는 해석

**금지 패턴:**
- "유가 상승 → 인플레이션 압력" (교과서 인과)
- "금리 상승 → 밸류에이션 부담" (교과서 인과)
- "이익 추정치 상향 → 투자자 관심" (당연한 결론)

**진단:** `_score_interpretation_quality()` → `weak_interpretation` 항목

### A2. 헤징 언어 3분류 (`_P13_HEDGING_TRIAGE_RULES`)

| Type | 대상 | 헤징 허용 |
|---|---|---|
| 1 — 팩트 서술 | 과거/현재 수치·날짜 이벤트 | 금지. 출처 명시 후 직접 서술 |
| 2 — 분석적 연결 | 인과·해석·함의 | 문단당 1회 허용. 이후 직접 서술 |
| 3 — 전망·시나리오 | 미래 경로, 조건부 기대 | 허용. 단 명시적 조건(만약/발생 시) 필수 |

**진단:** `_score_interpretation_quality()` → `hedge_overuse` 항목
- 헤징 구문 / 전체 문장 수 비율 > 0.5 → FAIL, > 0.30 → WARN

### A3. 반론 최소 규격 (`_P13_COUNTERPOINT_SPEC`)

**반론 필수 3요소:**
1. 구체적 조건 — 어떤 상황이 발생해야 반론이 성립하는가
2. 그 조건 하의 결과
3. 오늘의 핵심 논지와의 충돌

**금지:** 카테고리 이름만 나열 ("변동성 리스크", "불확실성 지속")

**진단:** `_score_interpretation_quality()` → `counterpoint_spec` 항목
- 반론 섹션에서 조건 마커 ≥ 2개 → PASS, 1개 → WARN, 0개 → FAIL

### A4. 분석 뼈대 (`_P13_ANALYTICAL_SPINE_RULE`)

**뼈대 형식:**
`"[팩트 X]와 [팩트 Y]가 동시 발생 중이며, 이는 투자자가 [Z] 대신 [W]에 주목해야 함을 시사"`

GPT에게 작성 전 내부적으로 뼈대를 설정하고, 기사 제목 또는 첫 단락에 반영하도록 지시.

### A5. Post2 연속성 (`_P13_POST2_CONTINUITY_RULE`)

Post2는 Post1이 종료된 시점에서 시작. Post1의 매크로/테마 설정 재설명 금지.

**진단:** `_check_post_continuity()` → n-gram 4-gram 중복 + 배경 재설명 패턴 체크

---

## Track B — 시간/수치 신뢰성

### B1. 시간 일관성 가드 (`_check_temporal_sanity`)

체크 항목:
- 미래/당해 연도를 확정 사실 동사로 서술 (`FUTURE_AS_FACT`) → FAIL
- 과거 연도를 전망 동사로 서술 (`PAST_AS_FORECAST`) → WARN
- 출처 날짜가 7일 초과 경과 (`STALE_DATE_REF`) → WARN
- "최근/근래" 5회 이상 날짜 없이 반복 (`VAGUE_RECENCY`) → WARN

`FUTURE_AS_FACT` 존재 시 → FAIL → main.py 게이트에서 HOLD

### B2. 수치 합리성 가드 (`_check_numeric_sanity`)

합리적 범위 (2024-2027 기준, 넓게 설정):
| 항목 | 범위 |
|---|---|
| KOSPI | 1,800 – 4,500 pt |
| KOSDAQ | 500 – 1,800 pt |
| USD/KRW | 1,050 – 1,800 원 |

범위 이탈 2건 이상 → FAIL → main.py 게이트에서 HOLD

### B3. Verifier-to-Revision Closure (`_check_verifier_closure`)

- Gemini verifier가 탐지한 이슈 중 시간/수치 관련 고위험 이슈 추출
- Step3 수정 후 동일 인용 구절이 여전히 존재하는지 확인
- 미해소 ≥ 2건 → FAIL, 1건 → WARN

---

## 게이트 JSON 형식

```json
{
  "numeric_density":             "PASS|WARN|FAIL",
  "time_anchor":                 "PASS|WARN|FAIL",
  "counterpoint_presence":       "PASS|WARN|FAIL",
  "generic_wording_control":     "PASS|WARN|FAIL",
  "post_role_separation":        "PASS|WARN|FAIL",
  "interpretation_quality_p1":   "PASS|WARN|FAIL",
  "interpretation_quality_p2":   "PASS|WARN|FAIL",
  "hedge_overuse_p1":            "PASS|WARN|FAIL",
  "hedge_overuse_p2":            "PASS|WARN|FAIL",
  "counterpoint_specificity_p1": "PASS|WARN|FAIL",
  "counterpoint_specificity_p2": "PASS|WARN|FAIL",
  "post1_post2_continuity":      "PASS|WARN|FAIL",
  "temporal_consistency":        "PASS|WARN|FAIL",
  "numeric_sanity":              "PASS|WARN|FAIL",
  "verifier_revision_closure":   "PASS|WARN|FAIL|SKIP",
  "phase12_compatibility":       "PASS",
  "public_signature_stability":  "PASS",
  "import_build":                "PASS",
  "final_status":                "GO|HOLD"
}
```

**HOLD 트리거:**
- `temporal_consistency == FAIL` (미래 연도를 확정 사실로 서술)
- `numeric_sanity == FAIL` (주요 지수 수치 합리적 범위 이탈 2건 이상)

---

## 진단 함수 위치

| 함수 | 위치 | 목적 |
|---|---|---|
| `_score_interpretation_quality()` | generator.py SECTION A-3 | 헤징 과잉 + 약한 해석 + 반론 조건 마커 |
| `_check_temporal_sanity()` | generator.py SECTION A-3 | 연간 실적 혼용, 출처 날짜 스탈니스 |
| `_check_numeric_sanity()` | generator.py SECTION A-3 | KOSPI/KOSDAQ/환율 범위 이탈 |
| `_check_verifier_closure()` | generator.py SECTION A-3 | Step3 수정 후 이슈 해소 여부 |
| `_check_post_continuity()` | generator.py SECTION A-3 | Post2 도입부 중복 감지 |

---

## 프롬프트 주입 위치

| 위치 | 추가 내용 |
|---|---|
| `gemini_analyze()` user_msg 끝 | `_P13_GEMINI_SPINE_HINT` |
| `gpt_write_analysis()` user_msg 앞 | `_P13_POST1_INTELLIGENCE_RULES` (A1+A2+A3+A4 조합) |
| `gpt_write_picks()` user_msg 앞 | `_P13_POST2_INTELLIGENCE_RULES` (A5+A1+A2+A3+A4 조합) |

---

## 반환 데이터 구조 변경

`generate_deep_analysis()` 반환 dict에 `p13_scores` 추가:
```python
{
  "interpretation": {hedge_overuse, hedge_count, hedge_ratio, weak_interpretation, weak_interp_hits, counterpoint_spec, condition_hits, overall},
  "temporal":       {status, flags, stale_date_count, forecast_confusion_count},
  "numeric":        {status, flags, suspicious_count},
  "closure":        {status, total_checked, resolved_count, unresolved_count, unresolved},
}
```

`generate_stock_picks_report()` 반환 dict에 `p13_scores` 추가 (위 항목 + `continuity`):
```python
{
  ...위와 동일...,
  "continuity": {status, ngram_overlap_count, bg_repeat_count, sample_overlaps},
}
```

---

## 리스크 / 후속 항목

| 항목 | 내용 |
|---|---|
| 해석 품질 진단은 진단일 뿐 | `_score_interpretation_quality`는 규칙 기반 근사치. 진짜 비자명성은 인간 판단 필요 |
| 수치 범위는 넓게 설정 | 오탐 방지를 위해 KOSPI 1,800–4,500 등 의도적으로 넓음. 실제 의심 수치만 FAIL |
| Gemini spine hint는 지시일 뿐 | Gemini가 theme 필드 논지화 지시를 무시하면 GPT 뼈대 설정에 영향 없음 |
| 헤징 비율 임계값 튜닝 필요 | 0.30(WARN) / 0.50(FAIL)은 초기값. 실제 런 후 calibration 필요 |
| Post2 continuity BG_PATTERNS | 하드코딩된 배경 패턴. 테마가 바뀌면 false positive 가능. 다음 페이즈에서 동적화 고려 |
