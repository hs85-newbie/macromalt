# REPORT_PHASE16J_THEME_ROTATION_AND_PARSEFAILED_STANDARDIZATION.md

> Phase 16J — Phase 16I CONDITIONAL GO 잔여 이슈 마감 정리
> 완료일: 2026-03-19
> 판정: **PHASE16J_IMPL_GO**

---

## 1. 작업 개요

Phase 16I에서 CONDITIONAL GO 판정의 근거가 된 두 잔여 이슈를
구조 개편 없이 **표준화 + 운영 회전 규칙 보강**으로 마감한다.

| 트랙 | 이슈 | 접근 |
|------|------|------|
| Track A | Post2 `step3_status = PARSE_FAILED` 운영 혼선 | Option A — 독립 상태 유지, 명확한 문서화 |
| Track B | `post1_post2_continuity FAIL` — 동일 theme 연속 | 방향 3 (opener 강화) + 방향 4 (진단 경고) |

---

## 2. 변경 파일 목록

| 파일 | 변경 유형 |
|------|---------|
| `generator.py` | Track A: enum 주석, 로그, docstring 업데이트 |
| `generator.py` | Track B: `_P16J_POST2_SAME_THEME_OPENER` 상수 추가 |
| `generator.py` | Track B: `_p16j_check_theme_repeat()` 함수 추가 |
| `generator.py` | Track B: `gpt_write_picks()` `same_theme_hint` 파라미터 추가 |
| `generator.py` | Track B: `generate_stock_picks_report()` theme 진단 + hint 전달 |
| `generator.py` | Post1/Post2 `p16b_guard` dict `parse_failed` 필드 추가 |
| `generator.py` | Post2 `p16b_guard` dict `theme_repeat_diag` 필드 추가 |

---

## 3. Track A — PARSE_FAILED 운영 표준화

### 선택지 결정: Option A (독립 상태 유지)

**Option B (FAILED_NO_REVISION 계열 통합) 미선택 이유:**
- `PARSE_FAILED`와 `FAILED_NO_REVISION`은 런타임 의미가 근본적으로 다르다.
  - `FAILED_NO_REVISION`: Gemini verifier 호출 성공 → 이슈 발견 → 수정 API 호출 실패 (503/timeout)
  - `PARSE_FAILED`: Gemini verifier 호출 성공 → 응답 반환 → JSON 파싱 실패 → 수정 시도 자체 없음
- 통합하면 "수정을 시도했으나 실패"와 "검수 결과를 읽지 못해 통과 처리" 사이의 의미가 뭉개진다.
- 운영 관점에서 두 상태는 재현 시 대응 방법도 다르다.
  - `FAILED_NO_REVISION` → 수정 API 재시도 또는 재실행
  - `PARSE_FAILED` → Gemini JSON fallback 강화, 응답 포맷 프롬프트 조정

### 구현 상세

#### 3-1. `verify_draft()` 로그 강화 (line ~5324)

**Before:**
```python
logger.warning("검수 결과 파싱 실패 — 통과로 처리")
```

**After:**
```python
logger.warning(
    "[Phase 16J] Step3 검수 결과 파싱 실패 (step3_status=PARSE_FAILED) "
    "— Gemini 응답이 JSON으로 파싱 불가 → 검수 단계 skip, GPT 초안 원본 발행 경로. "
    "FAILED_NO_REVISION과 달리 수정 시도 없이 즉시 통과 처리."
)
```

운영자가 로그에서 `PARSE_FAILED`를 봤을 때:
- `[Phase 16J]` 태그로 표준화된 상태임을 인식
- "검수 단계 skip" → 발행은 됐지만 Step3 품질 보호 없음
- "수정 시도 없이" → `FAILED_NO_REVISION`과 구분

#### 3-2. `verify_draft()` enum 주석 확장 (line ~5334)

