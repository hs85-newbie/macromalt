# REPORT_PHASE20_EDITORIAL_PLANNER_TRACK.md

작성일: 2026-03-23
범위: Phase 20 — Editorial Planner Track (Phase 1~3)
최종 판정: **구현 완료 — 실전 run 대기**

---

## 1. 작업 배경

### 문제 진단

macromalt 파이프라인의 글쓰기 품질 문제는 어휘나 상투어가 아니라 **파이프라인의 인식 구조**에 있었다.

```
Gemini Step1 → 평탄한 사실 묶음 JSON
     ↓
GPT → "이 JSON을 HTML로 변환하라" (serializer 역할)
     ↓
결과: 사실을 균등 배분한 구조적 요약 → AI처럼 읽힘
```

- 모든 사실이 동등한 중요도로 처리됨
- "왜 오늘 이게 중요한가"를 결정하는 레이어 없음
- 어떤 사실이 리드인지 GPT가 모른 채 글을 작성
- 균등 배분이 기본값 → 모든 섹션이 동형 구조 반복

### 해결 방향

작업지시서(`PROMPT_CLAUDECODE_EDITORIAL_PLANNER_TRACK.md`)에 따라 파이프라인을 재설계:

```
structured facts → editorial plan → writer draft → verify/revise
```

**핵심 변경**: GPT를 "neutral fact serializer"에서 "thesis-expansion engine"으로 전환.

---

## 2. 구현 범위 (Phase 1~3 단일 배치)

| Phase | 내용 | 상태 |
|-------|------|------|
| 1 | Step1 스키마 확장 (fact ID + perspective fields) | ✅ 완료 |
| 2 | Step1.5 Editorial Planner 삽입 (Post1/Post2 분리) | ✅ 완료 |
| 3 | Writer 역할 재정의 + 4-tier contract 소비 | ✅ 완료 |
| 4 | Verifier/Reviser 구조 검사 추가 | 다음 배치 |
| 5 | Slot/dedup opener strategy 연결 | 다음 배치 |
| 6 | 내부 지표 정식 스코어 | 이후 |

---

## 3. 변경 파일 및 변경 내용

### `generator.py`

#### Phase 1: GEMINI_ANALYST_SYSTEM 스키마 확장

**facts 배열 신규 필드:**
- `id`: `"fact_1"`, `"fact_2"` ... (planner evidence_ids 참조용 키)
- `causal_path`: 금융시장 전파 경로 (A → B → C 형식)
- `confidence`: `high | medium | low`

**background_facts 배열 신규 필드:**
- `id`: `"bg_1"`, `"bg_2"` ...
- `usage_rule`: 항상 `"background_only"` (배경 처리 명시)

**신규 perspective fields:**
```json
"why_now":          { "claim", "evidence_ids", "confidence" }
"market_gap":       { "claim", "evidence_ids", "confidence" }
"analyst_surprise": { "level", "claim", "evidence_ids", "confidence" }
"stance_type":      "consensus_miss | underpriced_risk | overread | low_confidence | neutral"
"stance_evidence_ids": [...]
"risk_of_overstatement": [{ "text", "reason" }]
```

**perspective fields 생성 규칙 추가:**
- `evidence_ids`가 실제 facts id와 불일치하면 해당 필드 omit
- `why_now`는 today's specific trigger 필수. 범용 설명 금지.
- `market_gap`은 사실 서술만. 투자 권유 금지.
- `stance_type` 근거 없으면 강제로 `"neutral"`.
- `risk_of_overstatement`는 why_now/market_gap 존재 시 1개 이상 필수.

#### Phase 2: Step1.5 Editorial Planner 신규

**신규 상수:**
- `GEMINI_PLANNER_POST1_SYSTEM`: Post1 전용 planner (macro_mechanism / transmission_path / market_structure / counterpoint)
- `GEMINI_PLANNER_POST2_SYSTEM`: Post2 전용 planner (pick_trigger / stock_sensitivity / selection_logic / counterpoint)
- `GEMINI_PLANNER_USER`: planner 입력 템플릿

**신규 함수:**
- `_validate_planner_evidence_ids(planner, step1)`: evidence_ids 검증. 불일치 id 제거. lead 비면 None 반환.
- `_call_editorial_planner(step1, post_type, slot, run_id, history_constraints)`: Gemini planner 호출. 실패/검증 실패 시 None 반환 (fallback 보장).
- `_build_writer_contract(step1, planner, slot, history_constraints)`: planner 결과를 4-tier 구조 contract로 변환.

**4-tier contract 구조:**
```json
{
  "lead_facts":        [...],  // 글의 중심축 사실
  "secondary_facts":   [...],  // lead 강화 2차 근거
  "background_facts":  [...],  // context_only — 논거 인용 금지
  "disallowed_fact_ids": [...] // 본문 등장 절대 금지
}
```

