# REPORT_PHASE15B_VERB_ENDING_COVERAGE_MICRO_HOTFIX

**작성일:** 2026-03-17
**커밋:** d97f0b2
**대상 파일:** `generator.py`
**Phase 상태:** 구현 GO — 8/8 단위 테스트 PASS

---

## 1. Changed Files

| 파일 | 변경 유형 | 변경 위치 |
|------|-----------|-----------|
| `generator.py` | 추가 | `_P15B_COMPOUND_RE_CONNECTIVE` regex 상수 |
| `generator.py` | 추가 | `_P15B_CONNECTIVE_ENDING_MAP` dict 상수 |
| `generator.py` | 수정 | `_P15_TENSE_CORRECTION_MAP` 상단에 됩니다/된다 외 17개 연결어미 패턴 추가 |
| `generator.py` | 수정 | `_enforce_tense_correction()` Step 0b 추가 |
| `docs/REPORT_PHASE15B_VERB_ENDING_COVERAGE_MICRO_HOTFIX.md` | 신규 | 본 보고서 |

---

## 2. Implementation Summary

### 2.1 Phase 15A HOLD 원인 재확인

Phase 15A 실출력 검증(run_id: 20260317_145007)에서 발견된 미교정 잔존 문장:

```
전: [전망] 2024년 SK하이닉스는 매출 55조 7,362억 원과 영업이익 21조 3,145억 원을
    기록할 것으로 전망되며, 이는 전년 대비 각각 101.7%와 556.6% 증가한 수치로 파악됩니다.
```

**근본 원인:**
- GPT가 처음엔 올바르게 과거형(`기록했습니다`)으로 작성
- Gemini Step3 검수기가 "2024년은 현재 진행 중인 연도"로 오인 → [전망] 태그와 `기록할 것으로 전망되며` 주입
- Phase 15A regex (`됩니다|된다`만 커버) → `되며` 어미 미매칭
- 리스트 맵도 `되며` 어미 패턴 없음 → 교정 완전 실패

**정확한 갭:** `됩니다|된다` 이외 연결어미(`되며|되고|되어`) 미커버

### 2.2 Phase 15B 변경 내용

#### Change 1 — `_P15B_COMPOUND_RE_CONNECTIVE` 추가

```python
_P15B_COMPOUND_RE_CONNECTIVE = re.compile(
    r"([가-힣]+)할(\s+것으로\s+)(추정|예상|전망|기대|관측)(되며|되고|되어)"
)
_P15B_CONNECTIVE_ENDING_MAP = {
    "되며": "됐으며",   # 전망되며  → 집계됐으며  (연결어미 유지)
    "되고": "됐고",     # 전망되고  → 집계됐고   (연결어미 유지)
    "되어": "됐다",     # 전망되어  → 집계됐다   (자연스러운 종결)
}
```

#### Change 2 — `_enforce_tense_correction()` Step 0b

```python
# Phase 15B Step 0b: 연결어미 커버 확장 (되며/되고/되어)
updated = _P15B_COMPOUND_RE_CONNECTIVE.sub(
    lambda m: m.group(1) + "한" + m.group(2) + "집계" + _P15B_CONNECTIVE_ENDING_MAP[m.group(4)],
    updated,
)
```

이 스텝은 Phase 15A Step 0 (`됩니다|된다`) 직후, 리스트 맵 적용 전에 실행됨.

#### Change 3 — `_P15_TENSE_CORRECTION_MAP` 연결어미 패턴 17개 추가

맵 최상단에 `되며|되고|되어` 계열 복합 패턴 명시 추가 (regex 안전망 보완):

```python
("기록할 것으로 전망되며",  "기록한 것으로 집계됐으며"),
("기록할 것으로 전망되고",  "기록한 것으로 집계됐고"),
("달성할 것으로 전망되며",  "달성한 것으로 집계됐으며"),
("증가할 것으로 전망되며",  "증가한 것으로 집계됐으며"),
... (총 17개)
```

### 2.3 교정 전후 비교 (HOLD 원인 문장)

```
전: [전망] 2024년 SK하이닉스는 매출 55조 7,362억 원과 영업이익 21조 3,145억 원을
    기록할 것으로 전망되며, 이는 전년 대비 각각 101.7%와 556.6% 증가한 수치로 파악됩니다.

후: [전망] 2024년 SK하이닉스는 매출 55조 7,362억 원과 영업이익 21조 3,145억 원을
    기록한 것으로 집계됐으며, 이는 전년 대비 각각 101.7%와 556.6% 증가한 수치로 파악됩니다.
```

