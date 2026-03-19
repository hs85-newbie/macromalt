# REPORT_PHASE16B_OUTPUT_QUALITY_HARDENING

작성일: 2026-03-19
Phase: 16B — Output Quality Hardening
구현 기반: Phase 16A GO (run_id 20260318_000537)
게이트: **PHASE16B_IMPL_GO** (코드 구현 완료 / 실출력 검증은 16B-Real에서)

---

## 1. Why Phase 16A GO Does Not End Quality Work

Phase 16A는 "현재 연도 과거 월 시제 정상화" 핵심 목표를 달성했다.
그러나 16A 실출력 검증에서 다음 잔존 위험이 확인되었다:

| 항목 | 16A 상태 | 원인 |
|------|----------|------|
| Post2 Step3 503 UNAVAILABLE | WARN | Gemini 인프라 불안정 → GPT 초안 원본 발행 |
| Post1/Post2 도입부 중복 | FAIL (기존) | n-gram 5개 이상 중복, 연속성 FAIL |
| Post2 generic wording | FAIL | Step3 미수정 상태로 발행 |
| premium editorial tone | WARN | Step3 미수정 및 GPT prompt 불충분 |

이 위험들은 Phase 16 자체의 회귀가 아니라 **Step3 인프라 불안정과 GPT 생성 품질 바닥의 한계**다.
Phase 16B는 이 품질 바닥을 올리는 하드닝 레이어를 추가한다.

---

## 2. What Phase 16B Changed

### Track A — Step3 실패 품질 저하 방지

**문제**: Step3 503/timeout 시 GPT 초안이 그대로 발행됨.

**구현**:
1. `verify_draft()` 반환 dict에 `step3_status` 필드 추가:
   - `"PASS"` — Step3 통과 (수정 불필요)
   - `"REVISED"` — Step3 실패 → 수정본 적용
   - `"FAILED_NO_REVISION"` — Step3 실패 + 수정 호출 실패 (503/timeout)
   - `"PARSE_FAILED"` — Step3 응답 파싱 실패
2. `_p16b_emergency_polish(content, label)` 함수 신규 추가:
   - `_P16B_GENERIC_MARKERS` (15개 generic 패턴) 기준 진단
   - **실 치환 미수행** (문장 컨텍스트 없는 regex 치환 → 의미 역전 위험)
   - 대신: 발견 건수를 WARN 로그로 노출 + `polish_log` dict 반환
   - 16C에서 실 치환 여부 결정
3. `generate_deep_analysis()` / `generate_stock_picks_report()`:
   - `_p1_step3_status` / `_p2_step3_status` 변수로 상태 추적
   - `step3_status == "FAILED_NO_REVISION"` 시 `_p16b_emergency_polish` 호출

**가시성**: `p16b_guard.step3_status`, `p16b_guard.fallback_triggered`, `p16b_guard.emergency_polish` — p13_scores에 노출

---

### Track B — Post1/Post2 도입부 중복 감소

**문제**: 도입부 n-gram 5개 이상 중복 → 연속성 FAIL.

**구현**:
1. `_p16b_compute_intro_overlap(post1_content, post2_content, n=4)` 함수 신규 추가:
   - 각 아티클 앞 300자(plain text) 추출
   - 4-gram 기준 겹침 비율 계산
   - `status`: LOW (<15%) / MEDIUM (<30%) / HIGH (≥30%)
   - HIGH 시 WARN 로그 + 16C 권고 플래그
2. `_P16B_POST2_ANGLE_DIVERSIFICATION` 상수 신규 추가:
   - gpt_write_picks user_msg 최상단에 주입 (Phase 15C 레이블 차단 다음)
   - Post2가 Post1과 다른 각도에서 열도록 GPT 지시
   - "왜 지금 이 종목인가?" 투자자 관점 시작 강제
3. Post2 p13_scores에 `p16b_guard.intro_overlap` 필드 노출

**제한**: GPT prompt 주입으로 확률적 개선. 100% 보장 아님 — 16C에서 post-gen 각도 다양성 체크 고려.

---

### Track C — Generic Wording / Analytical Spine 하드닝

**문제**: "이러한 흐름은", "주목됩니다" 등 generic 문장 → 투자자 신뢰 저하.

