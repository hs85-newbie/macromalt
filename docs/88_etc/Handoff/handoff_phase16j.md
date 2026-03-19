# handoff_phase16j.md

> Phase 16J — PARSE_FAILED 운영 표준화 + Theme Rotation 운영 규칙 보강
> 완료일: 2026-03-19
> 판정: **PHASE16J_IMPL_GO**

---

## 실행 정보

| 항목 | 값 |
|------|---|
| 대상 Phase | 16J (Phase 16I CONDITIONAL GO 잔여 이슈 마감) |
| 선행 Phase | 16I (CONDITIONAL GO — 2개 잔여 이슈 확인) |
| 구현 범위 | generator.py — 표준화 + 운영 규칙 보강 (구조 개편 없음) |

---

## Track A — PARSE_FAILED 운영 표준화

### 선택: Option A (독립 상태 유지)

`PARSE_FAILED`와 `FAILED_NO_REVISION`은 런타임 의미가 다르다:

| 상태 | 발생 조건 | 수정 시도 | 발행 경로 |
|------|---------|---------|---------|
| `FAILED_NO_REVISION` | Gemini verifier 호출 성공 → 이슈 발견 → 수정 API 실패 | 있음 (실패) | GPT 초안 원본 |
| `PARSE_FAILED` | Gemini verifier 응답 반환 → JSON 파싱 불가 | 없음 | GPT 초안 원본 |

### 변경 내용

| 위치 | 변경 |
|------|------|
| `verify_draft()` log | `[Phase 16J]` 태그 + "검수 단계 skip, GPT 초안 원본 발행, 수정 시도 없음" 명시 |
| `verify_draft()` enum 주석 | `PARSE_FAILED` 4번째 표준 상태로 추가, FAILED_NO_REVISION과의 차이 설명 |
| `_p16b_emergency_polish()` docstring | step3_status 목록에 `PARSE_FAILED` 추가 |
| Post1/Post2 `p16b_guard` | `"parse_failed": bool` 필드 추가 |

### 운영 해석 기준 (이제부터)

로그에서 `[Phase 16J] Step3 검수 결과 파싱 실패 (step3_status=PARSE_FAILED)` 발견 시:
- 이번 Post의 Step3 검수는 실질 미실행
- 발행은 정상 진행됨 (GPT 초안 원본)
- 대응: Gemini 응답 포맷 확인, 다음 run 모니터링

---

## Track B — Theme Rotation / Continuity 운영 규칙 보강

### 구현: 방향 3 + 방향 4

#### 신규 함수: `_p16j_check_theme_repeat(current_theme: str) -> dict`

- Phase 11의 `_make_theme_fingerprint()` + `_load_publish_history()` 재사용
- 현재 theme_fp가 최근 이력에 존재하면 `is_repeat=True`, WARNING 로그 출력
- `기타` fingerprint는 진단 제외

```
반환:
{
  "is_repeat":    bool,   # True = 동일 theme_fp 이력 있음
  "repeat_count": int,    # 이력 내 동일 theme_fp 건수
  "theme_fp":     str,    # 현재 theme fingerprint
  "matched_slots": list,  # 최근 3건 {slot, published_at, post1_title}
}
```

#### 신규 상수: `_P16J_POST2_SAME_THEME_OPENER`

- repeat 감지 시 `gpt_write_picks()` user_msg에 조건부 주입
- 강제 각도: ① 픽 바스켓의 공통 민감도 / ② 왜 이 종목들인가 / ③ 어떤 트리거에 베팅하는가
- 기존 `_P16B_POST2_ANGLE_DIVERSIFICATION` 앞에 삽입 (더 구체적인 상황별 지침)

#### `p16b_guard` 신규 필드

```python
# Post2 p16b_guard
"theme_repeat_diag": {
    "is_repeat":    True/False,
    "repeat_count": int,
    "theme_fp":     "에너지_유가|지정학_전쟁",
    "matched_slots": [...]
}
```

---

## 비침범 확인

| 항목 | 상태 |
|------|------|
| temporal SSOT (Phase 15D/15E/15F) | 비침범 ✅ |
| intro_overlap 계산식 | 비침범 ✅ |
| bridge_diag 기본 로직 | 비침범 ✅ |
| step3_status PASS/REVISED/FAILED_NO_REVISION 의미 | 비침범 ✅ |
| hedge_overuse_p1 로직 | 비침범 ✅ |
| verifier_revision_closure 구조 | 비침범 ✅ |
| Phase 11 history_context | 비침범 ✅ |

---

## Phase 16 계열 성과 요약

| Phase | 핵심 성과 |
|-------|---------|
| 16A | temporal SSOT 기반 구축 |
| 16B | emergency_polish, intro_overlap, generic_wording 진단 |
| 16C | 실출력 검증 1차 |
| 16D | Post2 macro 재서술 억제, bridge 강제 |
| 16E | 실출력 검증 2차 (bridge mismatch 발견) |
| 16F | bridge-pick 정합성 강화, step3_status 표준화, bridge_diag |
| 16G | 실출력 검증 3차 (intro_overlap HIGH→LOW/MEDIUM) |
| 16H | hedge 절제, closure false fail 완화, polish 집계 단일화 |
| 16I | 실출력 검증 4차 — Track A/B/C 효과 확인, CONDITIONAL GO |
| **16J** | **PARSE_FAILED 표준화 + Theme Rotation 운영 규칙 보강 → Phase 16 계열 종료** |

---

## 코드 핵심 변경 위치

| 파일 | 위치 | 변경 |
|------|------|------|
| `generator.py` | `_p16j_check_theme_repeat()` (~line 224) | 신규 함수 — theme 연속 진단 |
| `generator.py` | `_P16J_POST2_SAME_THEME_OPENER` (~line 3210) | 신규 상수 — 동일 theme opener 강화 |
| `generator.py` | `verify_draft()` (~line 5324) | 로그 강화 + enum 주석 확장 |
| `generator.py` | `gpt_write_picks()` (~line 5220) | `same_theme_hint` 파라미터 추가 |
| `generator.py` | `generate_stock_picks_report()` (~line 5736) | theme 진단 + hint 전달 |
| `generator.py` | Post1/Post2 `p16b_guard` | `parse_failed`, `theme_repeat_diag` 필드 추가 |

---

## 다음 세션 우선순위

1. **Phase 17 설계 시작**:
   - Gemini JSON 파싱 견고성 강화 (PARSE_FAILED 근본 원인 제거)
   - `post1_post2_continuity` 정량 개선 검증 (실출력에서 16J opener 규칙 효과 확인)
   - 슬롯 theme rotation 강화 (Phase 11 STRONG 감지 범위 확대 검토)
2. **다음 run 모니터링**:
   - `p16b_guard.parse_failed` 필드 정상 출력 확인
   - 동일 theme 연속 시 `[Phase 16J] 동일 theme 연속 감지` 로그 확인
   - `post1_post2_continuity` 개선 여부 관찰
