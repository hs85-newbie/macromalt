# handoff_phase16h.md

> Phase 16H — 운영 안정화 및 잔여 품질 정리
> 완료일: 2026-03-19
> 판정: PHASE16H_IMPL_GO

---

## 변경 요약

### Track A — Post1 hedge_overuse 완화

**What**: `_P16H_POST1_HEDGE_REDUCTION` 상수 추가 → `gpt_write_analysis()` user_msg 선두 주입

**Why**: Phase 14I의 [해석] 블록 재작성이 HTML 노출 없어 0건 추출 → 사후 교체 무효. GPT 생성 단계에서 factual spine 헤징 직접 억제가 필요.

**Effect**: factual spine 구간("확정 수치, 과거 발표")에 유보형 어미 금지. 해석/전망 구간의 hedge는 유지.

**Target metric**: hedge_overuse_p1 FAIL(>50%) → WARN(30~50%) 이하

---

### Track B — verifier_revision_closure false fail 완화

**What**: `_check_verifier_closure()` 에 `STYLE_RESIDUAL_KW` 분류 레이어 추가

**Why**: 16G run2에서 [10](숫자가 없는 문단 구조), [13](완충 문장/4요소) 2건이 style/writing quality 이슈임에도 FAIL 트리거 → false fail

**New logic**:
- `truly_unresolved`: STYLE_RESIDUAL_KW 미포함 → 사실 오류 미해소 → FAIL 판정에 포함
- `style_residual`: STYLE_RESIDUAL_KW 포함 → 서술 품질 → WARN으로 강등
- FAIL 기준: `truly_unresolved_cnt >= 2` (style_residual만 있으면 WARN)

**16G run2 소급**: truly=0건, style=2건 → WARN (기존 FAIL → WARN)

**Result dict 신규 필드**:
- `truly_unresolved_count`
- `style_residual_count`
- `closure_reason` (운영 가독용 요약)

---

### Track C — emergency_polish 집계 기준 단일화

**What**: `_p16b_emergency_polish()` 집계 필드 분리 + 로그 형식 개선

**Phase 16H 표준 기준**:
| 필드 | 의미 |
|------|------|
| `unique_marker_count` | 서로 다른 마커 종류 수 |
| `total_occurrence_count` | 마커 총 출현 횟수 |

**로그 형식 (Phase 16H 이후)**:
```
[Phase 16B] Post2 emergency_polish: generic 마커 3종 5건 | status=WARN | ...
```

**하위호환**: `total_generic_found` 필드 유지 (= total_occurrence_count)

**보고서 기재 기준**: `{unique_marker_count}종 {total_occurrence_count}건` 형식 사용

---

## 16G GO 축 비회귀 확인

| 축 | 상태 |
|----|------|
| temporal SSOT (15D/15E/15F) | 비침범 |
| bridge-pick 정합성 (_p16f_diagnose_bridge) | 비침범 |
| step3_status enum (PASS/REVISED/FAILED_NO_REVISION) | 비침범 |
| intro_overlap 기본 로직 | 비침범 |
| emergency_polish 관측 | 보존 + 개선 |

---

## 다음 세션 체크리스트

- [ ] 실출력 실행 (Phase 16I 또는 다음 실출력 검증)
- [ ] Post1 hedge_overuse WARN 이하 달성 확인
- [ ] verifier_revision_closure WARN/PASS 확인 (FAIL 탈출)
- [ ] 로그에서 `{N}종 {M}건` 형식 확인
- [ ] 16G GO 축 비회귀 확인

---

## 코드 핵심 변경 위치

| 파일 | 위치 | 변경 |
|------|------|------|
| `generator.py` | ~line 3117 | `_P16H_POST1_HEDGE_REDUCTION` 상수 추가 |
| `generator.py` | `gpt_write_analysis()` user_msg | `_P16H_POST1_HEDGE_REDUCTION` 선두 주입 |
| `generator.py` | `_check_verifier_closure()` | STYLE_RESIDUAL_KW + truly/style 분류 + closure_reason |
| `generator.py` | `_p16b_emergency_polish()` | unique_marker_count / total_occurrence_count 분리 |
