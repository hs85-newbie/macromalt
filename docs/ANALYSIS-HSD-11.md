# ANALYSIS-HSD-11: HSD-5 반영 결과 점검 및 추가 조치 사항

- **이슈 ID**: HSD-11
- **작성일**: 2026-04-09
- **분석 범위**: HSD-5에서 제안된 모든 이슈의 반영 여부 + 부분 반영 항목의 잔존 위험
- **참조 커밋**: `0457944` (2026-04-08, "fix: HSD-5 우선순위 항목 반영")

---

## 1. 현황 요약

HSD-5 분석(2026-04-08)에서 P0 보안 3건, P1 코드 품질 4건, P2 개선 4건, 게시글 퀄리티 8건을 제안했다.
커밋 `0457944`에서 7개 항목이 반영됐으나, **2개 항목이 부분 반영**이고 **8개 항목이 미반영** 상태이다.
또한 반영 과정에서 새로운 2개 이슈가 발생했다.

### 반영 현황 요약표

| 이슈 | 분류 | 제목 | 반영 상태 |
|------|------|------|----------|
| P0 #1 | 보안 | API 설정 하드코딩 시크릿 제거 | ⚠ 부분 반영 |
| P0 #2 | 보안 | CORS wildcard 제거 | ✅ 완전 반영 |
| P0 #3 | 보안 | 결제 API 오류 응답 노출 차단 | ✅ 완전 반영 |
| P1 #4 | 품질 | generator.py 모듈 분리 | ❌ 미반영 |
| P1 #5 | 품질 | 광역 Exception 처리 개선 | ❌ 미반영 |
| P1 #6 | 품질 | 외부 API 재시도 로직 (tenacity) | ✅ 완전 반영 |
| P1 #7 | 품질 | 로거 설정 중복 제거 | ✅ 완전 반영 |
| P1 #8 | 보안 | _apply_ctx_to_env 패턴 제거 | ❌ 미반영 (M2 대기) |
| P2 #9 | 품질 | 의존성 upper bound 추가 | ✅ 완전 반영 |
| P2 #10 | 품질 | 비용 요금표 분리 | ❌ 미반영 |
| P2 #11 | 품질 | BackgroundTask 오류 추적 | ✅ 완전 반영 |
| P2 #12 | 품질 | publish_history.json 경쟁 조건 | ❌ 미반영 (M2 대기) |
| #F | 게시글 | 발행 전 품질 게이트 | ⚠ 부분 반영 |
| #A~#H (#F 제외) | 게시글 | 게시글 퀄리티 고도화 7건 | ❌ 미반영 |

---

## 2. 발견 이슈 목록

### 🔴 P0 — 잔존 보안 위험

#### 이슈 #1: config.py 시크릿 — ENVIRONMENT 미설정 시 우회 가능 (P0)

- **파일**: `api/core/config.py` (라인 14-21, 33)
- **반영 현황**: 부분 반영
- **현재 코드**:
  ```python
  JWT_SECRET_KEY: str = _DEV_SECRETS["JWT_SECRET_KEY"]  # 기본값이 dev 시크릿
  ...
  if settings.ENVIRONMENT == "production":   # ENVIRONMENT 설정해야 검사 실행
      ...raise ValueError(...)
  ```
- **잔존 위험**: Railway 배포 시 `ENVIRONMENT=production` 환경변수를 빠뜨리면 dev 시크릿이 프로덕션에서 사용됨. 원래 HSD-5 제안(`default=None` + 무조건 ValueError)이 더 안전했음.
- **수정 방향**:
  ```python
  JWT_SECRET_KEY: str = Field(default=None)  # 기본값 없음
  ...
  @model_validator(mode="after")
  def _validate_secrets(self):
      missing = [f for f in ["JWT_SECRET_KEY", "AES_SECRET_KEY", ...] if not getattr(self, f)]
      if missing:
          raise ValueError(f"필수 환경변수 누락: {missing}")
      return self
  ```
- **후속 이슈 제목**: `fix(m1): config.py 시크릿 기본값 완전 제거 — model_validator로 무조건 검증`

---

### 🟠 P1 — 코드 품질 (미반영 항목)

#### 이슈 #2: generator.py 과대 파일 (8,104줄) — 미반영

- **파일**: `generator.py`
- **현황**: HSD-5 분석 시와 동일하게 8,104줄 단일 파일 유지
- **영향**: LLM 에이전트가 파일 전체를 읽지 못해 분석·수정이 어려우며, 테스트 격리 불가
- **수정 방향**: HSD-5 이슈 #4의 모듈 분리 계획 그대로 유지
  ```
  generator/
  ├── __init__.py    themes.py    post1.py    post2.py
  ├── verifier.py    dedup.py     history.py
  ```
- **후속 이슈 제목**: `refactor(pipeline): generator.py 7개 모듈로 분리`

---

#### 이슈 #3: 광역 Exception 처리 — 미반영 (4곳 이상)

