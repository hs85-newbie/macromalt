# REPORT_PHASE15D_JEONMANG_TAG_STRIP

**작성일:** 2026-03-17
**커밋:** b3f1f89
**Gate:** GO

---

## 1. Changed Files

| 파일 | 변경 내용 |
|---|---|
| `generator.py` | +108 lines |

### 변경된 구역 요약

| 위치 | 변경 유형 | 설명 |
|---|---|---|
| `_detect_internal_label_leakage` 이후 (~line 2370) | 추가 | `_P15D_CONFIRMED_VERB_MARKERS` 상수 (16개 패턴) |
| 상수 이후 | 추가 | `_strip_misapplied_jeonmang_tags()` 함수 (76줄) |
| Post1 Phase 15 시제 교정 이후 (~line 4407) | 추가 | `_strip_misapplied_jeonmang_tags()` 호출 |
| `p13_scores` Post1 | 수정 | `"jeonmang_strip"` 키 추가 |
| Post2 Phase 15C 레이블 탐지 이후 (~line 4631) | 추가 | `_strip_misapplied_jeonmang_tags()` 호출 |
| `p13_scores` Post2 | 수정 | `"jeonmang_strip"` 키 추가 |

---

## 2. 근본 원인

Phase 15C HOLD의 정확한 원인:

**Step3 Reviser가 Phase 15C temporal grounding 프롬프트를 받고도 확정 실적 문장 앞에 `[전망]` 텍스트 태그를 추가했다.**

- Phase 15A/15B는 동사 어미 패턴(`기록할 것으로 전망됩니다` → `기록한 것으로 집계됐습니다`)을 교정하는 regex 계층이다.
- `[전망]` 태그는 동사 어미와 별개의 텍스트 요소 — 기존 교정 로직이 전혀 커버하지 않았다.
- 프롬프트 수준 차단(Phase 15C)이 확률적 Gemini 모델을 완전히 막지 못했다.

실제 발행 위반 예시 (Phase 15C validation, Post2 ID 157):
```
[전망] 2025년 SK하이닉스의 매출액은 53조 1,000억 원으로 전년 대비 100% 이상 증가하고,
       영업이익은 15조 9,000억 원을 기록한 것으로 집계됐습니다(상상인증권 리서치).
```
→ 동사: "기록한 것으로 집계됐습니다" = 올바른 과거형 (Phase 15B 교정 성공)
→ `[전망]` 접두 태그: 확정 실적을 예측처럼 제시 = 독자 신뢰도 훼손 **(Phase 15D 대상)**

---

## 3. Implementation Summary

### `_P15D_CONFIRMED_VERB_MARKERS`

16개 확정 어미 패턴:
- 집계됐습니다 / 집계됐다 / 집계됐으며 / 집계됐고 / 집계됐습
- 기록한 것으로 집계 / 집계된 것으로
- 기록됐습니다 / 기록됐다 / 기록됐으며
- 달성했습니다 / 달성했다 / 달성했으며
- 증가한 것으로 / 감소한 것으로 / 상승한 것으로 / 하락한 것으로

### `_strip_misapplied_jeonmang_tags(content, run_year, label)`

제거 판단 기준 (AND 조건):

| 조건 A | 조건 B |
|---|---|
| 완료 연도 포함 (2023/2024/2025년) OR 확정 과거 월 포함 (2026년 1~2월) | `_P15D_CONFIRMED_VERB_MARKERS` 중 하나 포함 |

진짜 전망 문장 보존:
- `[전망] 2026년 하반기 HBM 수요 증가 예상됩니다` → 조건 B 미충족 → **보존**
- `[전망] 2027년 가이던스 달성 기대됩니다` → 조건 A 미충족 → **보존**

처리 방식:
1. `\[전망\]\s*` regex로 모든 위치 탐지
2. 역순 처리 (인덱스 보존)
3. 각 위치 이후 300자 컨텍스트 추출 → HTML 태그 제거 → 조건 판단
4. 조건 충족 시 `[전망]\s*` 제거
5. 결과: `(updated_content, strip_log)` 반환

호출 위치:
- Post1: Phase 15 시제 교정 이후, `p13_scores` 구성 이전
- Post2: Phase 15C 내부 레이블 탐지 이후, `p13_scores` 구성 이전

---

## 4. Verification Results

### 7/7 Unit Tests PASS

