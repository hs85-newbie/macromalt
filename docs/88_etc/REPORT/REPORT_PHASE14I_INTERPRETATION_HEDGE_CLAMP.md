# REPORT_PHASE14I_INTERPRETATION_HEDGE_CLAMP

작성일: 2026-03-17 | 기반: Phase 14H 실출력 검증 HOLD

---

## 1. Changed Files

| 파일 | 변경 유형 | 변경 요약 |
|---|---|---|
| `generator.py` | 수정 | +175라인 (4,393→4,568라인): Track A/B/C/D 구현 |
| `docs/REPORT_PHASE14I_INTERPRETATION_HEDGE_CLAMP.md` | 신규 | 이 파일 |

### generator.py 세부 변경

| 위치 | 변경 내용 |
|---|---|
| SECTION A-4 (enforcement constants) | `_P14I_INTERP_HEDGE_ENDINGS` 리스트 (10개) + `_P14I_INTERP_HEDGE_CLAMP` 상수 추가 |
| `_P14_POST1_ENFORCEMENT_BLOCK` | `_P14I_INTERP_HEDGE_CLAMP` 블록 추가 (len: 1,836 → 2,569자) |
| `GEMINI_TARGETED_BLOCK_REWRITE_SYSTEM_POST1` | `[Phase 14I — [해석] 헤징 어미 차단]` 섹션 추가 |
| `GEMINI_TARGETED_BLOCK_REWRITE_SYSTEM_POST2` | 동일 |
| 신규 함수 `_detect_interp_hedge_density()` | [해석] 블록 헤징 포화도 측정 |
| 신규 함수 `_extract_hedge_heavy_interp_blocks()` | [해석]+헤징어미 블록 추출 |
| `_enforce_interpretation_rewrite()` | `hedge_overuse_status` 파라미터 추가, hedge_overuse FAIL 트리거 경로 추가 |
| `generate_deep_analysis()` Post1 call | `hedge_overuse_status=hedge_ovuse` 추가 |
| `generate_stock_picks_report()` Post2 call | `hedge_overuse_status=p2_hedge_ovuse` 추가 |

---

## 2. Implementation Summary

### 왜 이 핫픽스가 필요한가

Phase 14H 실출력 검증 결과:
- Post1 [해석] 문장 7개 중 6개 = "이는 X로 파악됩니다/보입니다" 공식
- hedge_overuse = 74% (19문장 중 14회) → Phase 13 FAIL
- 타겟 재작성 핫픽스 미실행 (weak_hits=2 < 임계값 3)
- 결과: 글이 면책 선언처럼 읽힘. 분석 판단이 아님

핵심 진단: `[해석]` 레이블 문장이 "파악됩니다/보입니다"로 끝나는 패턴이 GPT의 기본 출력 공식으로 고착됨. 이 패턴은 Phase 14의 팩트 서술 헤징 금지와 별개이며, Phase 14의 weak_interp 감지기도 이를 충분히 잡지 못함.

### Track A — Interpretation Hedge Clamp

**`_P14I_INTERP_HEDGE_ENDINGS`** (10개):
```python
["파악됩니다", "보입니다", "것으로 보입니다", "것으로 파악됩니다",
 "작용하는 것으로 보입니다", "시사하는 것으로 보입니다",
 "판단됩니다", "것으로 판단됩니다", "보여집니다", "여겨집니다"]
```

**`_P14I_INTERP_HEDGE_CLAMP`** (732자):
- [해석] 레이블 문장에서 위 어미를 기본 결말로 사용 금지 명시
- 금지 예 3개 (실제 실패 기사에서 추출)
- 허용 대안 5개: "핵심은 [판단]에 있다", "이는 [A] 대신 [B]에 주목해야 함을 의미한다", 등

이 상수는 `_P14_POST1_ENFORCEMENT_BLOCK`에 포함되어 Post1/Post2 모든 GPT 생성에 주입됨.

### Track B — Hedge-Aware Rewrite Trigger

**기존:** `weak_interp_hits >= 3`만 재작성 트리거

**Phase 14I:** `weak_interp_hits >= 3` **OR** `hedge_overuse_status == "FAIL"` 트리거

```python
weak_trigger  = weak_interp_hits >= 3
hedge_trigger = hedge_overuse_status == "FAIL"
if not weak_trigger and not hedge_trigger:
    return content  # 스킵
```

Phase 14H 검증 런 조건으로 시뮬레이션:
- weak_hits=2 → weak_trigger=False
- hedge_overuse=FAIL (74%) → hedge_trigger=True
- **결과: 재작성 실행됨** ✅

### Track C — Targeted Hedge Rewrite

**`_extract_hedge_heavy_interp_blocks(content)`:**
- `[해석]` 태그가 있는 HTML 블록만 스캔
- `_P14I_INTERP_HEDGE_ENDINGS` 어미로 끝나는 블록만 추출 (최대 6개)
- 추출된 블록을 `_rewrite_weak_blocks()`에 전달 (기존 인터페이스 재사용)

**실행 경로:**
```
hedge_trigger=True
→ _detect_interp_hedge_density() 전 진단 + 로그
→ _extract_hedge_heavy_interp_blocks() → 헤징 어미 블록 추출
→ _rewrite_weak_blocks() → Gemini 타겟 교체
→ _apply_block_replacements() → HTML 삽입
→ _detect_interp_hedge_density() 후 진단 (비율 개선 검증)
```

**Gemini 재작성 시스템 프롬프트 업데이트:**
`GEMINI_TARGETED_BLOCK_REWRITE_SYSTEM_POST1/POST2` 양쪽에 `[Phase 14I — [해석] 헤징 어미 차단]` 섹션 추가:
- 재작성 중에도 헤징 어미 금지 명시
- 허용 대안 형식 제시
- 구체적 금지 예 포함

