# REPORT_PHASE16D_CONTINUITY_AND_BRIDGE_HARDENING.md

**Phase**: 16D — Continuity & Bridge Hardening
**작성일**: 2026-03-19
**구현 파일**: `generator.py`
**최종 판정**: **PHASE16D_IMPL_GO**

---

## 1. 배경

Phase 16C 실출력 검증에서 `PHASE16C_OUTPUT_HOLD` 판정을 받았다.
HOLD 원인 3가지:

1. Post1/Post2 도입부 34.7% HIGH 중복 — `post1_post2_continuity: FAIL` 지속
2. Post2 "오늘 이 테마를 보는 이유" 섹션이 Post1 매크로 배경을 1:1 재서술
3. Post2 픽-테마 브릿지 약함 (XLE·SK하이닉스·하나마이크론 테마 분산)
4. `emergency_polish` 진단 로그 비가시 (FAILED_NO_REVISION 아닌 경우 미출력)

Phase 16D는 위 3+1 원인을 **프롬프트 레벨 + 진단 레벨 정밀 보강**으로 해결하는 페이즈다.
대규모 구조 개편 없이, temporal SSOT 성과를 절대 훼손하지 않으며 진행했다.

---

## 2. Phase 16C HOLD 원인 재정리

| 원인 | 분류 | 16D 타깃 |
|------|------|---------|
| 도입부 n-gram 34.7% HIGH 중복 | 프롬프트 미약 | Track A |
| "오늘 이 테마를 보는 이유" 매크로 반복 | 프롬프트 미약 | Track A |
| 픽-테마 브릿지 누락 | 프롬프트 미약 | Track B |
| emergency_polish 로그 미출력 | 관측성 부족 | Track D |
| intro_overlap 임계값 미표시 | 관측성 부족 | Track C |

---

## 3. 구현 변경점 요약

### 3.1 변경된 파일
- `generator.py` (4개 구간 수정)

### 3.2 추가된 상수 (lines ~3058–3094)
```
_P16D_POST2_CONTINUITY_HARDENING   ← Track A
_P16D_POST2_BRIDGE_REQUIREMENT     ← Track B
```

### 3.3 수정된 함수
- `_p16b_emergency_polish()` — 시그니처 + 로그 변경 (Track D)
- `_p16b_compute_intro_overlap()` — 로그 + 리턴 dict 보강 (Track C)

### 3.4 수정된 호출부
- `gpt_write_picks()` user_msg 조립 (Track A+B 주입)
- `gpt_write_post()` Post1 emergency_polish 호출 (Track D)
- `gpt_write_post2()` Post2 emergency_polish 호출 (Track D)

---

## 4. Continuity 억제 장치 (Track A) 설명

### 상수: `_P16D_POST2_CONTINUITY_HARDENING`

```
[Phase 16D — Post2 매크로 재서술 억제 ★]

Post2([캐시의 픽])에서 '오늘 이 테마를 보는 이유' 또는 유사 섹션을 작성할 때:

❌ 금지:
  - Post1([심층분석])이 이미 서술한 거시 배경(호르무즈 해협 수치, 브렌트유 가격,
    FOMC 결정 내용, 달러 강세 등)을 같은 분량으로 다시 설명
  - '중동 전쟁이 X주 차에 접어들며...' / 'Y 해협 통행량이 Z% 급감...'
    류의 사건 경위 재서술
  - 거시 배경 단독 설명 문단이 2문장을 초과

✅ 필수:
  - 매크로 사실은 1~2문장 이내 요약으로만 참조하고,
    즉시 '그렇다면 어떤 종목/섹터가 이 흐름에서 포지셔닝 기회를 갖는가?'로 전환
  - 섹션 첫 문장부터 종목 바스켓 또는 투자 각도를 명시
```

**주입 위치**: `gpt_write_picks()` `user_msg` 조립부 — `_P15C_POST2_LABEL_BAN` 직후 (최우선 순서 2위)

**작동 원리**: GPT가 Post2의 배경 재서술 섹션을 작성할 때 명시적 금지 규칙을 읽고, 매크로 배경 2문장 이내 요약 + 즉시 종목 각도 전환 구조로 쓰도록 유도한다.

---

## 5. 픽-테마 브릿지 강제 장치 (Track B) 설명

### 상수: `_P16D_POST2_BRIDGE_REQUIREMENT`

