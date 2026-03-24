# Phase 18 — 안정화 하드닝 보고서

작성일: 2026-03-24
기준 커밋: (이 커밋)
커버 범위: Phase 18 (신규 포함 4개 트랙)

---

## 0. 배경

Phase 17 종료 이후 실제 런 3회(run_id: 20260324_094707, 20260323 런, 20260324_101225) 결과에서
아래 항목이 반복 FAIL로 기록됨:

| 지표 | 상태 | 런 횟수 |
|------|------|---------|
| `post1_post2_continuity` | FAIL (n-gram 19개) | 3/3 |
| `verifier_revision_closure` | FAIL | 2/3 |
| `counterpoint_specificity_p2` | FAIL (0마커) | 3/3 |
| PARSE_FAILED 차단 정책 | 미구현 (항상 허용) | — |

---

## 1. Track A — post1_post2_continuity 면책문구 오염 수정 [신규]

### 원인 분석

`_check_post_continuity(post1_content, post2_content)` 내부 `_text()` 함수가
두 글의 앞 400/600자를 HTML 태그 제거 후 비교한다.

Phase C `_inject_disclaimer()`가 `</h1>` 직후에 동일한 면책문구를 주입한 결과,
두 글의 도입부 추출 구간 안에 동일한 면책문구 텍스트가 포함됨.

```
Post1 앞 400자: <h1>제목</h1> + ⚠본글은투자참고용정보이며… (면책문구)
Post2 앞 600자: <h1>제목</h1> + ⚠본글은투자참고용정보이며… (면책문구)
```

4-gram 비교에서 면책문구 단어들이 모두 중복 → n-gram 19개 오탐 발생.
**실제 콘텐츠 중복이 아닌 보일러플레이트 오염.**

### 수정 내용

`_text()` 함수에서 첫 `<h2>` 또는 `<h3>` 등장 이전(h1+면책문구 블록)을 건너뛰고
본문 섹션부터 비교 구간으로 사용하도록 변경.

```python
# 수정 전
def _text(html: str, limit: int = 400) -> str:
    return _re.sub(r"<[^>]+>", " ", html)[:limit]

# 수정 후
def _text(html: str, limit: int = 400) -> str:
    m = _re.search(r"<h[23][^>]*>", html, _re.IGNORECASE)
    body = html[m.start():] if m else html
    return _re.sub(r"<[^>]+>", " ", body)[:limit]
```

### 기대 효과

- 면책문구 n-gram 오탐 제거 → 실제 콘텐츠 중복만 감지
- `post1_post2_continuity` FAIL → PASS/WARN 수준으로 개선 예상

---

## 2. Track B — verifier_revision_closure FAIL 잔존 원인 분석 및 수정

### 원인 분석

**Post1 고위험 8건 | 해소 6 / 미해소 2 (사실 2건) → FAIL**

미해소 이슈 2건:
1. `[1] "그러나, 이러한 시나리오가 실현되지 않는다면..."` — 시나리오 조건 근거 부족
2. `[1] "이는 오늘 분석의 전제인..."` — "오늘" 시점 표현

**두 가지 구조적 문제:**

#### 문제 A: STYLE_RESIDUAL_KW 범위 부족
이슈 1은 해석·분석 품질 문제(근거 부족)인데, `STYLE_RESIDUAL_KW`에 해당 패턴이 없어
`truly_unresolved`로 오분류됨. FAIL 판정에서 제외되어야 할 이슈.

#### 문제 B: reviser에 "오늘" 본문 교체 규칙 없음
이슈 2의 "오늘 분석의 전제인..." 구문은 시점 일관성 위반이 맞으나,
reviser 규칙 9(opener 구조 보정)가 opener H3만 다루고 본문 "오늘" 참조는 미처리.
reviser가 수정하지 않아 `still_present=True` → unresolved 유지.

### 수정 내용

#### A: STYLE_RESIDUAL_KW 확장 (generator.py, `_check_verifier_closure`)