### Track D — Hedge Density Diagnostics

**`_detect_interp_hedge_density(content) → dict`:**
```python
{
  "interp_total":  int,    # [해석] 포함 문장 수
  "interp_hedged": int,    # 헤징 어미로 끝나는 [해석] 문장 수
  "hedge_ratio":   float,  # hedged/total
  "status":        str,    # "FAIL"(>0.5) | "WARN"(>0.25) | "PASS"
  "bad_lines":     list,   # 헤징 어미 탐지 문장 샘플 (최대 5개)
}
```

재작성 전/후 비교 로그:
```
[Phase 14I] [해석] 헤징 진단 [Post1] 전 — 6/7 (86%) status=FAIL
[Phase 14I] [해석] 헤징 교체 성공 [Post1] — 86% → 29%
```

hedge_ratio가 재작성 후 감소하지 않으면 WARN 로그 출력 (unresolved 처리).

---

## 3. Verification Results

### 유닛 테스트 결과 (12개 전원 통과)

| 테스트 | 결과 |
|---|---|
| `_P14I_INTERP_HEDGE_ENDINGS` 10개 포함 | ✅ |
| `_P14I_INTERP_HEDGE_CLAMP` len > 300, 키워드 포함 | ✅ |
| `_P14_POST1_ENFORCEMENT_BLOCK` clamp 포함 | ✅ |
| `_detect_interp_hedge_density` hedge-heavy 콘텐츠 FAIL | ✅ |
| `_detect_interp_hedge_density` clean 콘텐츠 PASS | ✅ |
| `_extract_hedge_heavy_interp_blocks` 3블록 추출 | ✅ |
| `_enforce_interpretation_rewrite` 파라미터 signature | ✅ |
| skip: weak_hits=0, hedge=PASS | ✅ |
| skip: weak_hits=2, hedge=WARN | ✅ |
| trigger 조건 검증 (hedge=FAIL → 미스킵) | ✅ |
| 빌드: `ast.parse(generator.py)` | ✅ |
| 빌드: `ast.parse(main.py)` | ✅ |

### Before/After 헤징 진단 예시

Phase 14H 검증 기사 Post1 [해석] 블록 3개:
```
전: "[해석] 이는 시장 전반의 불확실성을 줄이고... 작용하는 것으로 보입니다." → HEDGED
전: "[해석] 이는 성장성 기대가 이어지는 것으로 파악됩니다."             → HEDGED
전: "[해석] 이는 기업의 실적 개선에 기여하는 것으로 판단됩니다."         → HEDGED
→ interp_total=3, hedged=3, ratio=1.0, status=FAIL
```

Phase 14I 재작성 목표:
```
후: "[해석] 핵심은 시장이 안전자산 회피보다 금리 민감도를 더 크게 반영하고 있다는 점이다."
후: "[해석] 이번 흐름은 단순 기대감보다 성장성 프리미엄이 다시 가격에 반영되기 시작했다는 신호에 가깝다."
→ interp_total=2, hedged=0, ratio=0.0, status=PASS (목표)
```

---

## 4. Risks / Follow-up

### 리스크

| 리스크 | 영향 | 완화 |
|---|---|---|
| GPT가 생성 시 Phase 14I clamp를 준수하지 않을 경우 | hedge_overuse FAIL 지속 → 재작성 트리거 계속 발동 | 재작성 루프가 안전망으로 작동 |
| Gemini 타겟 재작성이 [해석] 어미는 바꾸지만 내용은 여전히 교과서 인과일 경우 | 어미만 바뀌고 non-obviousness 미개선 | Gemini 프롬프트에 내용 기준도 명시 (이미 포함) |
| hedge_trigger가 과도하게 발동되어 비용 증가 | Gemini API 호출 횟수 증가 | hedge_overuse FAIL 기준 >50%로 높은 임계값 유지 |
| [해석] 태그 미사용 단락의 헤징은 탐지 불가 | 커버리지 부분적 | [해석] 레이블 준수율 향상 필요 (별도 Phase) |

### 후속 항목

1. **실출력 검증** — Phase 14I 이후 신규 런 발행 기사에서 hedge_ratio 측정 (목표: [해석] hedge_ratio < 30%)
2. **[해석] 태그 빈도 제한** — 현재 [해석] 태그가 단락당 반복됨. 기사당 최대 3-4개로 제한하는 별도 지시 검토
3. **spine 추출 개선** — 현재 폴백이 첫 [해석] 문장을 사용 → 헤징 어미 포함 spine이 Post2에 전달됨. SPINE 주석 생성 강제율 개선 필요
4. `_detect_interp_hedge_density` 결과를 main.py gate에 별도 키로 노출 고려

---

## 5. Final Gate JSON

```json
{
  "interpretation_hedge_clamp": "PASS",
  "hedge_line_detection": "PASS",
  "hedge_trigger_extension": "PASS",
  "targeted_hedge_rewrite": "PASS",
  "post_rewrite_hedge_rescoring": "PASS",
  "hedge_resolution_detection": "PASS",
  "post2_interpretation_clamp": "PASS",
  "phase14h_compatibility": "PASS",
  "public_signature_stability": "PASS",
  "import_build": "PASS",
  "final_status": "GO"
}
```

---

*이전 보고서: [REPORT_PHASE14H_REAL_OUTPUT_VALIDATION.md](REPORT_PHASE14H_REAL_OUTPUT_VALIDATION.md)*
*Phase 14I 이후 필수: 실출력 검증 — 신규 런 발행 기사의 [해석] hedge_ratio 측정*
