# REPORT_PHASE16F_BRIDGE_ALIGNMENT_AND_STATUS_STANDARDIZATION.md

**Phase**: 16F — Bridge Alignment & Status Standardization
**작성일**: 2026-03-19
**최종 판정**: **PHASE16F_IMPL_GO**

---

## 1. 배경

Phase 16E 실출력 검증에서 `PHASE16E_OUTPUT_CONDITIONAL_GO` 판정을 받았다.
잔존 이슈 2가지:

1. **브릿지-픽 불일치**: "에너지 vs 기술 섹터" 대비형 브릿지가 생성됐으나, 실제 픽(S-Oil + XLE)은 모두 에너지 섹터 → 브릿지 논리와 바스켓 불일치
2. **step3_status 명칭 혼용**: 코드값 `"REVISED"` vs 구 보고서 표기 `"FAILED_REVISION_ADOPTED"` → 운영 해석 혼선

16F는 이 두 가지를 미세조정으로 해결한다. 대규모 구조 개편 없이 프롬프트 강화 + 코드 주석/docstring 정비 수준으로만 처리한다.

---

## 2. Phase 16E HOLD 원인 재정리

| 원인 | 분류 | 16F 타깃 |
|------|------|----------|
| 브릿지 문장이 픽 바스켓과 논리 불일치 | 프롬프트 미약 | Track A |
| step3_status 명칭 코드/문서 불일치 | 문서 혼선 | Track B |
| 브릿지 타입 관측 로그 부재 | 관측성 부족 | Track C |

---

## 3. 변경 파일 목록

- `generator.py` (3개 구간 수정 + 1개 함수 추가)

---

## 4. 구현 변경점 상세

### Track A — Bridge Alignment Guard

#### 변경 대상
`_P16D_POST2_BRIDGE_REQUIREMENT` 상수 (lines ~3074–3097)

#### 변경 전 (Phase 16D)
```
[Phase 16D — 픽-테마 브릿지 강제 ★]
- 공통 투자 논리 명시
- 서로 다른 성격의 종목이면 묶는 기준 제시
- 예시: 에너지 섹터와 AI/반도체를 함께 담는다 (← 대비형 예시!)
```

#### 변경 후 (Phase 16F)
```
[Phase 16D/16F — 픽-테마 브릿지 강제 ★ 픽 정합성 필수]

브릿지 작성 필수 원칙 (픽 정합성):
  ★ 브릿지는 반드시 최종 선정 종목 리스트의 실제 공통 속성에만 기반해야 한다.
  ★ '섹터 A vs 섹터 B' 대비형 브릿지는 실제로 양쪽 섹터에 모두 픽이 있을 때만 사용하라.
    픽이 모두 같은 섹터에 속하면 대비형 축은 절대 쓰지 말라.
  ★ 공통 논리가 뚜렷하지 않으면 과장하지 말고 더 좁고 안전한 표현으로 쓰라.

브릿지 유형 가이드:
  [동일 섹터 픽] → 공통 수혜 논리 / 공통 민감도 / 헤지 구조 차이로 묶어라
  [이종 섹터 픽] → 오늘 매크로 국면에서 두 섹터를 동시에 보는 이유를 1문장으로 연결하라
  [단일 픽]      → 픽-테마 연결 한 문장으로 충분하다

❌ 금지:
  - 픽 바스켓에 없는 섹터를 브릿지에서 언급
  - 픽 확정 전 가상 후보군 기준으로 브릿지를 생성하는 것
```

**효과 원리**:
- GPT가 user_msg 내 `tickers_and_prices` (최종 픽 목록)를 먼저 읽고, 그 이후 연결되는 브릿지 규칙에서 "최종 선정 종목 리스트"를 참조하도록 명시
- "대비형 브릿지는 양쪽 섹터에 픽이 있을 때만" 규칙이 GPT의 브릿지 생성 경로를 제한
- 기존 energy+semiconductor 예시 삭제 → 대비형 브릿지 생성을 유도하던 템플릿 제거

---

### Track B — step3_status 표준화

#### Phase 16F 표준 enum