```
[Phase 16D — 픽-테마 브릿지 강제 ★]

종목 개별 섹션(메인 픽 / 보조 픽)을 시작하기 직전에,
'왜 이 종목들이 오늘의 매크로 국면에서 한 바구니에 담겼는가'를
1~2문장으로 설명하는 브릿지 문장을 반드시 포함하라.

브릿지 문장 기준:
  - 공통 투자 논리(예: 고유가 직수혜, 금리 내성, AI 인프라 수요 등)를 명시
  - 서로 다른 성격의 종목이 함께 들어가면, 묶는 기준을 먼저 제시
  - 브릿지는 구체적이어야 하며, 'X, Y, Z를 함께 봅니다' 식의 단순 나열 금지
```

**주입 위치**: `_P16D_POST2_CONTINUITY_HARDENING` 직후 (Track A와 페어)

**작동 원리**: 종목 개별 섹션 이전에 공통 투자 논리 1~2문장을 강제함으로써 Gemini Step3의 "테마 분산 지적"을 upstream에서 방지한다. 하드코딩 문구 금지 원칙으로 기사마다 맥락에 맞는 브릿지가 생성되도록 예시 방향만 제시.

---

## 6. `emergency_polish` 관측성 변경 (Track D)

### 변경 전
```python
# Post1
_p16b_polish_log: dict = {}
if _p1_step3_status == "FAILED_NO_REVISION":
    final_content, _p16b_polish_log = _p16b_emergency_polish(
        final_content, label="Post1"
    )
```

```
→ FAILED_NO_REVISION 아닌 경우 호출 자체 없음 → p13_scores에 {} 저장, 로그 없음
```

### 변경 후
```python
# Post1 & Post2 — 항상 실행
final_content, _p16b_polish_log = _p16b_emergency_polish(
    final_content, label="Post1", step3_status=_p1_step3_status
)
```

### 함수 시그니처 변경
```python
# 변경 전
def _p16b_emergency_polish(content: str, label: str = "Post") -> tuple

# 변경 후
def _p16b_emergency_polish(
    content: str, label: str = "Post", step3_status: str = "PASS"
) -> tuple
```

### 로그 출력 변경
- 기존: generic 마커 있을 때만 WARNING 로그
- 신규: 항상 INFO/WARNING 로그 + mode + step3_status 명시

**실행 예시 (매번 출력)**:
```
[Phase 16B] Post1 emergency_polish: generic 마커 없음 | status=PASS | mode=routine-diagnostic | step3=FAILED_REVISION_ADOPTED
[Phase 16B] Post2 emergency_polish: generic 마커 3건 | status=WARN | mode=routine-diagnostic | step3=FAILED_REVISION_ADOPTED
```

**리턴 dict 변경**:
```python
{
    "applied": False,                          # 변경 없음 — 원칙 유지
    "mode": "routine-diagnostic",             # 신규 — fallback vs routine 구분
    "step3_status": "FAILED_REVISION_ADOPTED", # 신규 — step3 상태 포함
    "total_generic_found": 3,
    "markers": [...],
    "status": "WARN",
    "note": "diagnostic-only — 실 치환 미수행 (Phase 16D 원칙 유지)",
}
```

---

## 7. intro_overlap 진단 보강 (Track C)

### 변경 전 로그
```
[Phase 16B] 도입부 4-gram 중복: 34.7% (HIGH) | 공유 n-gram 95개
[Phase 16B] 도입부 HIGH 중복 감지 — 16C에서 각도 분리 강화 필요. 샘플: [...]
```

### 변경 후 로그
```
[Phase 16B] 도입부 4-gram 중복: 34.7% (HIGH) | 공유 n-gram 95개 | 기준: LOW<15% / MEDIUM<30% / HIGH≥30%
[Phase 16B] 도입부 HIGH 중복 감지 (임계값: ≥30%) — 반복 n-gram 샘플: [...]
```

- `MEDIUM` 상태에도 WARNING 출력 추가 (기존: HIGH만)
- 리턴 dict에 `thresholds`, `intro_chars_used` 추가

---

## 8. Temporal SSOT 비회귀 보호 (Track E)

Phase 16D에서 변경한 코드 범위:

| 영역 | 변경 여부 | 비고 |
|------|----------|------|
| `_build_temporal_ssot()` | ❌ 미변경 | SSOT 계산 로직 그대로 |
| `_build_p16_generation_block()` | ❌ 미변경 | GPT 주입 블록 그대로 |
| `_build_p16_step3_block()` | ❌ 미변경 | Step3 주입 블록 그대로 |
| Phase 15D/15E/15F | ❌ 미변경 | 시제 교정 레이어 그대로 |
| Step3 팩트체크/수정 | ❌ 미변경 | verify_draft() 그대로 |
| Post2 user_msg (Track A+B 추가) | ✅ 변경 | 시제 무관한 continuity 규칙만 추가 |
| emergency_polish | ✅ 변경 | applied=False 원칙 유지, prose 미수정 |

**결론**: 시제/SSOT/팩트 레이어 일체 미접촉. Track A+B는 prose 생성 지시문이며 시제 해석과 무관.

---

## 9. 자체 점검 결과

| 체크 항목 | 결과 |
|----------|------|
| Step3 상태와 무관하게 `step3_status` 로그 남는가? | ✅ YES — emergency_polish 항상 실행, step3_status INFO 포함 |
| `intro_overlap`에 수치+상태+기준 정보가 남는가? | ✅ YES — `기준: LOW<15% / MEDIUM<30% / HIGH≥30%` 추가 |
| `emergency_polish` 실행/스킵 여부+이유가 보이는가? | ✅ YES — mode=routine-diagnostic/fallback-diagnostic + step3 상태 |
| Post2 도입부가 Post1 매크로 서론 재서술하지 않도록 유도됐는가? | ✅ YES — `_P16D_POST2_CONTINUITY_HARDENING` 주입 |
| Post2 종목 바스켓 앞 브릿지 논리가 필수화됐는가? | ✅ YES — `_P16D_POST2_BRIDGE_REQUIREMENT` 주입 |
| temporal SSOT 비회귀가 보장되는가? | ✅ YES — 시제 관련 코드 일체 미수정 |
| syntax / compile / 정적 검증이 통과하는가? | ✅ YES — `python -c "import generator"` + 4개 항목 단언 통과 |

---

## 10. 정적 검증 결과

```bash
$ python -c "
import generator
# 상수 존재 확인
assert hasattr(generator, '_P16D_POST2_CONTINUITY_HARDENING')
assert hasattr(generator, '_P16D_POST2_BRIDGE_REQUIREMENT')
# emergency_polish 시그니처
import inspect
sig = inspect.signature(generator._p16b_emergency_polish)
assert 'step3_status' in sig.parameters
# intro_overlap return dict
src = inspect.getsource(generator._p16b_compute_intro_overlap)
assert 'thresholds' in src
assert 'intro_chars_used' in src
print('ALL CHECKS PASSED')
"
ALL CHECKS PASSED
```

---

## 11. 잔여 위험

| 위험 | 수준 | 비고 |
|------|------|------|
| GPT가 새 프롬프트 규칙을 무시하고 여전히 매크로 재서술할 가능성 | MEDIUM | 프롬프트 지시는 확률적 — Phase 16E 실출력으로 확인 필요 |
| 브릿지 문장이 "하드코딩 예시 문구 반복"으로 고착될 가능성 | LOW | 예시 방향만 제시, 하드코딩 금지 명시함 |
| Track A+B 프롬프트 추가로 인한 총 user_msg 토큰 증가 | LOW | +약 400~450 토큰 (6000 토큰 한도 내 여유 충분) |

---

## 12. Phase 16E 실출력 검증 포인트

Phase 16E에서 반드시 확인해야 할 사항:

1. **Post2 "오늘 이 테마를 보는 이유" 구간** — 거시 배경 서술이 2문장 이내인가?
2. **Post2 첫 단락** — 종목/포지셔닝 각도에서 즉시 시작하는가?
3. **픽 섹션 이전 브릿지 문장** — 공통 투자 논리가 1~2문장으로 명시됐는가?
4. **emergency_polish 로그** — 매 런마다 INFO 수준으로 출력되는가?
5. **intro_overlap 수치** — 임계값 기준과 함께 로그에 표시되는가?
6. **시제 비회귀** — Phase 15D/15E/15F 및 SSOT가 여전히 정상 작동하는가?
7. **p16b_guard.intro_overlap 수치** — 16C 대비 감소했는가? (34.7% → 목표 MEDIUM 이하 <30%)

---

*보고서 생성: Claude Code (Phase 16D 구현)*
