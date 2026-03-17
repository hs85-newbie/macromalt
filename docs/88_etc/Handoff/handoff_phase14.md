# Phase 14 핸드오프 — Generation Enforcement & Source Normalization

## 배경

Phase 13 이후 확인된 진단/생성 격차:
- Phase 13 탐지기는 올바르게 작동함 (weak_interp, temporal, numeric 감지 정상)
- 그러나 GPT는 프롬프트 규칙 텍스트만으로는 여전히 범용·교과서 인과관계 문장을 생성
- 소스 데이터의 전망형 어미가 팩트 서술에 그대로 배어들어 오염
- Phase 13은 "약한 해석을 탐지"했지만, 약한 해석이 발행됨
- KOSPI 5,500+ 2026 시장 레벨에서 numeric sanity가 과도한 HOLD 유발

Phase 14 목표: **진단이 실제 출력 변화를 만들어내도록** 강제.
탐지로 끝내지 않고, 소스 정규화 → 생성 강제 → 재작성 루프 → 수치 재보정으로 완성.

---

## 변경 파일

| 파일 | 변경 내용 |
|---|---|
| `generator.py` | SECTION A-4 삽입 (~370라인): Track A/B/C/D 상수 + 함수 6개. gpt_write_analysis / gpt_write_picks / generate_deep_analysis / generate_stock_picks_report / _check_numeric_sanity 수정 |
| `main.py` | Phase 14 게이트 블록 교체 (Phase 13 키 유지 + 신규 8개 키 추가), 배너 Phase 14 변경, HOLD 조건 재정의 |
| `docs/handoff_phase14.md` | 이 파일 |

---

## Track A — Source Normalization (소스 정규화)

### 목적

GPT가 글을 쓰기 전에, 소스 문장의 시제·확정 여부·신뢰도를 분류해서 프롬프트에 주입.
"2026년 3월 10일 KOSPI는 X로 마감할 것으로 예상됩니다" 같이 확정 사실이 전망 어미로
오염된 소스가 GPT 출력까지 오염되는 경로를 차단.

### 구현: `_normalize_source_for_generation(materials, run_date_str) -> str`

```
입력: materials["facts"] 리스트, 실행일 문자열
출력: GPT user_msg에 삽입할 정규화 블록 문자열
```

**분류 기준:**

| 분류 | 판별 기준 | GPT 지시 |
|---|---|---|
| ✅ CONFIRMED 팩트 | `date` 필드가 실행일 이전 + 확정 동사 (마감했습니다, 기록했습니다, ...) | 직접 서술 필수, 헤징 어미 금지 |
| ⚠ FORECAST | 미래 날짜 OR 전망 지시어 (예상됩니다, 전망됩니다, ...) | `[전망]` 태그 + 조건부 서술 필수 |
| ❓ AMBIGUOUS | 날짜 없음 OR 판별 불가 | `[해석]` 또는 조건부로만 서술 |

**`_P14_CONFIRMED_FACT_VERBS`** — 확정 동사 리스트 (19개):
`기록했습니다, 마감했습니다, 달성했습니다, 증가했습니다, ...`

**`_P14_FORECAST_INDICATORS`** — 전망 지시어 리스트 (20개):
`예상됩니다, 전망됩니다, 것으로 예상, 것으로 전망, ...`

### 주입 위치

- `gpt_write_analysis()` user_msg 맨 앞 (enforcement block 다음)
- `gpt_write_picks()` user_msg 맨 앞 (continuation block + enforcement block 다음)

---

## Track B — Generation Enforcement (생성 강제)

### B1. Few-shot BAD→GOOD 대조 예시 (`_P14_FEWSHOT_BAD_GOOD_INTERP`)

GPT 프롬프트에 **5개 BAD→GOOD 대조 쌍** 주입. 추상 규칙 텍스트 대신 대조 예시.

```
❌ BAD: 유가 상승으로 인플레이션 압력이 높아질 것으로 전망됩니다.
✅ GOOD: 이번 유가 반등은 공급 제약 없이 수요 회복에서 비롯됐습니다.
         인플레이션 이전에 실적 개선 신호가 먼저 나타나는 구조여서,
         금리에 선행해 정유·화학 이익 추정치가 상향될 가능성이 높습니다.
```

쌍의 수: 5개 (유가/인플레, 금리/밸류, 이익추정치, 변동성, 불확실성)

### B2. Analytical Spine Enforcement (`_P14_ANALYTICAL_SPINE_ENFORCEMENT`)

`<!-- SPINE: [논지 요약] -->` HTML 주석을 Post1 첫 줄에 삽입하도록 강제.

형식 요건:
```html
<!-- SPINE: [팩트 X]와 [팩트 Y] 동시 발생 → [투자 프레이밍 Z] 우선 -->
```

### B3. Hedge Direct Prohibition (`_P14_HEDGE_DIRECT_PROHIBITION`)

이미 지난 날짜에 전망 동사 사용 금지 명시:
- `것으로 예상됩니다 / 파악됩니다 / 추정됩니다` → 확정 사실 서술 시 금지
- `보입니다 / 것으로 보입니다` → 팩트 직접 서술로 대체 지시

