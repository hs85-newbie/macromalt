# Phase 12 Handoff — Evidence Density & Writing Quality Hardening

**Commit**: `25a7cfc`
**Status**: GO
**Date**: 2026-03-16

---

## 1. What Phase 12 Changes

Phase 12는 기존 파이프라인 구조를 유지하면서 **생성 품질을 높이기 위한 3가지 메커니즘**을 추가한다.

| 메커니즘 | 위치 | 효과 |
|---|---|---|
| 프롬프트 증거 밀도 규칙 주입 | `gemini_analyze`, `gpt_write_analysis`, `gpt_write_picks` | 수치·시점·근거 포함 강제 지시 |
| 수치 하이라이트 블록 | `generate_deep_analysis` | 수집 자료의 핵심 수치를 요약해 LLM 입력 앞에 주입 |
| rule-based 품질 스코어링 | `generate_deep_analysis`, `generate_stock_picks_report`, `main.py` | 5개 지표 진단 + Post1/Post2 분리 체크 (비파괴) |

---

## 2. 추가된 컴포넌트 (generator.py SECTION A-2)

### 상수

| 이름 | 역할 |
|---|---|
| `_P12_QUALITY_THRESHOLDS` | 5개 품질 지표 통과/경고 임계값 (튜닝 가능) |
| `_P12_GENERIC_PHRASES` | 비근거 표현 목록 (일반어 과다 탐지용) |
| `_P12_COUNTERPOINT_MARKERS` | 반론 존재 탐지 마커 목록 |
| `_P12_ANALYST_EVIDENCE_RULES` | Gemini 분석 단계용 증거 밀도 지시문 |
| `_P12_POST1_EVIDENCE_RULES` | GPT Post1 4요소 구조 강제 지시문 |
| `_P12_POST2_EVIDENCE_RULES` | GPT Post2 4단계 구조 강제 지시문 |

### 함수

| 이름 | 반환 | 역할 |
|---|---|---|
| `_build_numeric_highlight_block(articles, research)` | `str` | 수치 포함 문장 추출 → 하이라이트 블록 |
| `_score_post_quality(content, label)` | `dict` | rule-based 품질 스코어 (비파괴) |
| `_check_post_separation(post1_content, post2_content)` | `dict` | h3 헤딩 + 단락 중복 체크 |

---

## 3. 튜닝 가능한 임계값

`generator.py` 상단 `_P12_QUALITY_THRESHOLDS` dict:

```python
_P12_QUALITY_THRESHOLDS = {
    "numeric_density_pass":  5,   # 숫자 패턴 5개 이상 → PASS
    "numeric_density_warn":  2,   # 2~4개 → WARN, 2 미만 → FAIL
    "time_anchor_pass":      3,   # 시점 앵커 3개 이상 → PASS
    "time_anchor_warn":      1,
    "counterpoint_pass":     2,   # 반론 마커 2개 이상 → PASS
    "counterpoint_warn":     1,
    "generic_phrase_pass":   2,   # 일반어 2개 이하 → PASS
    "generic_phrase_warn":   5,
    "evidence_binding_pass": 2,   # 출처 패턴 2개 이상 → PASS
}
```

수치 기준이 너무 엄격하거나 느슨하면 이 값만 조정. 코드 수정 없이 튜닝 가능.

---

## 4. 품질 체크 발생 위치

```
generate_deep_analysis()
  ├── _build_numeric_highlight_block()  → Gemini 입력에 수치 블록 주입
  ├── gemini_analyze()                   → _P12_ANALYST_EVIDENCE_RULES append
  ├── gpt_write_analysis()               → _P12_POST1_EVIDENCE_RULES prepend
  └── _score_post_quality(content, "Post1")  → 품질 진단 로그 + return

generate_stock_picks_report()
  ├── gpt_write_picks()                  → _P12_POST2_EVIDENCE_RULES prepend
  └── _score_post_quality(content, "Post2")  → 품질 진단 로그 + return

main.py / main()
  └── _check_post_separation()           → h3 중복 체크 + Phase 12 게이트 로그
```

---

## 5. Post1 / Post2 역할 분리 강제 방식

**프롬프트 레벨 (생성 단계)**:
- `_P12_POST1_EVIDENCE_RULES` 마지막 항목: "Post1은 거시·시장 구조·파급 경로 중심. Post2 종목 분석과 동일 문장 반복 금지."
- `_P12_POST2_EVIDENCE_RULES` 3번 항목: "Post1 거시 배경을 그대로 반복하지 않는다."

**진단 레벨 (생성 후)**:
- `_check_post_separation()`: h3 헤딩 교집합 + 80자 이상 단락 교차 탐지
- 결과: PASS (overlap=0) / WARN (≤2) / FAIL (>2)
- main.py 게이트에 `post_role_separation` 항목으로 기록

---

## 6. 로그 패턴

```
[Phase 12] 수치 하이라이트 블록 생성: N개 항목
[Phase 12] 품질 스코어 [Post1] | 숫자밀도: PASS(8) | 시점앵커: PASS(5) | 반론: PASS(6) | 일반어: PASS(1) | 근거결합: WARN(1)
[Phase 12] 품질 경고 [Post1] — 개선 대상: ['evidence_binding']
[Phase 12] Post1/Post2 역할 분리 | h3 중복: 0개 | 단락 중복: 0개 | 상태: PASS
[Phase 12] 최종 품질 게이트:
  numeric_density: PASS
  time_anchor: PASS
  ...
  final_status: GO
```

---

## 7. 비파괴 보장

- `_score_post_quality`: 콘텐츠를 수정하거나 파이프라인을 차단하지 않음. 진단 전용.
- `_check_post_separation`: 동일하게 진단 전용.
- `_build_numeric_highlight_block`: 수집 자료를 수정하지 않음. 별도 블록으로 주입만 수행.
- 공개 함수 시그니처 전원 유지 (signature 변경 없음).
- Phase 11 publish_history 구조 유지 (필드 추가 없음).

---

## 8. 리스크 및 후속 과제

| 리스크 | 설명 |
|---|---|
| 프롬프트 토큰 증가 | 3개 규칙 블록 + 수치 하이라이트 블록 추가로 Gemini/GPT 입력 토큰이 증가함 (약 200~500 토큰 추가 추정). 현재 max_tokens 여유 내에서 처리 가능. |
| 수치 하이라이트 false noise | 수치처럼 보이는 비금융 숫자(전화번호, 주소번지 등)가 포함될 수 있음. 임계값 `_P12_HIGHLIGHT_MIN_ITEMS=3`으로 완화. |
| `evidence_binding` 감지 한계 | 한국어 출처 패턴 정규식이 표현 다양성을 완전히 커버하지 못할 수 있음. WARN이 기본 허용 수준. |
| `_check_post_separation` 단락 체크 | 80자 이상 동일 단락 탐지 — 태그 제거 후 단순 비교라 편집된 반복은 미탐지. |

---

## 9. 종료 기준 충족 여부

| 기준 | 상태 |
|---|---|
| A. 증거 밀도 규칙 (수치/시점/출처) | ✅ 프롬프트 3단계 + 스코어링 |
| B. 구조적 글쓰기 규율 (Why now / Evidence / Implication / Counter) | ✅ Post1 4요소, Post2 4단계 강제 |
| C. Post1/Post2 역할 차이 강화 | ✅ 프롬프트 지시 + 진단 체크 |
| D. Soft quality gates (비파괴) | ✅ 5개 지표 스코어링 + 로그 |
| 기존 파이프라인 무손상 | ✅ import OK, signature 안정 |
| Phase 11 호환성 | ✅ 이력 구조 유지 |
