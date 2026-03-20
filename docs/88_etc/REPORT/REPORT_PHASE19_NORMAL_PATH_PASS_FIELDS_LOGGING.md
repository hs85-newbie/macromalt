# REPORT_PHASE19_NORMAL_PATH_PASS_FIELDS_LOGGING.md

작성일: 2026-03-20
Phase: **Phase 19 — 정상 발행 경로 4개 pass 필드 로그화 개발 반영 보고서**
최종 판정: **GO**

---

## 1. 변경 파일 목록

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `generator.py` | 추가 + 리팩터 | `_calc_quality_pass_fields()` 추출, `_log_normal_publish_event()` 추가, `_log_parse_failed_event()` 리팩터 |
| `main.py` | 추가 | Phase 19 정상발행 품질로그 호출 블록 삽입 |

---

## 2. 수정 위치 요약

### generator.py

#### 신규 함수 1: `_calc_quality_pass_fields(content: str) -> dict`
- 위치: `_log_parse_failed_event()` 직전 (line ~5382)
- 역할: 4개 pass 필드를 계산하는 **단일 진실 소스 함수**
- PARSE_FAILED 경로 / 정상 발행 경로 양쪽에서 동일 정의로 호출됨
- 반환: `{opener_pass, criteria_1_pass, criteria_5_pass, source_structure_pass}`

#### 신규 함수 2: `_log_normal_publish_event(...) -> dict`
- 위치: `_calc_quality_pass_fields()` 직후 (line ~5424)
- 역할: 정상 발행 경로에서 4개 pass 필드 + final_status + public_url을 운영 로그에 기록
- 로그 레벨: `INFO` (`PARSE_FAILED`는 `WARNING` — 레벨 구분 유지)
- 로그 태그: `[Phase 19] 정상발행 품질로그`

#### 기존 함수 리팩터: `_log_parse_failed_event()`
- 변경 전: 4개 pass 필드를 함수 내부에서 직접 계산
- 변경 후: `_calc_quality_pass_fields(raw_output)` 호출로 위임
- 의미 변경 없음 — bool 값, 판정 기준 완전 동일

### main.py

#### 신규 블록: Phase 19 정상발행 품질로그
- 위치: Phase 10 발행 이력 저장 직후 (`save_publish_history()` 블록 뒤)
- 내용:
  ```python
  from generator import _log_normal_publish_event
  if post1_result:
      _log_normal_publish_event(run_id=..., slot=..., post_type="post1", ...)
  if post2_result:
      _log_normal_publish_event(run_id=..., slot=..., post_type="post2", ...)
  ```
- 비치명 처리: `except Exception as e: logger.warning(...)` — 품질로그 실패가 발행 파이프라인을 중단하지 않음

---

## 3. 로그 Before / After 비교

### Before (Phase 19 T1까지의 정상 발행 로그)

```
2026-03-20 13:43:31 [INFO] WordPress 업로드 성공 | Post ID: 225 | URL: https://macromalt.com/...
2026-03-20 13:43:32 [INFO] WordPress 업로드 성공 | Post ID: 226 | URL: https://macromalt.com/...
2026-03-20 13:43:32 [INFO]   final_status: GO
2026-03-20 13:43:32 [INFO]      URL     : https://macromalt.com/...
2026-03-20 13:43:32 [INFO]      URL     : https://macromalt.com/...
```
→ **4개 pass 필드 없음. 정상 발행 경로에서는 품질 증적 0.**

### After (Phase 19 정상발행 품질로그 반영 후)

```
2026-03-20 15:42:17 [INFO] [Phase 19] 정상발행 품질로그 | run_id=20260320_154017 | slot=evening | post_type=post1 | final_status=GO | opener_pass=False | criteria_1_pass=True | criteria_5_pass=True | source_structure_pass=True | public_url=https://macromalt.com/...
2026-03-20 15:42:17 [INFO] [Phase 19] 정상발행 품질로그 | run_id=20260320_154017 | slot=evening | post_type=post2 | final_status=GO | opener_pass=True | criteria_1_pass=True | criteria_5_pass=True | source_structure_pass=True | public_url=https://macromalt.com/...
```
→ **Post1 / Post2 각각 4개 pass 필드 + final_status + public_url 직접 기록.**