- **파일 및 위치**:
  - `generator.py` 518행: `except Exception: pass` (날짜 파싱 오류 묵살)
  - `generator.py` 1210행: `except Exception: pass` (staleness 검사 오류 묵살)
  - `macro_data.py` 144행: `except Exception: pass` (캐시 로드 오류 묵살)
  - `macro_data.py` 222행: `except Exception: return None` (숫자 파싱 오류 묵살)
  - `api/routers/pipeline.py` 41행: `except Exception: keys[...] = None` (복호화 실패 묵살)
  - `api/routers/pipeline.py` 57행: `except Exception: wp_password = None` (복호화 실패 묵살)
- **영향**: 복호화 실패 시 사용자 API 키가 None으로 세팅되면서 파이프라인이 "키 없음" 오류로 실패하나 원인 추적 불가
- **수정 방향**:
  ```python
  # pipeline.py 41행 예시
  try:
      keys[key_row.provider] = decrypt_api_key(key_row.key_enc, key_row.iv)
  except Exception as e:
      logger.error(f"[pipeline] {key_row.provider} API 키 복호화 실패: {e}", exc_info=True)
      keys[key_row.provider] = None
  ```
- **후속 이슈 제목**: `fix(pipeline): 광역 Exception catch에 logger.error 추가 — 원인 추적 가능하도록`

---

#### 이슈 #4: _apply_ctx_to_env() — os.environ 오염 (M2 대기 중)

- **파일**: `main.py` (라인 39-66)
- **현황**: 미반영. M2(멀티유저 전환) 작업 시 해결 예정
- **위험**: 단일 서버에서 동시에 2명의 사용자가 파이프라인을 실행하면 os.environ이 덮어써져 API 키 혼용 가능
- **현재 리스크**: M1(FastAPI) + BackgroundTasks 구조가 완성됐고 멀티 사용자 실행이 가능한 상태이므로, M2 이전에 이 버그가 실제 발생할 수 있음
- **우선순위 재검토 필요**: M2 대기보다 앞당겨야 할 가능성 있음
- **후속 이슈 제목**: `fix(m2): _apply_ctx_to_env 제거 — ctx를 함수 파라미터로 직접 전달`

---

### 🟡 P2 — 개선 사항 (미반영 항목)

#### 이슈 #5: 비용 요금표 하드코딩 — 미반영

- **파일**: `cost_tracker.py` (라인 25-34)
- **현황**: OpenAI/Gemini 요금 및 환율이 코드에 직접 하드코딩
  ```python
  OPENAI_INPUT_PRICE_PER_M = 2.50
  USD_TO_KRW = 1_380   # 수동 관리, 월 1회 업데이트 권장 (주석만 있음)
  ```
- **영향**: 요금 변동 시 코드 수정 필요. 환율 갱신 누락 시 비용 계산 오류
- **수정 방향**: `cost_rates.json` 분리 + 파일에서 로드
- **후속 이슈 제목**: `chore(pipeline): 비용 요금표를 cost_rates.json으로 분리`

---

#### 이슈 #6: publish_history.json 경쟁 조건 — 미반영 (M2 대기)

- **파일**: `generator.py` (save_publish_history 함수)
- **현황**: 미반영. M2에서 DB 기반 이력 관리로 전환 예정
- **영향**: 현재 M1 파이프라인이 BackgroundTask로 동시 실행 가능하므로 경쟁 조건 실제 발생 가능
- **후속 이슈 제목**: `fix(m2): publish_history.json → DB RunLog 테이블 기반으로 전환`

---

### 🟡 반영 품질 — 부분 반영 항목의 잔존 문제

#### 이슈 #7: 발행 전 품질 게이트 — 소프트 게이트로만 구현

- **파일**: `publisher.py` (라인 166-177, 270-272)
- **반영 현황**: 부분 반영
- **현재 코드**:
  ```python
  gate_issues = _quality_gate(content)
  if gate_issues:
      logger.warning(f"[품질 게이트] '{title}' 발행 경고: {gate_issues}")
  # 발행은 그대로 진행됨
  ```
- **잔존 문제**:
  1. 품질 기준 미달 시 **발행이 차단되지 않음** — 경고 로그만 남김
  2. Post2(종목픽) 게시글의 단기/중기 체크: Post2는 다른 포맷을 사용해 오탐 가능
  3. 리스크 섹션 체크가 이중 조건(`"⚠" not in content and "리스크" not in content`)이어서 "리스크" 단어가 본문에 한 번만 있어도 통과
- **수정 방향**:
  ```python
  gate_issues = _quality_gate(content, post_type="post1")  # post_type 파라미터 추가
  if gate_issues:
      logger.warning(...)
      # 선택지: 발행 차단 + 예외 발생 OR 관리자 알림 후 Draft로 강제 전환
  ```
- **후속 이슈 제목**: `fix(pipeline): 품질 게이트 하드 블록 + Post1/Post2 분리 적용`

---

### 🔵 신규 발견 이슈

#### 이슈 #8: HSD-7 분석 — 코드 수정 미착수

