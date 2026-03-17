# REPORT_PHASE14_TARGETED_REWRITE_HOTFIX

작성일: 2026-03-17 | 커밋: da817d5

---

## 1. Changed Files

| 파일 | 변경 내용 |
|---|---|
| `generator.py` | +797 / -32라인: Track C 타겟 블록 교체 시스템 추가, `_enforce_interpretation_rewrite` 전면 재작성 |

---

## 2. Implementation Summary

### 왜 기존 재작성 루프가 실패했는가

`_score_interpretation_quality`의 `weak_hits` 계산 방식:

```python
weak_hits = sum(
    1 for (kw1, kw2) in _P13_WEAK_INTERP_PATTERNS
    if kw1 in plain and kw2 in plain   # ← 기사 전체 plain text에서 검사
)
```

문제: `kw1`과 `kw2`가 **서로 다른 섹션**에 나타나도 hit로 감지됨.
예: "지정학" → 배경 섹션 사실 서술, "불확실" → 반론 섹션 카테고리 나열.
전체 기사를 Gemini로 재작성해도, [해석] 섹션이 개선되더라도 배경 섹션의 "지정학"과
반론 섹션의 "불확실"은 그대로 남아 패턴이 계속 감지됨.
→ **whole-article rewrite는 이 구조에서 null-op**.

### 새로운 접근: 타겟 블록 교체 3단계

**Track A: `_extract_weak_interp_blocks(content)`**

1. HTML을 `<p>`, `<li>`, `<h1-6>`, `<blockquote>` 단위로 분리
2. 각 블록 plain text에서 패턴 `(kw1, kw2)` 쌍이 **동시 등장**하는 블록 선별 (co-occurrence)
3. Co-occurrence 없으면 `[해석]`/`[전망]`/`[반대]` 섹션 힌트가 있는 블록 보조 선별
4. 최대 6개 반환 (Gemini 컨텍스트 절약)

```python
# 결과 구조
{
    'html_block': '<p>[해석] 유가 상승이 인플레이션 압력을...</p>',
    'plain_text': '[해석] 유가 상승이 인플레이션 압력을...',
    'matched_patterns': [('유가', '인플레')],
    'has_cooccurrence': True,
    'section_hint': '[해석]',
}
```

**Track B: `_rewrite_weak_blocks(targets, article_spine, post_type, label)`**

- 타겟 블록들을 Gemini에 **일괄** 전달 (API 호출 1회)
- `GEMINI_TARGETED_BLOCK_REWRITE_SYSTEM_POST1` / `_POST2` 별도 시스템 프롬프트
  - Post1: 비자명적 매크로 해석, spine 지지, 직접 인과 제거
  - Post2: 종목 레벨 차별화, 수급 비대칭, 반론 조건+충돌 강화
- 출력 형식: `BLOCK_N:` 구분자로 번호별 교체본 파싱
- 길이 안전 가드: 교체본 < 원본의 30% → 스킵

**Track C: `_apply_block_replacements(content, replacements, label)`**

- `{원본 HTML 블록 → 교체 HTML 블록}` 매핑으로 정밀 교체
- HTML 구조 보존 (태그, 헤딩, 주석 손대지 않음)
- 원본 블록 미탐지 시 스킵 (안전 폴백)

**Track D: Re-score 검증**

교체 후 `_score_interpretation_quality()` 재실행:
```python
new_hits = new_score.get("weak_interp_hits", weak_interp_hits)
if new_hits < weak_interp_hits:
    # IMPROVED
else:
    # 패턴이 비-해석 섹션에 잔존 — 로그 기록, 폴백으로 진행
```

**폴백: 전체 기사 재작성 유지**

타겟 블록 0개이거나 교체 결과 없을 경우 기존 `GEMINI_INTERP_REWRITE_SYSTEM` 방식으로 폴백.
이전 동작을 100% 보존.

### 호출 위치 변경

**Post1 (`generate_deep_analysis`):**
```python
# Before
final_content = _enforce_interpretation_rewrite(final_content, weak_hits, label="Post1")

# After
_pre_spine = _extract_post1_spine(final_content)
final_content = _enforce_interpretation_rewrite(
    final_content, weak_hits, label="Post1", article_spine=_pre_spine
)
```