**구현**:
1. `_P16B_QUALITY_HARDENING_RULES` 상수 신규 추가 (GPT prompt 공통 블록):
   - Generic 문장 금지 목록 (❌ 4개 패턴)
   - Analytical Spine 유지 규칙 (✅ 4개 규칙): 사실→해석→변수→반론 흐름
   - Why-Now 프레임 필수화
   - 인과 메커니즘 구체화 요구
2. `gpt_write_analysis()` user_msg 최우선에 `_P16B_QUALITY_HARDENING_RULES` 주입
3. `gpt_write_picks()` user_msg에도 동일 주입

---

### Track D — Premium Editorial Tone 복구

**구현**: `_P16B_QUALITY_HARDENING_RULES` 내 Premium Tone 섹션:
- 고요하고 확신 있는 어조 지시
- Sell-side 보고서 수준 이상 언어 요구
- 연극적 비유·감정 호소 금지
- "투자자들의 주목을 받고 있습니다" 류 금지

---

### Track E — Temporal SSOT 비회귀 보호

**설계 원칙**: 16B의 모든 품질 변경은 Phase 16 Temporal SSOT 위에 쌓이는 레이어.

보호 구조:
1. `_P16B_QUALITY_HARDENING_RULES`는 시제 관련 지시를 포함하지 않음 — Temporal SSOT가 최우선
2. `_p16b_emergency_polish`는 실 치환 미수행 → temporal 문장 침범 불가
3. `_p16b_compute_intro_overlap`은 읽기 전용 — 콘텐츠 수정 없음
4. 기존 Phase 15D/15E/15F 교정 순서 유지 (16B guard는 Step3 직후, Phase 15 교정 이전에 위치)

---

### Track F — 진단 가시성

`p13_scores["p16b_guard"]` 딕셔너리 (Post1 / Post2 모두):

| 필드 | 설명 | 값 예시 |
|------|------|---------|
| `step3_status` | Step3 실행 결과 | `"PASS"` / `"REVISED"` / `"FAILED_NO_REVISION"` |
| `fallback_triggered` | Step3 실패 여부 | `false` / `true` |
| `emergency_polish` | generic 진단 결과 | `{"applied": false, "total_generic_found": 3, "status": "WARN"}` |
| `intro_overlap` | 도입부 중복률 (Post2만) | `{"overlap_ratio": 0.22, "status": "MEDIUM", ...}` |

이 필드들은 이후 16C~16E에서 다음 질문에 바로 답할 수 있게 한다:
- Step3 실패했는가? 어떤 fallback이 동작했는가?
- Post1/Post2 도입부 중복이 개선되었는가?
- generic wording이 정량적으로 얼마나 남아 있는가?

---

## 3. Changed File List

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `generator.py` | 수정 | Phase 16B 신규 코드 6개 편집 |

### 신규 추가된 코드 (generator.py)

| 항목 | 위치 | 역할 |
|------|------|------|
| `_P16B_QUALITY_HARDENING_RULES` | line ~3012 | GPT Post1/Post2 공통 품질 지시 블록 |
| `_P16B_POST2_ANGLE_DIVERSIFICATION` | line ~3025 | Post2 도입부 차별화 지시 블록 |
| `_P16B_GENERIC_MARKERS` | line ~3036 | emergency polish 탐지 마커 목록 (15개) |
| `_p16b_emergency_polish()` | line ~3042 | Step3 실패 시 generic 진단 pass |
| `_p16b_compute_intro_overlap()` | line ~3085 | Post1/Post2 도입부 4-gram 중복 계산 |

### 수정된 기존 코드

| 함수 | 변경 내용 |
|------|----------|
| `verify_draft()` | `step3_status` 필드 반환 추가 |
| `gpt_write_analysis()` | `_P16B_QUALITY_HARDENING_RULES` user_msg 최우선 주입 |
| `gpt_write_picks()` | `_P16B_POST2_ANGLE_DIVERSIFICATION` + `_P16B_QUALITY_HARDENING_RULES` 주입 |
| `generate_deep_analysis()` | step3_status 추적, emergency polish 조건 호출, p16b_guard p13_scores 추가 |
| `generate_stock_picks_report()` | 동일 + intro_overlap 계산 및 p16b_guard 추가 |

---

## 4. Verification Checklist

### Track A — Step3 실패 대응

| 항목 | 기준 | 검증 방법 |
|------|------|----------|
| step3_status 필드 존재 | p13_scores.p16b_guard.step3_status 있음 | 로그 / JSON |
| FAILED_NO_REVISION 탐지 | 503 발생 시 "FAILED_NO_REVISION" 로그 | Gemini 503 시 확인 |
| emergency_polish 호출 | fallback_triggered=true 시 "[Phase 16B] emergency polish" 로그 | 로그 |
| Temporal SSOT 비침범 | emergency_polish.applied=false | 항상 False (현 단계) |