### B4. Post2 Continuation (`_P14_POST2_CONTINUATION_TEMPLATE`)

`post1_spine` 문자열을 Post2 user_msg 맨 앞에 주입:

```
[Post1 핵심 논지 — 이미 확립된 프레임]
{post1_spine}

Post2 작성 지침:
- 위 논지를 전제로 시작하십시오. 매크로/테마 배경을 재설명하지 마십시오.
- Post1이 끝난 시점에서 연속 작성: 구체적 종목·섹터·포지셔닝으로 즉시 진입.
```

**`gpt_write_picks()`의 새 파라미터:** `post1_spine: str = ""`

### B5. `_P14_POST1_ENFORCEMENT_BLOCK`

= spine + few-shot + hedge prohibition 세 블록의 합. 모든 Post1/Post2 생성 시 주입.

---

## Track C — Rewrite Enforcement Loop (재작성 루프)

### 목적

Phase 13이 weak interpretation을 탐지하면 → 발행을 허용하는 것이 아니라 → 재작성을 시도.

### `_enforce_interpretation_rewrite(content, weak_interp_hits, label="")`

```
조건: weak_interp_hits >= 3
액션: Gemini에게 타겟 재작성 요청
반환: 재작성된 HTML (또는 길이 < 70% 시 원본)
```

**트리거 기준:** `weak_interp_hits >= 3` (Phase 13 `_score_interpretation_quality()` 반환값)

**`GEMINI_INTERP_REWRITE_SYSTEM`** 주요 지시:
```
당신은 금융 분석 문장을 '교과서 인과관계 → 비자명적 해석'으로 업그레이드하는 편집자.
다음 패턴을 반드시 교체:
  - "유가 상승 → 인플레이션" 수준의 직접 연결
  - 카테고리 이름만 나열하는 반론
  - 전망 어미로 서술된 확정 팩트
```

**안전 장치:**
- 재작성 길이 < 원본의 70% → 원본 반환
- `<!-- PICKS: ... -->` 주석 보존 (종목 결정 이유 태그)

### 재작성 후 재진단

`generate_deep_analysis()`와 `generate_stock_picks_report()`에서:
```python
weak_hits = p13_interp.get("weak_interp_hits", 0)
final_content = _enforce_interpretation_rewrite(final_content, weak_hits, label="Post1")
if weak_hits >= 3:
    p13_interp = _score_interpretation_quality(final_content, label="Post1-재작성후")
```

---

## Track D — Numeric Sanity Recalibration

### Phase 13 → Phase 14 범위 변경

| 지수 | Phase 13 범위 | Phase 14 SUSPICIOUS 범위 | Phase 14 HARD_FAIL 범위 |
|---|---|---|---|
| KOSPI | 1,800 – 4,500 | **1,500 – 8,000** | 100 – 50,000 |
| KOSDAQ | 500 – 1,800 | **400 – 4,000** | 50 – 20,000 |
| USD/KRW | 1,050 – 1,800 | **900 – 2,500** | 100 – 5,000 |

**목적:** 2026+ 시장 레벨 (KOSPI 5,500+)에서 false positive HOLD 제거.

### 2단계 티어 로직

```
HARD_FAIL:  명백한 자릿수 오류 (KOSPI 99,999)
SUSPICIOUS: 광역 범위 이탈이지만 현실 가능 (KOSPI 8,500)
```

**FAIL 조건 변경:**
- Phase 13: `suspicious >= 1` → HOLD
- Phase 14: `hard_fail_count >= 1` OR `suspicious_count >= 2` → HOLD
- `suspicious_count == 1` 단독 → WARN만, HOLD 아님

---

## main.py 게이트 블록 변경

### Phase 14 신규 키

| 키 | 의미 |
|---|---|
| `source_normalization` | _normalize_source_for_generation 호출 여부 |
| `fact_forecast_separation` | CONFIRMED/FORECAST/AMBIGUOUS 분류 블록 생성 여부 |
| `analytical_spine_enforcement` | <!-- SPINE: --> 주석 Post1에 존재 여부 (PASS/WARN) |
| `post2_continuation_enforcement` | post1_spine → Post2 주입 여부 (PASS/WARN) |
| `weak_interpretation_rewrite_loop` | 재작성 루프 배선 여부 |
| `numeric_sanity_recalibration` | _P14_SANITY_RANGES 사용 여부 |
| `phase13_compatibility` | Phase 13 진단 키 유지 여부 |
| `public_signature_stability` | gpt_write_picks 서명 호환 여부 |

### HOLD 조건 변경

```python
# Phase 13:
temporal_status == "FAIL"
OR suspicious_count >= 1

# Phase 14:
temporal_status == "FAIL"
OR (p1_hf + p2_hf) >= 1  # hard_fail_count only
```

`suspicious_count` 단독으로는 더 이상 HOLD를 유발하지 않음.

---

## Phase 13 호환성