**Post2 (`generate_stock_picks_report`):**
```python
# Before
final_content = _enforce_interpretation_rewrite(final_content, p2_weak_hits, label="Post2")

# After
final_content = _enforce_interpretation_rewrite(
    final_content, p2_weak_hits, label="Post2",
    article_spine=post1_spine,   # Post2는 Post1 뼈대를 spine으로 전달
)
```

---

## 3. Verification Results

### 유닛 테스트 (전원 통과)

| 테스트 | 결과 |
|---|---|
| co-occurrence 블록 추출 (유가+인플레 동일 단락) | ✅ PASS |
| section hint 블록 추출 ([해석] 내 단일 키워드) | ✅ PASS |
| 패턴 없는 콘텐츠 → 타겟 0개 | ✅ PASS |
| 최대 6개 블록 캡 | ✅ PASS |
| `_apply_block_replacements` 교체 적용 | ✅ PASS |
| 비존재 원본 블록 → HTML 불변 안전 폴백 | ✅ PASS |
| `_enforce_interpretation_rewrite` 시그니처 (article_spine 포함) | ✅ PASS |
| weak_hits < 3 스킵 보존 | ✅ PASS |
| 약한 콘텐츠 weak_hits=4 감지 | ✅ PASS |
| 강한 콘텐츠 weak_hits 감소 확인 | ✅ PASS |

### 빌드 검증

```
✅ generator.py syntax OK (151,198 chars, 4,324 lines)
✅ 신규 심볼 7개 존재 확인
✅ Post1 / Post2 호출 위치 spine 와이어링 확인
✅ generator import OK
```

### weak_hits 감소 가능성 측정

타겟 방식이 작동하는 케이스:
- 패턴 키워드 쌍이 동일 블록에 공존 → 해당 블록 교체 시 해당 패턴 소멸 가능

타겟 방식이 여전히 한계인 케이스:
- 패턴이 서로 다른 HTML 블록에 분산 (kw1 = 배경 섹션, kw2 = 반론 섹션)
  → 이 경우 폴백으로 전환 + 로그 기록
- 교체본에 다른 약한 패턴이 새로 유입될 경우 hits 불변 또는 증가 가능

---

## 4. Risks / Follow-up

| 항목 | 종류 | 완화 방법 |
|---|---|---|
| 분산 패턴 (kw1/kw2가 다른 섹션에 존재) | 구조적 한계 | 폴백 + 로그로 가시화. 다음 조치에서 키워드 범위 축소 고려 |
| Gemini BLOCK_N 파싱 실패 | 구현 리스크 | `_rewrite_weak_blocks` returns `{}` → fallback safe |
| 교체본 길이 30% 미만 가드 | 보수적 임계값 | 실전 데이터 보고 20%로 낮출 수 있음 |
| `_P13_WEAK_INTERP_PATTERNS` 패턴이 너무 넓음 | 진단 정확도 | 패턴 쌍을 동일 문장 내 co-occurrence로 재정의하는 별도 강화 필요 |
| Post2 약한 [해석] 재작성 품질 | 실전 미검증 | Phase 14H 실행 후 발행 결과 확인 필요 |

### 다음 후속 조치 (우선순위 순)

1. **Phase 14H 실전 실행** — 발행 기사에서 타겟 블록 교체 실제 효과 측정
2. **`_P13_WEAK_INTERP_PATTERNS` 정밀화** — 전체 기사 레벨 감지 → 문장 레벨 co-occurrence 감지로 개선
3. **Post2 [반대 포인트] 전용 강제** — 단순 `threshold >= 3` 외에 반론 섹션 별도 강화 루프 추가

---

## 5. Final Gate JSON

```json
{
  "weak_sentence_extraction": "PASS",
  "targeted_rewrite_generation": "PASS",
  "sentence_replacement_integration": "PASS",
  "html_structure_preservation": "PASS",
  "post_rewrite_rescoring": "PASS",
  "rewrite_resolution_detection": "PASS",
  "post2_stock_interpretation_hotfix": "PASS",
  "phase14_compatibility": "PASS",
  "public_signature_stability": "PASS",
  "import_build": "PASS",
  "final_status": "GO"
}
```

**판정 근거:**
- 타겟 블록 추출 → Gemini 교체 → HTML 삽입 → re-score 전 과정 구현 완료
- 폴백 경로 보존으로 기존 동작 100% 유지
- 실전 weak_hits 감소 여부는 다음 발행 결과로 검증 예정

---

*이전 Phase: [handoff_phase14.md](handoff_phase14.md)*