| 코드값 | 의미 | 구 보고서 표기 |
|--------|------|-------------|
| `"PASS"` | Step3 팩트체크 이슈 없음 (검수 통과) | — (동일) |
| `"REVISED"` | Step3 이슈 발견, 수정본 채택 성공 | `"FAILED_REVISION_ADOPTED"` (16B/16C 보고서) |
| `"FAILED_NO_REVISION"` | Step3 수정 API 실패 (503/timeout) | — (동일) |

#### 변경 1: `verify_draft()` 내 enum 블록 주석 추가 (line ~5093)

```python
# Phase 16B/16F step3_status enum (표준, Phase 16F에서 전체 통일):
#   "PASS"              — Step3 팩트체크 이슈 없음 (검수 통과)
#   "REVISED"           — Step3 이슈 발견, 수정본 채택 (구 보고서: "FAILED_REVISION_ADOPTED"와 동일)
#   "FAILED_NO_REVISION"— Step3 수정 API 실패 (503/timeout 등), GPT 초안 원본 발행
step3_status = "PASS"
```

#### 변경 2: `_p16b_emergency_polish()` docstring 수정 (line ~3121)

```python
# 변경 전
step3_status: 현재 Step3 처리 상태 (PASS / FAILED_REVISION_ADOPTED / FAILED_NO_REVISION).

# 변경 후
step3_status: 현재 Step3 처리 상태 (PASS / REVISED / FAILED_NO_REVISION).
              Phase 16F 표준 enum — 로그 컨텍스트로만 사용.
              ※ 구 보고서(16B/16C)에서 "FAILED_REVISION_ADOPTED"로 표기된 것은
                코드 기준 "REVISED"와 동일한 상태임 (Phase 16F에서 통일).
```

**결론**: 코드값 `"REVISED"` 유지 (가장 간결하고 정확). 구 보고서 표기와의 매핑은 주석으로 명시. 이후 모든 보고서/핸드오프에서 `"REVISED"` 사용.

---

### Track C — Bridge Observability (신규 함수 추가)

#### 신규 함수: `_p16f_diagnose_bridge(content, picks) -> dict`

```python
def _p16f_diagnose_bridge(content: str, picks: list) -> dict:
    """Phase 16F Track C: Post2 브릿지 타입 진단 (관측 전용, 본문 무수정)"""
```

**감지 항목**:
- `bridge_found`: "오늘 이 테마", "함께 담는", "공통 논리" 등 브릿지 키워드 존재 여부
- `bridge_mode`: `NONE` / `COMMON` / `CONTRAST`
  - `CONTRAST`: "vs", "상반된", "에너지 섹터와 기술" 등 대비 표현 감지
  - `COMMON`: 브릿지 존재하나 대비형 아님
- `contrast_risk`: `CONTRAST` 모드 + picks ≤ 2개인 경우 → WARNING 로그
- `picks`: 종목 ticker 목록 (정합성 추적용)

**로그 출력 예시**:
```
# 정상 케이스 (COMMON)
[Phase 16F] Post2 브릿지: found=True | mode=COMMON | picks=['S-OIL', 'XLE']

# 경고 케이스 (대비형 브릿지 + 동일 섹터 의심)
[Phase 16F] Post2 브릿지 타입: CONTRAST — 대비형 브릿지이나 picks=['S-OIL', 'XLE']
            (동일 섹터 가능성 있음). 브릿지-픽 정합성 확인 필요.
```

**호출 위치**: `gpt_write_post2()` 내 intro_overlap 계산 직후, p16b_guard에 `bridge_diag` 키로 저장

```python
_p16f_bridge_diag = _p16f_diagnose_bridge(final_content, parsed_picks)
...
"p16b_guard": {
    "step3_status":   ...,
    "intro_overlap":  ...,
    "bridge_diag":    _p16f_bridge_diag,  # Phase 16F 신규
},
```

---

## 5. Temporal SSOT 비회귀 보호