미래형 어간(`기록할`) → 완료형 어간(`기록한`), 미래형 동사(`전망되며`) → 완료형 동사(`집계됐으며`).

---

## 3. Verification Results

### 3.1 단위 테스트 (8/8 PASS)

| # | 패턴 | 기대 결과 | 판정 |
|---|------|-----------|------|
| 1 | `기록할 것으로 전망되며` (2024년) | `기록한 것으로 집계됐으며` | **PASS** |
| 2 | `달성할 것으로 예상되고` (2024년) | `달성한 것으로 집계됐고` | **PASS** |
| 3 | `증가할 것으로 추정되어` (2024년) | `증가한 것으로 집계됐다` | **PASS** |
| 4 | `기록할 것으로 추정됩니다` (2025년) — Phase15A | `기록한 것으로 집계됐습니다` | **PASS** |
| 5 | `달성할 것으로 예상된다` (2024년) — Phase15A | `달성한 것으로 집계됐다` | **PASS** |
| 6 | `증가할 것으로 전망되며` (2027년) — 미래연도 | 탐지 안 됨 (PASS) | **PASS** |
| 7 | `_has_mixed_tense_residue` — 교정 후 잔여 없음 | False | **PASS** |
| 8 | 잠정 마커 포함 → 자동 교정 제외 | WARN (예외 처리 유지) | **PASS** |

### 3.2 Phase 15A 호환성 확인

- Tests 4, 5 (됩니다/된다 어미) 모두 PASS — Phase 15A 기능 유지
- `_detect_completed_year_as_forecast()` 시그니처 변경 없음
- `_enforce_tense_correction()` 반환 타입 유지
- 빌드: `venv/bin/python3 -c "import generator; print('OK')"` → OK

---

## 4. Risks / Follow-up

### 4.1 잔존 리스크

| 리스크 | 심각도 | 설명 |
|--------|--------|------|
| Gemini Step3 시제 오인 (근본 원인) | 높음 | Phase 15B는 교정 레이어 안전망만 강화. 근본 원인(Step3가 2024년을 현재 진행 연도로 오인)은 별도 해결 필요 |
| 기타 미커버 어미 | 낮음 | `되는데`, `됩니다만`, `될 것이며` 등 더 드문 패턴 잔존 가능 |
| `되어` → `됐다` 자연스러움 | 낮음 | `되어` 종결 시 `됐다`로 변환하는데, 문맥에 따라 `돼` 또는 `됐었다`가 더 자연스러울 수 있음 |

### 4.2 권장 후속 작업

1. **Phase 15B 실출력 검증 즉시 실행** — 교정이 실제 발행 문장에서 작동하는지 확인
2. **Gemini Step3 시제 컨텍스트 주입 (Phase 15C)** — `발행 기준일 = 2026년, 2024/2025 = 완료 연도` 명시 주입으로 근본 원인 차단
3. **`_P15A_COMPOUND_RE_FORMAL/INFORMAL` 통합 리팩토링** — Phase 15A와 15B의 두 regex를 하나의 통합 패턴으로 정리 (기능 영향 없는 유지보수용, 우선순위 낮음)

---

## 5. Final Gate JSON

```json
{
  "ending_coverage_expansion": "PASS",
  "doemyeo_family_support": "PASS",
  "replacement_logic_update": "PASS",
  "mixed_tense_residue_removal": "PASS",
  "phase15a_compatibility": "PASS",
  "public_signature_stability": "PASS",
  "import_build": "PASS",
  "final_status": "GO"
}
```

---

## 6. 검증 체크리스트

- [x] `되며` 커버 동작 확인 (`기록할 것으로 전망되며` → `기록한 것으로 집계됐으며`)
- [x] 확장 어미 패밀리 커버 (`되며`, `되고`, `되어` 모두 PASS)
- [x] 교체 결과 자연스러움 (`됐으며`, `됐고`, `됐다` 과거 연결어미 보존)
- [x] 교정 후 혼재 시제 잔여 없음 (`_has_mixed_tense_residue()` PASS)
- [x] Phase 15A 호환성 유지 (됩니다/된다 패턴 Tests 4, 5 PASS)
- [x] 공개 함수 시그니처 안정성 유지
- [x] import/build PASS