```python
# Phase 16B/16F/16J step3_status enum (표준, Phase 16F에서 통일 / 16J에서 PARSE_FAILED 추가):
#   "PASS"              — Step3 팩트체크 이슈 없음 (검수 통과)
#   "REVISED"           — Step3 이슈 발견, 수정본 채택
#   "FAILED_NO_REVISION"— Step3 수정 API 실패 (503/timeout 등), GPT 초안 원본 발행
#   "PARSE_FAILED"      — [Phase 16J] Gemini 검수 응답 JSON 파싱 불가 → 검수 단계 skip.
#                         GPT 초안 원본 발행 (FAILED_NO_REVISION과 달리 수정 시도 자체 없음).
#                         운영 해석: verifier가 비표준 형식을 반환한 것 — 검수 실질 미실행.
#                         발행은 정상 진행되나 Step3 품질 보호 없이 발행됨.
```

#### 3-3. `_p16b_emergency_polish()` docstring 업데이트

`step3_status` 파라미터 설명에 `PARSE_FAILED` 명시 + 의미 설명 추가.

#### 3-4. `p16b_guard` dict — `parse_failed` 필드 추가

**Post1 p16b_guard:**
```python
"parse_failed": _p1_step3_status == "PARSE_FAILED",  # [Phase 16J]
```

**Post2 p16b_guard:**
```python
"parse_failed": _p2_step3_status == "PARSE_FAILED",  # [Phase 16J]
"step3_status": _p2_step3_status,  # PASS / REVISED / FAILED_NO_REVISION / PARSE_FAILED
```

운영자가 보고서/handoff에서 `p16b_guard.parse_failed = True`를 보면:
→ "이번 Post의 Step3 검수는 JSON 파싱 실패로 실질 미실행, GPT 초안 그대로 발행"

---

## 4. Track B — Theme Rotation / Continuity 운영 규칙 보강

### 구현 방향 선택: 방향 3 + 방향 4

- **방향 3 — Opening angle diversification 규칙 강화**: 동일 theme 연속 시 Post2 첫 2~3문단을 picker 논리 각도로 강제
- **방향 4 — 동일 theme 연속성 경고 진단**: 발행 전 운영자 경고 로그

방향 1 (penalty 부여), 방향 2 (role separation) 미선택 이유:
- 방향 1: 이미 Phase 11의 `_build_history_context()`에 유사 penalty 메커니즘 존재 (STRONG/BUCKET/MILD). 중복 레이어 추가는 비침범 원칙 위반.
- 방향 2: `_P16D_POST2_CONTINUITY_HARDENING`에 이미 role separation 원칙 포함. 추가 강화는 방향 3으로 충분.

### 4-1. `_P16J_POST2_SAME_THEME_OPENER` 상수 (방향 3)

```python
_P16J_POST2_SAME_THEME_OPENER: str = (
    "[Phase 16J — 동일 매크로 테마 연속 실행 감지: Post2 도입부 각도 강제 ★★]\n\n"
    "이번 슬롯은 직전 슬롯(들)과 동일한 거시 테마로 진행됩니다.\n"
    "Post2([캐시의 픽])의 첫 2~3문단은 반드시 아래 세 각도 중 하나로 열어야 합니다:\n\n"
    "  ① 픽 바스켓의 공통 민감도: '이 종목들이 같은 방향에 놓인 이유'\n"
    "  ② 왜 이 종목들인가: '같은 테마 중에서도 이 바스켓을 선택한 트리거 논거'\n"
    "  ③ 어떤 트리거에 베팅하는가: '오늘 이 특정 촉매에서 수혜 포지션'\n\n"
    "❌ 절대 금지 (동일 테마 연속 시 추가 제한):\n"
    "  - 매크로 배경을 이전 글과 같은 어휘·문장 구조로 재서술\n"
    "  - '이 테마가 중요한 이유' 식의 거시 설명으로 도입부 시작\n"
    "  - Post1 도입부와 유사한 흐름으로 같은 국면 설명 반복\n\n"
    "✅ 필수: 첫 문장부터 종목 선택의 논리 또는 투자 각도를 직접 제시하라.\n\n"
)
```