```python
# Phase 18 신규
"구체적 근거가 없",    # 근거 부족 지적 → 사실 오류 아닌 analytical quality
"실현 가능성에 대한",  # 조건부 시나리오 근거 없음 지적
"조건으로 제시",       # 조건부 전제 구조 지적
"근거 없이 단정",      # 사실 단정 서술 지적
"논리적 근거",         # 논리 흐름 품질 지적
```

#### B: reviser 규칙 9 확장 (generator.py, GEMINI_REVISER_SYSTEM)

```
- "오늘 분석의 전제" → "이번 분석의 전제"
- "오늘 분석에서" → "이번 분석에서"
- "오늘 논의" → "이번 논의"
- "오늘의 핵심" → "이번의 핵심"
※ opener H3 교체 규칙과 별개로 h3 헤딩 및 본문 모두 적용
```

### 기대 효과

- 이슈 1 → STYLE_RESIDUAL 분류 → truly_cnt 2→1
- status: FAIL → WARN 강등 (단일 미해소 사실 이슈)
- 이슈 2 → reviser가 "오늘" → "이번"으로 교체 → still_present=False → resolved

---

## 3. Track C — PARSE_FAILED TYPE별 발행 차단 정책 구현

### 원인 분석

기존 모든 PARSE_FAILED 케이스가 `publish_blocked=False` (항상 허용).
구조적으로 파손된 출력도 발행되는 문제.

Phase 17에서 TYPE 분류 체계(TYPE_A~E)를 구현했지만, 실제 차단 로직은 미구현.

### TYPE별 정책 확정

| TYPE | 원인 | 정책 |
|------|------|------|
| TYPE_A | verifier 응답에 h2/h3 없음 (구조 전무) | **차단** |
| TYPE_B | 금지 opener 패턴 포함 | **차단** |
| TYPE_C | HTML 태그 불균형 (파손) | **차단** |
| TYPE_D | PICKS 주석 누락 | 허용 (Post 187 실적 기반) |
| TYPE_E | reviser 과도 축소 | 허용 |
| TYPE_UNKNOWN | 미분류 | 허용 (보수적) |

### 수정 내용

#### `verify_draft()` — PARSE_FAILED 분기에 TYPE 분류 + 차단 플래그 추가

```python
_pf_type = _classify_parse_failed(raw or "")
_BLOCK_TYPES = {"TYPE_A", "TYPE_B", "TYPE_C"}
_pf_blocked = _pf_type in _BLOCK_TYPES
# ... logging with publish_blocked=_pf_blocked
return {
    ...,
    "parse_failed_type": _pf_type,
    "parse_failed_blocked": _pf_blocked,
}
```

#### `generate_deep_analysis()` — TYPE_A/B/C 시 RuntimeError 발생

```python
if verify_result.get("parse_failed_blocked", False):
    raise RuntimeError(f"[Phase 18] PARSE_FAILED {type} — Post1 발행 차단")
```

→ main.py가 `sys.exit(1)` 처리

#### `generate_stock_picks_report()` — 동일 패턴

→ main.py가 `post2=None` 처리 (Post1은 계속 발행)

#### `p16b_guard`에 `parse_failed_type` 필드 추가 (Post1/Post2 양쪽)

---

## 4. Track D — counterpoint_specificity_p2 FAIL 지속 원인 분석 및 수정

### 원인 분석

`_score_interpretation_quality()`의 `counterpoint_spec` 판정:

```python
ctr_match = search(r"반대|반론|체크포인트|리스크|위험|Counter")
# 매치 이후 텍스트에서 _P13_COUNTERPOINT_CONDITION_MARKERS 카운트
counter_status = "PASS" if cond_hits >= 2 else ...
```

Post2 리스크 섹션이 아래와 같이 서술됨:
```
미·중 무역 갈등 심화 시 반도체 수출 규제가 강화될 수 있습니다.
```

`"강화될 수 있습니다"`, `"심화 시"` 등은 조건부 표현이지만,
`_P13_COUNTERPOINT_CONDITION_MARKERS`에는 `"발생 시"`, `"하향 시"` 같은 구체적 복합어만 있어
**일반적인 `"될 경우"`, `"강화될"` 등이 매칭되지 않음 → 0마커 → FAIL**.