---

## 4. 신규 run_id

`20260320_154017`

---

## 5. 공개 URL

| post_type | Post ID | URL |
|-----------|---------|-----|
| post1 | 227 | https://macromalt.com/%ec%8b%ac%ec%b8%b5%eb%b6%84%ec%84%9d-%ec%a6%9d%ea%b6%8c%ec%97%85%ec%a2%85%ec%9d%98-%eb%b8%8c%eb%a1%9c%ec%bb%a4%eb%a6%ac%ec%a7%80-%ec%88%98%ec%9d%b5-%ea%b8%89%ec%a6%9d%ea%b3%bc-%ea%b2%8c%ec%9e%84/ |
| post2 | 228 | https://macromalt.com/%ec%ba%90%ec%8b%9c%ec%9d%98-%ed%94%bd-%ec%97%94%ec%94%a8%ec%86%8c%ed%94%84%ed%8a%b8-%ec%99%b8-%ec%a6%9d%ea%b6%8c%ea%b3%bc-%ea%b2%8c%ec%9e%84%ec%9d%98-%ec%9d%b4%ec%9d%b5-%eb%aa%a8%eb%a9%98/ |

---

## 6. 대표 로그 2건

### Post1 (post_type=post1)

```
2026-03-20 15:42:17 [INFO] [Phase 19] 정상발행 품질로그 | run_id=20260320_154017 | slot=evening | post_type=post1 | final_status=GO | opener_pass=False | criteria_1_pass=True | criteria_5_pass=True | source_structure_pass=True | public_url=https://macromalt.com/...심층분석-증권업종의-브로커리지-수익-급증과-게임.../
```

**`opener_pass=False` 해석 메모**:
`opener_pass`의 pick-angle 패턴(`왜\s+지금\s+\S+인가` 등)은 Post2(캐시의 픽) 전용 opener 구조다.
Post1(심층분석)은 이 패턴을 사용하지 않으므로 `False`가 **정상값**이다.
향후 Post1과 Post2의 opener 기준을 분리 정의하는 개선 과제로 남긴다 (이번 작업 범위 외).

### Post2 (post_type=post2)

```
2026-03-20 15:42:17 [INFO] [Phase 19] 정상발행 품질로그 | run_id=20260320_154017 | slot=evening | post_type=post2 | final_status=GO | opener_pass=True | criteria_1_pass=True | criteria_5_pass=True | source_structure_pass=True | public_url=https://macromalt.com/...캐시의-픽-엔씨소프트.../
```

Post2 기준 4개 필드 전건 `True`. pick-angle opener 정상 유지 확인.

---

## 7. 기존 PARSE_FAILED 경로와의 충돌 여부

- `_log_parse_failed_event()`는 `_calc_quality_pass_fields()` 호출로 리팩터됨
- `_log_normal_publish_event()`도 동일 함수 호출
- 동일 content에 대해 두 경로에서 bool 값이 달라질 수 없음 (단일 진실 소스)
- `PARSE_FAILED` 로그 포맷(15개 필드)은 변경 없음
- **충돌 없음**

---

## 8. 최종 판정

**GO**

- 정상 발행 경로에서 4개 pass 필드 로그 반영 완료
- Post1 / Post2 모두 적용 완료
- PARSE_FAILED 경로와 의미 충돌 없음
- 신규 run 1회 수행, 실발행본 및 공개 URL 확보
- 운영 로그에서 `slot=evening`, `post_type=post1/post2`, 4개 pass 필드, `final_status=GO`, `public_url` 전부 확인

---

## 9. 비고 — 개선 과제 (이번 작업 범위 외)

`opener_pass`는 현재 Post2 전용 pick-angle 패턴만 검사한다.
Post1에서는 항상 `False`가 기록되어 직관적이지 않다.
Phase 20 이후 `post_type`별 opener 기준 분리를 권장한다.