```
✅ 1. Phase 15D 상수/함수 존재 OK
✅ 2. 2025년 확정 실적 → [전망] 제거 OK  (Phase 15C 위반1 재현)
✅ 3. 2026년 2월 집계됐다 → [전망] 제거 OK  (Phase 15C 위반2 재현)
✅ 4. 혼합 문장 선두 [전망] 제거 OK  (Phase 15C 위반3 재현)
✅ 5. 진짜 전망 문장 → [전망] 보존 OK
✅ 6. 클린 콘텐츠 → 무변경 OK
✅ 7. Phase 15B 호환성 OK
```

로그 출력 확인 (테스트 실행 중):
```
[Phase 15D] 확정 실적 앞 [전망] 태그 1건 제거 [test]
  ✂ 제거 → 2025년 SK하이닉스의 매출액은 53조 원으로...기록한 것으로 집계됐습니다
[Phase 15D] 확정 실적 앞 [전망] 태그 1건 제거 [test]
  ✂ 제거 → 2026년 2월 양극재 수출액은 전월 대비 35% 증가한 것으로 집계됐다
[Phase 15D] 확정 실적 앞 [전망] 태그 1건 제거 [test]
  ✂ 제거 → 2026년 2월 양극재 수출량은 전월 대비 34% 증가한 것으로 집계됐으며...
```

### Verification Checklist

| 항목 | 결과 | 근거 |
|---|---|---|
| `_strip_misapplied_jeonmang_tags` 함수 추가 | **PASS** | 함수 존재 + 7개 단위 테스트 전부 통과 |
| Phase 15C 위반1 재현 후 제거 | **PASS** | `2025년 SK하이닉스...집계됐습니다` → [전망] 제거 확인 |
| Phase 15C 위반2 재현 후 제거 | **PASS** | `2026년 2월...집계됐다` → [전망] 제거 확인 |
| Phase 15C 위반3 재현 후 제거 | **PASS** | `집계됐으며...전망됩니다` 혼합 → 선두 [전망] 제거 확인 |
| 진짜 전망 문장 보존 | **PASS** | `2026년 하반기...예상됩니다` → [전망] 유지 확인 |
| 클린 콘텐츠 무변경 | **PASS** | `[전망]` 없는 콘텐츠 → 원문 동일 유지 |
| Phase 15B 호환성 | **PASS** | 동사 어미 교정 로직 영향 없음 |
| Post1/Post2 흐름 통합 | **PASS** | 두 흐름 모두 Phase 15 교정 이후 호출 |
| `p13_scores["jeonmang_strip"]` 키 | **PASS** | 진단 결과 포함 확인 |
| import/build | **PASS** | `source venv/bin/activate && python3 -c "import generator"` OK |

---

## 5. Risks / Follow-up

### 잠재적 리스크

| 리스크 | 수준 | 설명 |
|---|---|---|
| 오탐 (false positive) — 정상 전망 제거 | LOW | 조건 A(연도/월) AND 조건 B(확정 어미)의 AND 조건으로 설계 → 확정 어미가 없는 전망 문장은 보존 |
| 혼합 문장 선두 태그 제거 시 후반 전망 절 맥락 | LOW | 후반 절에 "전망됩니다/예상됩니다"가 있으면 독자가 문장 자체에서 전망성 판단 가능 |
| `[전망]` 태그 HTML 속성 사용 가능성 | NEGLIGIBLE | 기존 파이프라인에서 `[전망]`은 항상 플레인 텍스트 마커로만 사용됨 |
| `_now_month` 계산 (연말 edge case) | LOW | `run_year != datetime.now().year`이면 12로 고정 → 향후 연도 전환 시 정상 동작 |

### Follow-up Items

1. **Phase 15D 실출력 검증** (최우선)
   - 신규 run 실행 → Post2 `jeonmang_strip` 로그 확인
   - 발행 본문에서 `[전망]` 태그 위치 전수 검사
   - 제거 건수 > 0이면 제거된 항목이 실제 오주입인지 육안 확인

2. **오탐 모니터링** (지속)
   - `p13_scores["jeonmang_strip"]["log"]`에서 제거된 항목 검토
   - 정상 전망 문장이 잘못 제거되는 케이스 발견 시 `_P15D_CONFIRMED_VERB_MARKERS` 정교화

---

## 6. Final Gate JSON

```json
{
  "jeonmang_tag_strip_function": "PASS",
  "completed_year_tag_removal": "PASS",
  "confirmed_period_tag_removal": "PASS",
  "mixed_sentence_tag_removal": "PASS",
  "legitimate_forecast_preservation": "PASS",
  "clean_content_idempotency": "PASS",
  "phase15b_compatibility": "PASS",
  "post1_post2_integration": "PASS",
  "import_build": "PASS",
  "final_status": "GO"
}
```