Phase 13에서 도입된 모든 항목은 유지:
- `_score_interpretation_quality()` — 유지, Track C 재작성 트리거로 추가 활용
- `_check_temporal_sanity()` — 유지, HOLD 조건 그대로
- `_P13_WEAK_INTERP_PATTERNS` — 유지, Track C 재작성 프롬프트 생성에 사용
- `_P13_POST1_INTELLIGENCE_RULES`, `_P13_POST2_INTELLIGENCE_RULES` — 유지, user_msg 체인에 그대로 포함
- Phase 13 게이트 키 12개 — 모두 유지

---

## 실행 흐름 (Phase 14 이후)

```
[소스 데이터]
     │
     ▼
_normalize_source_for_generation()          ← Track A
     │  → CONFIRMED/FORECAST/AMBIGUOUS 블록
     ▼
gpt_write_analysis() / gpt_write_picks()
     │  user_msg = continuation_block        ← Track B (Post2만)
     │            + _P14_POST1_ENFORCEMENT_BLOCK  ← Track B (few-shot + spine + hedge)
     │            + source_norm_block         ← Track A
     │            + Phase 13 rules
     │            + Phase 12 rules
     │            + slot_hint
     │            + 원본 프롬프트
     ▼
GPT 초안 생성
     │
     ▼
Gemini Step3 verifier + 수정
     │
     ▼
Phase 13 진단: _score_interpretation_quality()
                _check_temporal_sanity()
                _check_numeric_sanity()        ← Track D (재보정 범위)
     │
     ▼
weak_interp_hits >= 3?
     │ Yes → _enforce_interpretation_rewrite()  ← Track C
     │         → Gemini 재작성
     │         → _score_interpretation_quality() 재진단
     │ No  → 그대로
     ▼
_extract_post1_spine()                         ← Track B-4
     │  → post1_spine → Post2 generation에 전달
     ▼
Phase 14 게이트 판정 (main.py)
```

---

## 검증 체크리스트

| 항목 | 방법 | 기대 결과 |
|---|---|---|
| 소스 정규화 함수 동작 | `_normalize_source_for_generation(test_mats, "2026-03-16")` 호출 | CONFIRMED/FORECAST 블록 출력 |
| 팩트/전망 분류 정확도 | 과거날짜+확정동사 → CONFIRMED, 미래날짜 → FORECAST | 카테고리 정확 |
| Few-shot 블록 존재 | `len(_P14_FEWSHOT_BAD_GOOD_INTERP) > 200` | True |
| SPINE 주석 추출 | `_extract_post1_spine('<!-- SPINE: X --><p>...</p>')` | 'X' 반환 |
| Post2 continuation 주입 | `gpt_write_picks(..., post1_spine="X")` → user_msg에 X 포함 | 포함 확인 |
| 재작성 스킵 (hits<3) | `_enforce_interpretation_rewrite(content, 2)` | 원본 그대로 |
| KOSPI 5800 PASS | `_check_numeric_sanity('코스피지수 5,800p')` | hard_fail_count=0 |
| KOSPI 99999 패턴 | `_check_numeric_sanity('KOSPI 99,999 pt')` | hard_fail_count >= 1 |
| Phase 13 키 유지 | main.py gate block에 interpretation_quality_p1 등 | 존재 |
| gpt_write_picks 서명 | `inspect.signature(gpt_write_picks)` | post1_spine 파라미터 포함 |
| 빌드 통과 | `python3 -c "import generator, main"` (venv) | 오류 없음 |

---

## 리스크 및 후속 항목

### 리스크

| 리스크 | 영향 | 완화 |
|---|---|---|
| Gemini 재작성이 원본보다 짧아짐 | 길이 < 70% 시 원본 복원 로직으로 완화 | 70% 임계값 조정 가능 |
| Few-shot 예시가 시장 상황과 맞지 않을 수 있음 | 일부 해석이 맥락 부합 안 할 수 있음 | 실제 발행물 검토 후 예시 교체 필요 |
| SPINE 주석이 GPT에 의해 생성 안 될 수 있음 | post1_spine이 빈 문자열 → Post2 continuation 블록 미주입 | [해석] / 80자 문장 fallback으로 대응 |
| Track A 분류가 단순 키워드 기반 | 복잡한 한국어 문장 엣지케이스 오분류 가능 | AMBIGUOUS 카테고리로 안전하게 처리 |

### 후속 항목

1. **실제 발행물 검증** — Phase 14 이후 신규 발행 기사 2개 이상에서 spine/fewshot 효과 측정
2. **Few-shot 예시 갱신** — 실제 시장 데이터 기반으로 BAD→GOOD 쌍 교체 (6개월마다)
3. **재작성 루프 임계값 조정** — `weak_interp_hits >= 3` → 실제 발행 품질에 맞게 재보정
4. **KOSPI 범위 재검토** — 2026년 연말 시장 레벨 확인 후 _P14_SANITY_RANGES 재조정

---

*작성일: 2026-03-16 | Phase: 14 | 이전: [handoff_phase13.md](handoff_phase13.md)*