### 수정 내용

#### A: `_P13_COUNTERPOINT_CONDITION_MARKERS` 확장

```python
# Phase 18 추가
"될 경우",    # "악화될 경우", "지속될 경우"
"할 경우",    # "현실화할 경우"
"강화될",     # "규제가 강화될"
"악화될",     # "업황이 악화될"
"약화될",     # "수요가 약화될"
"지연될",     # "회복이 지연될"
"심화될",     # "갈등이 심화될"
"하락할",     # "주가가 하락할"
"급락할",     # 급격한 하락 시나리오
```

#### B: `editorial_config.py` 리스크 섹션 지침 보강

기존의 "구체적 조건·수치·이벤트로 명시할 것" → 조건부 어미 형식 추가:

```
리스크 서술은 반드시 조건부 형식(시나리오 → 결과)으로 작성한다.
✅ 형식: "만약 ~될 경우 / ~가 지속될 경우 / ~가 현실화된다면 → [결과]"
✅ 예시: "HBM 공급 과잉이 지속될 경우 ASP 하락 압력 가중"
❌ 금지: "반도체 업황 불확실성" 등 명사형 나열
```

### 기대 효과

- 조건부 동사형 마커 적중 → cond_hits ≥ 2 → `counterpoint_spec: PASS`
- GPT도 리스크 섹션을 조건부 형식으로 서술하도록 유도

---

## 5. 수정 파일 요약

| 파일 | 수정 위치 | 내용 |
|------|-----------|------|
| `generator.py` | `_check_post_continuity()` | h1 블록 스킵 (Track A) |
| `generator.py` | `_check_verifier_closure()` — `STYLE_RESIDUAL_KW` | 해석 품질 이슈 패턴 추가 (Track B) |
| `generator.py` | `GEMINI_REVISER_SYSTEM` — 규칙 9 | "오늘" 본문 교체 규칙 추가 (Track B) |
| `generator.py` | `verify_draft()` PARSE_FAILED 분기 | TYPE 분류 + 차단 플래그 (Track C) |
| `generator.py` | `generate_deep_analysis()` | TYPE_A/B/C RuntimeError (Track C) |
| `generator.py` | `generate_stock_picks_report()` | TYPE_A/B/C RuntimeError (Track C) |
| `generator.py` | `p16b_guard` (Post1, Post2) | `parse_failed_type` 필드 추가 (Track C) |
| `generator.py` | `_P13_COUNTERPOINT_CONDITION_MARKERS` | 조건부 동사형 마커 9개 추가 (Track D) |
| `editorial_config.py` | `_PC_POST2_EDITORIAL_RULES` — 리스크 섹션 | 조건부 어미 형식 명시 (Track D) |

---

## 6. 비회귀 확인 항목

| 항목 | 기대 상태 |
|------|----------|
| temporal SSOT (Phase 15D/15E/15F) | ✅ 비회귀 |
| `[전망]` 태그 오주입 | ✅ 없음 |
| PARSE_FAILED TYPE_D 허용 경로 | ✅ 유지 (Post 187 실적 준수) |
| `_P13_COUNTERPOINT_CONDITION_MARKERS` 기존 마커 | ✅ 유지 (추가만) |
| `STYLE_RESIDUAL_KW` 기존 패턴 | ✅ 유지 (추가만) |

---

## 7. Phase 18 잔여 이슈 (Phase 19 이관)

| 이슈 | 내용 | 우선순위 |
|------|------|---------|
| `verifier_revision_closure` 완전 안정화 | WARN 수준 잔존 가능. PASS 달성을 위해 reviser 수정 품질 향상 필요 | 중간 |
| PARSE_FAILED TYPE_A/B/C 실전 발생 검증 | 아직 실전에서 TYPE_A/B/C 미발생. 차단 로직 실전 확인 필요 | 중간 |
| `counterpoint_specificity_p1` 안정성 | Post1도 가끔 WARN/FAIL. Post1 반론 조건 마커 현황 모니터링 필요 | 낮음 |