- **조건부 주입**: `_p16j_theme_diag["is_repeat"]`가 True일 때만 `gpt_write_picks()` user_msg에 삽입
- **비반복 시**: `same_theme_hint = ""` → 동작 변화 없음 (완벽한 비회귀)

### 4-2. `_p16j_check_theme_repeat()` 함수 (방향 4)

```python
def _p16j_check_theme_repeat(current_theme: str) -> dict:
    """Phase 16J Track B: 동일 macro theme 연속 슬롯 여부 진단."""
    theme_fp = _make_theme_fingerprint(current_theme)
    ...
    return {
        "is_repeat":    bool,   # True = 이력에 동일 theme_fp 있음
        "repeat_count": int,    # 이력 내 동일 theme_fp 건수
        "theme_fp":     str,    # 현재 theme fingerprint
        "matched_slots": list,  # 최근 3건 {slot, published_at, post1_title}
    }
```

**repeat 감지 시 로그:**
```
[Phase 16J] 동일 theme 연속 감지 | theme_fp=에너지_유가|지정학_전쟁 | 최근 2건 동일 theme 발행 이력 — Post2 opener 다양화 강화
  ⚠ [evening] 2026-03-19T14:17 | 이란 폭격으로 브렌트유 110달러
  ⚠ [morning] 2026-03-19T08:41 | 중동 지정학 리스크 3주차
```

**`기타` theme_fp**: 진단 제외 (미분류 theme는 Phase 11과 동일 기준).

### 4-3. `gpt_write_picks()` 파라미터 확장

```python
def gpt_write_picks(..., same_theme_hint: str = "") -> str:
```

user_msg 구성:
```python
user_msg = (
    _P15C_POST2_LABEL_BAN
    + _P16D_POST2_CONTINUITY_HARDENING
    + _P16D_POST2_BRIDGE_REQUIREMENT
    + same_theme_hint                   # Phase 16J: 동일 theme 반복 시 opener 강화 (조건부)
    + _P16B_POST2_ANGLE_DIVERSIFICATION
    + ...
)
```

삽입 위치 선택 이유:
- `_P16D_POST2_BRIDGE_REQUIREMENT` 뒤 → 브릿지 요구사항보다 상위 레이어(opener 방향)를 먼저 지시
- `_P16B_POST2_ANGLE_DIVERSIFICATION` 앞 → 기존 angle 지침을 덮지 않고 앞에서 상황별 강화

### 4-4. `generate_stock_picks_report()` 연동

```python
# ── Phase 16J Track B: 동일 theme 연속 진단 (opener 강화 + 경고)
_p16j_theme_diag = _p16j_check_theme_repeat(materials.get("theme", theme))
_p16j_same_theme_hint = (
    _P16J_POST2_SAME_THEME_OPENER if _p16j_theme_diag["is_repeat"] else ""
)

draft = gpt_write_picks(..., same_theme_hint=_p16j_same_theme_hint)
```

### 4-5. Post2 `p16b_guard` — `theme_repeat_diag` 필드 추가

```python
"theme_repeat_diag": _p16j_theme_diag,  # [Phase 16J Track B]: 동일 theme 연속 진단
```

운영자가 보고서에서 확인 가능:
- `theme_repeat_diag.is_repeat = True` → 이번 Post2에 opener 강화 프롬프트가 주입되었음
- `theme_repeat_diag.repeat_count` → 최근 몇 건 연속인지
- `theme_repeat_diag.matched_slots` → 어떤 슬롯이 반복이었는지

---

## 5. 비회귀 보호

### 비침범 항목 확인

