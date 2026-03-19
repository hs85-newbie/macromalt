# Handoff — Phase 16B: Output Quality Hardening

작성일: 2026-03-19
커밋: f4f0e6a
게이트: PHASE16B_IMPL_GO (코드 구현 완료 / 실출력 검증 미수행)

---

## 1. 이 Phase에서 한 일

Phase 16A GO 이후 남은 품질 위험 3가지를 해결하는 하드닝 레이어를 추가했다:

1. **Step3 503/timeout 시 품질 급락 방지** (Track A)
2. **Post1/Post2 도입부 n-gram 중복 감소** (Track B)
3. **Generic wording + analytical spine + premium tone 강화** (Track C/D)

Temporal SSOT (Phase 16) 회귀 없음.

---

## 2. 변경된 코드 요약

### 신규 추가 (generator.py)

| 항목 | 역할 |
|------|------|
| `_P16B_QUALITY_HARDENING_RULES` | GPT Post1/Post2 공통 품질 지시 블록 |
| `_P16B_POST2_ANGLE_DIVERSIFICATION` | Post2 도입부 각도 차별화 GPT 지시 |
| `_P16B_GENERIC_MARKERS` | emergency polish 탐지 마커 목록 (15개) |
| `_p16b_emergency_polish(content, label)` | Step3 실패 시 generic 진단 (치환 없음) |
| `_p16b_compute_intro_overlap(p1, p2, n=4)` | 도입부 4-gram 중복률 계산 |

### 수정된 기존 함수

| 함수 | 변경 내용 |
|------|----------|
| `verify_draft()` | `step3_status` 반환 추가 |
| `gpt_write_analysis()` | `_P16B_QUALITY_HARDENING_RULES` 주입 |
| `gpt_write_picks()` | angle diversification + quality hardening 주입 |
| `generate_deep_analysis()` | step3_status 추적, p16b_guard p13_scores 추가 |
| `generate_stock_picks_report()` | 동일 + intro_overlap 계산 |

---

## 3. 현재 파이프라인 실행 순서 (Post2 기준)

```
SSOT 구축 (_build_temporal_ssot)
  → SSOT GPT 주입 (_build_p16_generation_block)  ← Phase 16
  → GPT 생성 (gpt_write_picks)
    ← _P16B_POST2_ANGLE_DIVERSIFICATION           ← Phase 16B Track B
    ← _P16B_QUALITY_HARDENING_RULES               ← Phase 16B Track C/D
  → Step3 (verify_draft)
    → step3_status 기록                            ← Phase 16B Track A
  → emergency_polish (Step3 FAILED 시만)           ← Phase 16B Track A
  → Phase 15D/15E/15F 교정
  → _p16b_compute_intro_overlap                   ← Phase 16B Track B
  → p13_scores["p16b_guard"] 기록                 ← Phase 16B Track F
```

---

## 4. 진단 로그에서 확인할 것 (다음 런)

```
[Phase 16B] Post1 emergency polish: ...     ← Step3 실패 여부
[Phase 16B] 도입부 4-gram 중복: X.X% (LOW/MEDIUM/HIGH)
[Phase 16B] 도입부 HIGH 중복 감지 — ...    ← HIGH 시 WARN
```

p13_scores 필드:
```json
"p16b_guard": {
  "step3_status": "PASS|REVISED|FAILED_NO_REVISION",
  "fallback_triggered": false,
  "emergency_polish": {"status": "PASS|WARN|FAIL", "total_generic_found": N},
  "intro_overlap": {"overlap_ratio": 0.XX, "status": "LOW|MEDIUM|HIGH"}
}
```

---

## 5. 실출력 검증 체크리스트 (16B-Real 런용)

- [ ] `p16b_guard.step3_status` 로그 확인
- [ ] Post2 Step3 503 재발 시 `fallback_triggered=true` 확인
- [ ] `intro_overlap.status` — 16A 대비 LOW/MEDIUM 개선 여부
- [ ] Post2 도입부가 종목 직접 연결로 시작하는지 확인
- [ ] generic 마커 건수 16A 대비 감소 여부 (`emergency_polish.total_generic_found`)
- [ ] Temporal SSOT 비회귀: p16_ssot_run, p15f_strip 정상 여부

---

## 6. 남은 위험 (16C 판단 필요)

| 위험 | 심각도 | 참고 |
|------|--------|------|
| emergency_polish 실 치환 미수행 → generic 잔존 | MEDIUM | 16C에서 실 치환 추가 여부 결정 |
| angle diversification GPT 확률적 효과 | MEDIUM | HIGH overlap 지속 시 16C rewrite trigger 검토 |
| Step3 503 재발 구조적 문제 | LOW | retry 로직 16C 검토 |

---

## 7. 게이트 상태

| Phase | 게이트 |
|-------|--------|
| Phase 16 | PHASE16_IMPL_GO |
| Phase 16A | PHASE16A_OUTPUT_GO |
| **Phase 16B** | **PHASE16B_IMPL_GO** (실출력 검증 대기) |
| Phase 16C | 미수행 |