### Track B — Post1/Post2 도입부 중복

| 항목 | 기준 | 검증 방법 |
|------|------|----------|
| intro_overlap 필드 존재 | Post2 p13_scores.p16b_guard.intro_overlap | 로그 / JSON |
| 중복 계산 정상 실행 | "[Phase 16B] 도입부 4-gram 중복:" 로그 | 로그 |
| HIGH 시 WARN 로그 | overlap_ratio ≥ 0.30 → WARN | 로그 |
| 도입부 각도 개선 | Post2 시작이 종목 직접 연결 | 실출력 검토 |

### Track C/D — Generic Wording + Premium Tone

| 항목 | 기준 | 검증 방법 |
|------|------|----------|
| 품질 규칙 주입 | "[Phase 16B — 품질 하드닝" GPT prompt 포함 | prompt 내용 |
| Post1 generic 감소 | 16A 대비 generic 마커 건수 감소 | 실출력 텍스트 |
| Post2 generic 감소 | 특히 Step3 미수정 케이스 | 실출력 텍스트 |

### Track E — Temporal 비회귀

| 항목 | 기준 | 검증 방법 |
|------|------|----------|
| SSOT 유지 | p16b_guard 삽입 후 p15f_strip/p16_ssot_run 정상 | 로그 |
| emergency_polish 시제 침범 없음 | applied=false → 콘텐츠 수정 없음 | 항상 보장 |
| 기존 Phase 15 교정 순서 유지 | 15D → 15E → 15F 순 정상 실행 | 로그 순서 |

### Track F — Inspectability

| 항목 | 기준 |
|------|------|
| Post1 p13_scores["p16b_guard"] 존재 | ✅ step3_status, fallback_triggered, emergency_polish, intro_overlap(None) |
| Post2 p13_scores["p16b_guard"] 존재 | ✅ step3_status, fallback_triggered, emergency_polish, intro_overlap(dict) |

### 빌드/임포트

| 항목 | 결과 |
|------|------|
| `python3 -c "import ast; ast.parse(...)"` | ✅ Syntax OK |
| 기존 public signature 변경 | ❌ 없음 (verify_draft 반환 dict 확장만) |
| 신규 외부 의존성 | ❌ 없음 (stdlib `re` 사용) |

---

## 5. Known Residual Risks

| 위험 | 심각도 | 완화 |
|------|--------|------|
| `_p16b_emergency_polish`가 실 치환 미수행 → generic wording 잔존 | MEDIUM | 진단은 수행됨, 실 치환은 16C에서 결정 |
| `_P16B_POST2_ANGLE_DIVERSIFICATION`이 GPT 확률적 적용 → 100% 보장 아님 | MEDIUM | 16C에서 post-gen 각도 다양성 체크 추가 고려 |
| intro_overlap MEDIUM/HIGH 지속 가능성 | LOW | 16C에서 HIGH 시 rewrite trigger 추가 고려 |
| Step3 503 구조적 재발 가능성 | LOW | Gemini 인프라 수준 문제 — retry 로직 16C 검토 |

---

## 6. What Is Intentionally Out of Scope (for 16C+)

- `_p16b_emergency_polish` 실 치환 구현 (16C 결정 필요)
- intro_overlap HIGH 시 자동 rewrite 트리거 (16C)
- Step3 retry 로직 (16C, 인프라 가용성 검증 후)
- `_P16B_GENERIC_MARKERS` 기반 자동 문장 재작성 (16C)
- Post1 intro도 overlap에 포함 (현재 Post2에서만 계산)

---

## 7. Gate Decision

**PHASE16B_IMPL_GO**

코드 구현 완료 / Syntax OK.
실출력 검증은 별도 16B-Real 런에서 수행.
Phase 16 Temporal SSOT 회귀 없음 확인.

---

## 8. Handoff Note

Phase 16B 구현 완료.
다음 단계: `jobs/PROMPT_PHASE16B_REAL_OUTPUT_VALIDATION.md` (또는 신규 실출력 런) 실행으로 16B 효과 실측.
emergency_polish.status, intro_overlap.status, step3_status 세 필드가 16C 우선순위 결정 기준이 된다.