**로깅 (Phase 2~3부터):**
```
[Phase 20] editorial planner OK | run_id=... | slot=... | post_type=... |
planner_used=True | stance_type=... | narrative_shape=... |
lead_angle_evidence_ids=[...] | background_ids=[...] | drop_ids=[...]

[Phase 20] writer evidence | run_id=... | post_type=... |
writer_used_evidence_ids=[...]

[Phase 20] planner FAILED | ... | planner_used=False | fallback=step1_only
```

#### Phase 3: Writer 역할 재정의

**신규 상수:**
- `_P20_POST1_CONTRACT_BLOCK`: Post1 writer contract 소비 지시 (user_msg 최상단 prepend)
- `_P20_POST2_CONTRACT_BLOCK`: Post2 writer contract 소비 지시

**핵심 writer 지시 변경:**
- "JSON을 HTML로 변환하라" → "lead_angle 논거를 중심으로 독자를 설득하라"
- 4-tier 사실 처리 규칙: lead_facts는 중심축, disallowed는 절대 금지
- section_plan role별 수사 구조 다변화 강제 (동형 구조 반복 금지)
- stance.type별 논리 구조 선택 (consensus_miss / underpriced_risk 등)
- narrative_shape 준수 (conclusion_first / contradiction_first / question_first)
- 출력 끝에 `<!-- macromalt:evidence_ids_used=[...] -->` 필수

**신규 helper:**
- `_parse_writer_evidence_ids(html)`: writer 출력에서 사용 evidence_ids 파싱

**함수 시그니처 변경:**
- `gpt_write_analysis(...)` ← `writer_contract=None`, `run_id=""` 추가
- `gpt_write_picks(...)` ← `writer_contract=None`, `run_id=""` 추가

**generate 함수 내 planner 호출 블록 삽입:**
- `generate_deep_analysis()`: Step 1.5 블록 (try/except fallback 포함)
- `generate_stock_picks_report()`: Step 1.5 블록 (try/except fallback 포함)

---

## 4. Fallback 구조

planner 실패 시 파이프라인은 중단되지 않는다.

```
planner JSON 파싱 실패
  → _call_editorial_planner() returns None
  → _p20_post1_contract = None
  → gpt_write_analysis(writer_contract=None)
  → 기존 방식 그대로 실행 (Phase 10~17 규칙 동일)
  → 로그: planner_used=False | fallback=step1_only
```

evidence_ids 검증 실패 시도 동일 fallback.

---

## 5. 로그 필드 정의 (Phase 2~3)

| 필드 | 출처 | 설명 |
|------|------|------|
| `planner_used` | planner 호출 결과 | True/False |
| `stance_type` | planner.stance.type | 5종 열거값 |
| `narrative_shape` | planner.narrative_shape | 3종 |
| `forced_rotation` | history_constraints | angle_shift 등 |
| `lead_angle_evidence_ids` | planner.lead_angle.evidence_ids | 리드 근거 id |
| `background_ids` | planner.background_or_drop.background_ids | 강등된 id |
| `drop_ids` | planner.background_or_drop.drop_ids | 제외된 id |
| `writer_used_evidence_ids` | writer HTML 주석 파싱 | 실제 사용 id |

---

## 6. 불변 원칙 (Phase 20 이후에도 변경 금지)

| 원칙 | 이유 |
|------|------|
| facts/background_facts 분리 | 시점 정책 (7일/30일) 유지 |
| `relevance_to_theme` 필드 유지 | `_filter_irrelevant_facts()` 의존 |
| planner 실패 → fallback 보장 | 파이프라인 차단 없음 원칙 |
| disallowed_fact_ids는 본문 금지 | 편집 계획 준수 |
| evidence_ids는 실제 id와 일치 필수 | 허구 근거 방지 |
| `stance_type` 5개 열거값만 허용 | 투자 권유 표현 방지 |

---

## 7. 다음 단계 (Phase 4)

| 항목 | 우선순위 |
|------|---------|
| Verifier 구조 검사 추가 (기준 26~35: section_isomorphism / emphasis_dispersion / lead_angle_drift 등) | 높음 |
| Slot/dedup → opener_strategy 연결 강화 | 중간 |
| 실전 run 1~2회 후 writer_used_evidence_ids vs lead_angle_evidence_ids 대조 분석 | 높음 |
| opener_pass Post1/Post2 기준 분리 (현재 Post1 항상 False) | 중간 |

---

## 8. 최종 판정

**구현 완료 — 실전 run으로 품질 검증 필요**

- Phase 1~3 단일 배치로 완료
- 문법 검증 완료 (`ast.parse` 통과)
- fallback 구조로 기존 파이프라인 안정성 유지
- planner/writer 8개 로그 필드 Phase 2~3부터 기록
- 실전 run에서 `planner_used=True`, `writer_used_evidence_ids` 확인 후 Phase 4 진행
