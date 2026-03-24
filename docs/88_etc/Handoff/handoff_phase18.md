# macromalt 핸드오프 — Phase 18 안정화 하드닝

작성일: 2026-03-24
기준 커밋: (이 커밋)
이전 문서: `handoff_total_phase5_to_phase17.md`
다음 단계: **Phase 19** — 런타임 안정성 검증 (Phase 18 수정 효과 확인)

---

## 1. Phase 18 개요

Phase 17 종료 후 실제 런 3회에서 반복 FAIL된 4개 항목을 구조적으로 수정.

| 트랙 | 수정 대상 | 결과 |
|------|-----------|------|
| A (신규) | `post1_post2_continuity` 면책문구 오염 | 수정 완료 |
| B (높음) | `verifier_revision_closure` FAIL 잔존 | 수정 완료 |
| C (높음) | PARSE_FAILED TYPE별 발행 차단 정책 | 구현 완료 |
| D (중간) | `counterpoint_specificity_p2` FAIL 지속 | 수정 완료 |

---

## 2. 주요 변경 위치 (generator.py)

| 함수/상수 | 위치 | Phase 18 변경 내용 |
|-----------|------|-------------------|
| `_check_post_continuity()` | ~line 1499 | `_text()` — h1 블록 스킵, h2/h3 이후부터 비교 |
| `_check_verifier_closure()` | ~line 1376 | `STYLE_RESIDUAL_KW` — 해석 품질 패턴 5개 추가 |
| `GEMINI_REVISER_SYSTEM` | ~line 5592 | 규칙 9 — "오늘" 본문 참조 교체 규칙 추가 |
| `verify_draft()` | ~line 6518 | PARSE_FAILED 분기 — TYPE 분류 + 차단 플래그 반환 |
| `generate_deep_analysis()` | ~line 6778 | `parse_failed_blocked` 체크 → RuntimeError |
| `generate_stock_picks_report()` | ~line 7113 | `parse_failed_blocked` 체크 → RuntimeError |
| `p16b_guard` (Post1) | ~line 6876 | `parse_failed_type` 필드 추가 |
| `p16b_guard` (Post2) | ~line 7249 | `parse_failed_type` 필드 추가 |
| `_P13_COUNTERPOINT_CONDITION_MARKERS` | ~line 1032 | 조건부 동사형 마커 9개 추가 |

---

## 3. PARSE_FAILED 차단 정책 (Phase 18 확정)

```python
BLOCK_TYPES = {"TYPE_A", "TYPE_B", "TYPE_C"}
# TYPE_A: verifier 응답에 h2/h3 없음 (구조 전무) → 차단
# TYPE_B: 금지 opener 패턴 포함 → 차단
# TYPE_C: HTML 태그 불균형 (파손) → 차단
# TYPE_D: PICKS 주석 누락 → 허용 (Post 187 실적 기반)
# TYPE_E: reviser 과도 축소 → 허용
# TYPE_UNKNOWN: 미분류 → 허용 (보수적)
```

Post1 차단 시: `RuntimeError` → main.py `sys.exit(1)`
Post2 차단 시: `RuntimeError` → main.py `post2 = None` (Post1은 계속 발행)

---

## 4. 품질 게이트 예상 변화

| 지표 | Phase 17 상태 | Phase 18 기대 |
|------|--------------|--------------|
| `post1_post2_continuity` | FAIL (n-gram 19개) | PASS (면책문구 오탐 제거) |
| `verifier_revision_closure` | FAIL (truly_cnt=2) | WARN (truly_cnt≤1) |
| `counterpoint_specificity_p2` | FAIL (0마커) | PASS (조건부 마커 추가) |
| PARSE_FAILED TYPE_A/B/C | 허용 (항상) | 차단 (RuntimeError) |

---

## 5. Phase 18 잔여 이슈 (Phase 19 이관)

| 이슈 | 내용 |
|------|------|
| `verifier_revision_closure` WARN 잔존 가능성 | truly_cnt=1 케이스는 WARN. 완전 PASS 달성 위한 추가 reviser 강화 고려 |
| TYPE_A/B/C 차단 실전 검증 | 아직 실전 미발생. 발생 시 main.py 흐름 확인 필요 |
| `counterpoint_specificity_p1` 모니터링 | Post1도 간헐적 WARN/FAIL. 별도 트랙 필요 시 Phase 19 이관 |