| 변경 영역 | 영향 |
|----------|------|
| `_P16D_POST2_BRIDGE_REQUIREMENT` | 시제 무관한 프롬프트 규칙만 추가 — SSOT 미접촉 |
| `verify_draft()` | 주석 추가만 — 실행 로직 미변경 |
| `_p16b_emergency_polish()` | docstring 수정만 — 로직 미변경 |
| `_p16f_diagnose_bridge()` | 신규 진단 함수 — 본문 무수정, SSOT 미접촉 |
| Phase 15D/15E/15F | 미접촉 |

---

## 6. 정적 검증 결과

```bash
$ python -c "
import generator, inspect

# Track A
assert '대비형 브릿지' in generator._P16D_POST2_BRIDGE_REQUIREMENT
assert '같은 섹터' in generator._P16D_POST2_BRIDGE_REQUIREMENT
assert '최종 선정 종목' in generator._P16D_POST2_BRIDGE_REQUIREMENT

# Track B
src = inspect.getsource(generator._p16b_emergency_polish)
assert 'REVISED' in src and 'FAILED_REVISION_ADOPTED' in src

src_vd = inspect.getsource(generator.verify_draft)
assert 'step3_status enum' in src_vd

# Track C (CONTRAST 감지)
html = '<p>오늘 이 테마를 보는 이유 에너지 섹터와 기술 섹터가 상반된 반응</p>'
r = generator._p16f_diagnose_bridge(html, [{'ticker': 'S-OIL'}, {'ticker': 'XLE'}])
assert r['bridge_mode'] == 'CONTRAST' and r['contrast_risk'] == True

# Track C (COMMON 정상 케이스)
html2 = '<p>오늘 이 테마를 보는 이유 공통 수혜 논리로 묶입니다</p>'
r2 = generator._p16f_diagnose_bridge(html2, [{'ticker': 'S-OIL'}, {'ticker': 'XLE'}])
assert r2['bridge_mode'] == 'COMMON'

print('ALL CHECKS PASSED')
"
ALL CHECKS PASSED
```

---

## 7. 자체 점검 결과

| 체크 항목 | 결과 |
|----------|------|
| 브릿지가 실제 픽 바스켓과 모순 방지 로직이 코드에 반영됐는가? | ✅ 프롬프트 규칙 + CONTRAST 감지 진단 |
| 대비형 브릿지 조건이 명시됐는가? | ✅ "양쪽 섹터에 모두 픽이 있을 때만" 명시 |
| step3_status 코드값과 로그값이 같은가? | ✅ 모두 "REVISED" 사용 |
| 보고서/핸드오프 표준이 정해졌는가? | ✅ "REVISED" 단일 표준, 매핑 주석 추가 |
| temporal SSOT 비회귀가 보장되는가? | ✅ 시제 코드 미접촉 |
| syntax/runtime 오류가 없는가? | ✅ 모든 단언 통과 |

---

## 8. 잔여 위험

| 위험 | 수준 | 설명 |
|------|------|------|
| GPT가 동일 섹터 픽에서도 대비형 브릿지 고집할 가능성 | LOW-MEDIUM | 프롬프트 강화됨, 실출력 검증으로 확인 필요 |
| `_p16f_diagnose_bridge`의 bridge_keywords가 모든 브릿지 형태를 포괄하지 못할 수 있음 | LOW | 진단 전용이므로 false negative는 로그 누락일 뿐, 본문 품질에 영향 없음 |
| step3_status="PARSE_FAILED" 케이스가 enum 표준에 미포함 | LOW | 극히 드문 케이스, 현재 문서 정리 범위 밖 |

---

## 9. Phase 16G 실출력 검증 포인트

1. **브릿지-픽 정합성**: Post2 브릿지가 실제 선정 종목 섹터와 일치하는가?
2. **bridge_diag 로그**: `[Phase 16F] Post2 브릿지: found=? | mode=? | picks=?` 출력 확인
3. **CONTRAST 경고**: 픽이 동일 섹터일 때 WARNING이 발생하지 않는가?
4. **step3_status 표기**: 로그/보고서에서 "REVISED" 단일 표기로 통일됐는가?
5. **temporal SSOT 비회귀**: Phase 15D/15E/15F 모두 PASS 유지
6. **intro_overlap**: MEDIUM 이하 유지

---

*보고서 생성: Claude Code (Phase 16F 구현)*