| 항목 | 상태 |
|------|------|
| temporal SSOT (Phase 15D/15E/15F) | 비침범 ✅ |
| [전망] / [해석] 태그 규칙 | 비침범 ✅ |
| hedge_overuse_p1 로직 | 비침범 ✅ |
| verifier_revision_closure 기본 구조 | 비침범 ✅ |
| intro_overlap 계산식 | 비침범 ✅ |
| bridge_diag 기본 로직 | 비침범 ✅ |
| step3_status PASS/REVISED/FAILED_NO_REVISION 의미 | 비침범 ✅ |
| Phase 11 _build_history_context() | 비침범 ✅ |

### 비회귀 설계 근거

- **Track A**: 코드 동작 변화 없음. 로그 메시지·주석·dict 필드만 추가. `verify_draft()` 반환 딕셔너리 구조 변화 없음 (기존 4개 키 유지, `parse_failed` 키는 `p16b_guard`에 추가).
- **Track B**: `same_theme_hint = ""` 기본값 → repeat 미감지 시 동작 변화 없음. `_p16j_check_theme_repeat()`은 `publish_history.json` 읽기 전용. `theme_repeat_diag` 필드는 `p16b_guard`에 추가 (기존 필드 비침범).
- `gpt_write_picks()` 파라미터 `same_theme_hint: str = ""` — 기존 호출 코드는 변경 없이 동작 (기본값 `""`).

---

## 6. 자체 검증

### A. PARSE_FAILED 표준화

| 검증 항목 | 결과 |
|----------|------|
| 코드/로그/보고서/handoff가 같은 의미 체계를 쓰는가 | ✅ 모두 `[Phase 16J]` 태그 + 동일 설명 |
| 운영자가 상태를 보고 바로 이해할 수 있는가 | ✅ "검수 skip, GPT 초안 원본 발행" 명시 |
| 실제 파싱 실패와 수정 실패가 혼동되지 않는가 | ✅ enum 주석에 차이 명시, `parse_failed` bool 분리 |

### B. Continuity 운영 규칙

| 검증 항목 | 결과 |
|----------|------|
| 동일 theme 반복 시 Post2 각도 분산 장치가 생겼는가 | ✅ `_P16J_POST2_SAME_THEME_OPENER` 조건부 주입 |
| Post1 매크로 재서술 억제 규칙이 강화되었는가 | ✅ 방향 3 — 첫 문단 각도 강제 |
| slot/theme rotation 관련 경고나 penalty가 생겼는가 | ✅ `_p16j_check_theme_repeat()` — WARNING 로그 |

### C. 문법 검증

```
python3 -c "import ast; ast.parse(open('generator.py').read()); print('Syntax OK')"
# → Syntax OK
```

---

## 7. 잔여 위험

| 항목 | 내용 |
|------|------|
| PARSE_FAILED 재발 | 다음 run에서 재발 가능성 있음. 로그가 명확해졌으나 근본 원인(Gemini JSON 포맷)은 이번 페이즈 범위 밖. Phase 17에서 JSON fallback 강화 검토. |
| theme_repeat opener 실효성 | 같은 theme여도 `기타` fingerprint면 repeat 미감지. 미분류 theme는 이번 범위 밖. |
| `_p16j_check_theme_repeat` 는 publish 전에 실행됨 | 따라서 이번 슬롯 자체를 이력에 포함하지 않음 — 정상 동작 (save_publish_history는 발행 후 호출). |

---

## 8. 다음 실출력 검증 포인트 (Phase 17 또는 다음 run)

- `p16b_guard.parse_failed` 필드가 로그/보고서에서 읽히는가
- 동일 theme 2회 연속 run 시:
  - `[Phase 16J] 동일 theme 연속 감지` WARNING 로그 출력되는가
  - Post2 도입부가 픽 논리 각도로 시작하는가
  - `p16b_guard.theme_repeat_diag.is_repeat = True` 보고되는가
- `post1_post2_continuity` ngram 중복이 이전 대비 감소하는가
- 16G/16I 성과 축 (hedge 19%, closure PASS, intro_overlap MEDIUM) 비회귀 유지