- **참조**: `docs/ANALYSIS-HSD-7.md` (2026-04-08 작성)
- **내용**: [해석]/[전망] 태그가 Gemini Reviser/품질 게이트에 의해 재주입되는 근본 원인 분석 완료
- **현황**: 분석 문서만 존재, 코드 수정 이슈(HSD-7-fix)가 생성되지 않음
- **수정이 필요한 위치** (HSD-7 분석 기준):
  - `GEMINI_REVISER_SYSTEM` 5745, 5751, 5754, 5758행 — 태그 추가 지시 삭제
  - 품질 게이트 #6 7941~7942행 — 자연어 표지 패턴으로 교체
  - GPT Writer 자기검수 5424행 — `[전망] 태그 추가` 지시 삭제
  - 발행 직전 태그 일괄 제거 함수 추가
- **후속 이슈 제목**: `fix(pipeline): [해석]/[전망] 태그 재주입 차단 — HSD-7 분석 기반 코드 수정`

---

#### 이슈 #9: HSD-8 분석 — 코드 수정 미착수

- **참조**: `docs/ANALYSIS-HSD-8.md` (2026-04-08 작성)
- **내용**: 참고출처 날짜·출처 분리 버그의 근본 원인 분석 완료 (`_format_source_section._rebuild()`)
- **현황**: 분석 문서만 존재, 코드 수정 이슈(HSD-8-fix)가 생성되지 않음
- **수정이 필요한 위치** (HSD-8 분석 기준):
  - `generator.py` 4761행: `re.sub(r"<[^>]+>", " ", ...)` → 블록 태그를 개행으로 먼저 치환
  - `generator.py` 4762행: `re.split(r"[\n,·•]+", raw)` → 쉼표 구분자 제거
  - Post1/Post2 프롬프트(5414, 5580행): 참고출처 `<li>` 포맷 명시 추가
- **후속 이슈 제목**: `fix(pipeline): 참고출처 날짜·출처 분리 버그 수정 — HSD-8 분석 기반`

---

## 3. 개선 제안 (미반영 게시글 퀄리티 항목)

HSD-5의 게시글 퀄리티 제안 #A~#H 중 #F만 (부분) 반영됐고 나머지 7건은 미반영이다.
우선순위가 높은 2건을 재확인한다.

### 제안 A — 출처 신뢰도 티어 시스템 (재확인)
- HSD-5 제안 그대로 유효
- `sources.json`에 `trust_tier` 필드 추가 → Gemini 분석 프롬프트에서 Tier A/B 우선
- **후속 이슈 제목**: `feat(pipeline): 뉴스 소스 신뢰도 티어 시스템 구현`

### 제안 B — Post2 재무 수치 자동 검증 레이어 (재확인)
- HSD-5 제안 그대로 유효
- yfinance/pykrx 실제 수치와 GPT 생성 수치 비교 → 오차 > 10% 시 재작성
- **후속 이슈 제목**: `feat(pipeline): Post2 재무 수치 자동 검증 레이어 추가`

---

## 4. 우선순위 요약

| 우선순위 | 이슈 번호 | 분류 | 제목 | 긴급도 |
|---------|----------|------|------|-------|
| P0 | #1 | 보안 | config.py 시크릿 — model_validator 무조건 검증으로 전환 | 🔴 즉시 |
| P0 | #8 | 버그 | [해석]/[전망] 태그 재주입 차단 (HSD-7 fix) | 🔴 즉시 |
| P0 | #9 | 버그 | 참고출처 날짜·출처 분리 버그 수정 (HSD-8 fix) | 🔴 즉시 |
| P1 | #3 | 품질 | 광역 Exception에 logger.error 추가 (pipeline.py 우선) | 🟠 이번 스프린트 |
| P1 | #4 | 보안 | _apply_ctx_to_env 우선순위 재검토 — M2 이전 해결 검토 | 🟠 이번 스프린트 |
| P1 | #7 | 품질 | 품질 게이트 하드 블록 + Post1/Post2 분리 적용 | 🟠 이번 스프린트 |
| P2 | #2 | 품질 | generator.py 모듈 분리 | 🟡 다음 스프린트 |
| P2 | #5 | 품질 | 비용 요금표 cost_rates.json 분리 | 🟡 다음 스프린트 |
| P2 | #6 | 품질 | publish_history.json → DB 전환 (M2 작업 시) | 🟡 M2 |
| 게시글 | #A, #B | 퀄리티 | 출처 신뢰도 티어, 재무 수치 자동 검증 | 🟡 다음 스프린트 |

---

## 5. 즉시 착수 권장 작업

1. **이슈 #8 (HSD-7 fix)**: `[해석]/[전망]` 태그가 현재도 발행 게시글에 노출되는 상태 — 운영 품질 직결
2. **이슈 #9 (HSD-8 fix)**: 참고출처 분리 버그가 최신 게시글 2~4개에 영향 — 독자 신뢰도 직결
3. **이슈 #1 (config.py 강화)**: 코드 2~3줄 수정으로 해결 가능한 보안 리스크

---

*이 문서는 HSD-5 반영 점검 결과이며, 이슈 #8, #9는 별도 HSD 이슈로 생성해 처리한다.*
