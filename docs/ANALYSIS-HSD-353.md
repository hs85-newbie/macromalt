# ANALYSIS-HSD-353 — macromalt 전체 점검 및 고도화 방안

> 작성일: 2026-04-15
> 이슈: HSD-353
> 범위: 파이프라인(Phase 1~23) + Phase 24 백엔드/프론트엔드 전체 점검
> 목적: 현재 구현 상태 진단, 품질/보안 이슈 식별, 우선순위 기반 후속 작업 정의

---

## 1. 현황 요약

### 1-1. 프로젝트 성격

macromalt은 **뉴스 수집 → AI 콘텐츠 생성 → WordPress 자동 발행**을 수행하는 매크로 분석 자동화 파이프라인이다. Phase 1~23(파이프라인)이 2년 이상 운영되며 안정화되었고, Phase 24에서 **멀티유저 SaaS 전환**(FastAPI 백엔드 + 결제 + 대시보드)이 진행 중이다.

**주요 스택**:
- 파이프라인: Python 3.9+, OpenAI GPT-4o, Gemini 2.5 Flash, BeautifulSoup, tenacity
- 백엔드(Phase 24): FastAPI, SQLAlchemy async, JWT, AES-256-GCM
- 저장소: SQLite(로컬) / PostgreSQL(Railway)
- 프론트엔드: Vanilla JS + TailwindCSS CDN
- 배포: Railway (Nixpacks)
- CI/CD: GitHub Actions + Claude Code 자동화

### 1-2. Phase 진행 갭 분석

| Phase | CLAUDE.md 예정 | 실제 상태 | 진행률 | 평가 |
|-------|---------------|----------|--------|------|
| 1~23 | ✅ 완료 | ✅ 완료 | 100% | 안정 운영 |
| 24-M0 설계 | 🔄 진행 중 | ✅ 완료 | 100% | 예상 초과 달성 |
| 24-M1 백엔드 | ⏳ 대기 | 🔄 진행 중 | ~70% | 예상보다 앞서감 |
| 24-M2 파이프라인 ctx 전환 | ⏳ 대기 | ❌ 미시작 | 0% | **갭 확대 주의** |
| 24-M3 결제 | ⏳ 대기 | 🟡 부분 | ~40% | 라이브 전환 전 감사 필요 |
| 24-M4 프론트엔드 | ⏳ 대기 | 🟡 설계만 | ~20% | 대시보드 UI 전무 |

### 1-3. 핵심 진단

| 분류 | 건강도 | 요지 |
|------|--------|------|
| 파이프라인 안정성 | 🟢 양호 | Phase 1~23 가동 중, 품질 게이트 #7 강화 완료 |
| 코드 품질(파이프라인) | 🔴 위험 | `generator.py` 8,107줄, `main.py:_run_pipeline_main` 248줄 — CLAUDE.md 규칙 극심 위반 |
| 테스트 커버리지 | 🔴 위험 | 파이프라인 0%, API ~27% — 회귀 버그 감지 불가 |
| API 보안 | 🟡 주의 | JWT/AES 기본 잘 구현, 단 CORS 와일드카드·복호화 무음 실패 등 잔여 |
| 설계 문서(M0) | 🟢 양호 | schema.sql / openapi.yaml / user_context.py 완료 |
| CI/CD | 🟢 양호 | 일일 발행 cron 4슬롯 + gitleaks pre-commit 적용 |
| 멀티유저 전환(M2) | 🔴 미시작 | `os.environ` 의존 파이프라인이 ctx 구조로 미전환 |

---

## 2. 상세 분석

### 2-1. 디렉토리/모듈별 현황

```
macromalt/
├── main.py              499줄   파이프라인 오케스트레이터
├── generator.py       8,107줄   ⚠️ AI 콘텐츠 생성 (모놀리식)
├── scraper.py         2,054줄   뉴스/리서치 수집
├── publisher.py         335줄   WordPress 발행
├── cost_tracker.py      389줄   비용 추적
├── api/                         FastAPI 백엔드 (M1 70%)
│   ├── main.py                  앱 진입점 + CORS
│   ├── core/                    config, database, security, deps
│   ├── models/                  SQLAlchemy 모델 7개
│   ├── schemas/                 Pydantic v2 스키마
│   ├── routers/                 auth / users / settings / pipeline / payments
│   └── tests/                   conftest + test_auth/settings/payments
├── web/                         프론트엔드 (M4 20%)
│   ├── index.html               랜딩 페이지 (완성)
│   └── app/                     login, dashboard (미완성)
├── design/                      M0 설계 (완료)
│   ├── schema.sql               7 테이블
│   ├── openapi.yaml             OpenAPI 3.0 계약서
│   └── user_context.py          UserContext 데이터클래스
├── docs/                        19MB 운영 문서
└── .github/workflows/           publish / claude / claude-dispatch / claude-code-review / phase20-weekly
```

### 2-2. 파이프라인 모듈 품질

#### generator.py — 8,107줄 (CLAUDE.md 300줄 규칙 27배 초과)

| 지표 | 값 | 평가 |
|------|-----|------|
| 파일 크기 | 392 KB / 8,107줄 | 🔴 모놀리식 |
| 함수 개수 | 약 95개 | 🔴 과다 |
| 장함수 샘플 | `_enforce_tense_correction` ~140줄 (`generator.py:2497~`), `_enforce_interpretation_rewrite` ~204줄 (`generator.py:3817~`), `verify_draft` ~137줄 (`generator.py:6752~`) | 🔴 30줄 규칙 위반 |
| 단위 테스트 | 0건 | 🔴 회귀 보호 없음 |
| 에러 처리 | `_parse_json_response` 실패 시 `None` 반환만 (`generator.py:4127~`) | 🟡 로그 없음 |

**근본 원인**: Phase 5~23 누적 패치(품질 게이트, 후처리 규칙, 시제 교정)가 한 파일에 축적. 테스트가 없어 분리 리팩토링이 지연됨(악순환).

#### main.py — 499줄, 핵심 함수 장함수

| 함수 | 라인 범위 | 길이 | 상태 |
|------|----------|------|------|
| `_apply_ctx_to_env` | `main.py:39~72` | 34줄 | 🟡 30줄 소폭 초과 |
| `detect_slot` | `main.py:87~139` | 52줄 | 🟡 DST 분기 혼재 |
| `_run_pipeline_main` | `main.py:245~493` | **248줄** | 🔴 30줄 규칙 **8배** 초과 |

`_run_pipeline_main`은 step_* 함수를 호출하지만 조건부 분기·try/except·로그·상태 기록이 혼재되어 제어 흐름 파악이 어렵다.

#### scraper.py — 2,054줄

- 함수 단위 평균 30~50줄로 **양호**. `tenacity` 재시도·타임아웃 설정 완비.
- 단, 단위 테스트 0건. 소스 추가 시 회귀 감지 불가.
- `fetch_hankyung_consensus()` 등 외부 사이트 로그인 자격증명 경로가 컨텍스트 객체 대신 환경변수에 의존.

#### publisher.py — 335줄 / cost_tracker.py — 389줄

- 둘 다 책임이 명확히 분리되어 있고 함수 크기 적정. 다만 **테스트 0건**.

### 2-3. api/ 백엔드 구현도 (M1 ~70%)

| 파일 | 구현 상태 | 비고 |
|------|----------|------|
| `api/main.py` | ✅ | 앱 초기화, CORS, 라우터 등록, `/health` |
| `api/core/config.py` | ✅ | Pydantic BaseSettings + 프로덕션 검증 |
| `api/core/security.py` | ✅ | JWT(HS256), bcrypt, AES-256-GCM |
| `api/core/database.py` | ✅ | async 엔진, SQLite/PG 자동 감지 |
| `api/core/deps.py` | ✅ | `get_current_user` OAuth2 Bearer |
| `api/models/models.py` | ✅ | User, Subscription, UserApiKey, UserWpSettings, UserPipelineSettings, RunLog, PublishedPost |
| `api/schemas/schemas.py` | ✅ | Pydantic v2 |
| `api/routers/auth.py` | ✅ | register / login / refresh |
| `api/routers/users.py` | 🟡 | `GET /me` 만 있음 — PATCH/DELETE 미구현 |
| `api/routers/settings.py` | ✅ | API 키 / WP / 파이프라인 설정 CRUD |
| `api/routers/pipeline.py` | ✅ | execute(BackgroundTask) / runs / posts |
| `api/routers/payments.py` | 🟡 | Toss ready / confirm / billing — 실패 재시도·환불 없음 |
| `api/tests/test_auth.py` | ✅ | 5케이스 |
| `api/tests/test_settings.py` | ✅ | API 키·WP 설정 |
| `api/tests/test_payments.py` | ✅ | 결제 시나리오 |

**미구현 핵심**:
- 스케줄러(정기 cron) — 현재 `BackgroundTasks`만 있음
- 사용자 프로필 수정/탈퇴 (`users.py` PATCH/DELETE)
- 플랜별 레이트 제한
- 암호화 키 로테이션
- 결제 실패/환불 흐름

### 2-4. web/ 프론트엔드 (M4 ~20%)

| 파일 | 상태 | 비고 |
|------|------|------|
| `web/index.html` | ✅ | 랜딩(히어로·기능·요금·CTA) 완성 |
| `web/app/login.html` | 🟡 | 마크업만, JS 이벤트 핸들러 미연결 |
| `web/app/dashboard.html` | ❌ | 파이프라인 컨트롤/설정 폼/실행 이력 UI 전무 |
| `web/assets/api.js` | 🟡 | 클라이언트 스텁, 401 자동 refresh 미구현 |

### 2-5. 설계/문서 (M0 완료)

- `design/schema.sql` — 7 테이블, 외래키·유니크·인덱스 완비
- `design/openapi.yaml` — 전체 엔드포인트 계약서(OpenAPI 3.0)
- `design/user_context.py` — UserContext dataclass + `from_env()` 하위 호환 + `validate()`
- `docs/` 19MB — 정책(`10_policies/`), 보고서(`88_etc/REPORT/`), 인수인계 문서

### 2-6. CI/CD 현황

| 워크플로우 | 역할 | 상태 |
|----------|------|------|
| `.github/workflows/publish.yml` | 일일 발행 cron 4슬롯(morning/evening/us_open DST/non-DST), artifact 14일 보관 | ✅ |
| `.github/workflows/claude.yml` | `@claude` 멘션 트리거, OAuth 인증 | ✅ |
| `.github/workflows/claude-dispatch.yml` | 복잡한 자동화 dispatch | ✅ |
| `.github/workflows/claude-code-review.yml` | PR 리뷰 자동화 | ✅ |
| `.github/workflows/phase20-weekly.yml` | 주간 리포트 | ✅ |
| `.pre-commit-config.yaml` | gitleaks 시크릿 스캔 | ✅ (HSD-344에서 추가) |

**갭**: pytest 실행을 CI에서 강제화하지 않음. 테스트 실패가 merge를 막지 못함.

### 2-7. 코드 품질 이슈 요약 (CLAUDE.md 규칙 기준)

| 규칙 | 기준 | 위반 위치 | 배수 |
|------|------|---------|------|
| 파일 최대 300줄 | 300 | `generator.py` 8,107줄 | 27배 |
| 파일 최대 300줄 | 300 | `scraper.py` 2,054줄 | 6.8배 |
| 함수 최대 30줄 | 30 | `main.py:245 _run_pipeline_main` 248줄 | 8.3배 |
| 함수 최대 30줄 | 30 | `generator.py:3817 _enforce_interpretation_rewrite` ~204줄 | 6.8배 |
| 함수 최대 30줄 | 30 | `generator.py:2497 _enforce_tense_correction` ~140줄 | 4.7배 |
| 함수 최대 30줄 | 30 | `generator.py:6752 verify_draft` ~137줄 | 4.6배 |
| 함수 최대 30줄 | 30 | `main.py:87 detect_slot` 52줄 | 1.7배 |
| 커버리지 80% 미만 금지 | 80% | 파이프라인 0% / API ~27% | 전반 위반 |

### 2-8. 보안 이슈

| # | 심각도 | 위치 | 내용 |
|---|--------|------|------|
| S1 | 🔴 High | `api/core/config.py:4~9` | `JWT_SECRET_KEY`, `AES_SECRET_KEY`, `TOSS_SECRET_KEY` 개발 기본값 하드코딩. 프로덕션 검증(`config.py:33~38`)은 존재하지만 기본값 노출 자체가 실수 가능성을 높임 |
| S2 | 🟡 Med | `api/main.py:13~19` | CORS `allow_methods=["*"]`, `allow_headers=["*"]` — 필요한 것만 지정 권장 |
| S3 | 🟡 Med | `api/routers/pipeline.py:39~42` | API 키 복호화 실패 시 `except Exception: keys[...] = None` 무음 실패 — 로그/사용자 알림 없음 |
| S4 | 🟡 Med | `api/routers/pipeline.py:54~58` | WP 비밀번호 복호화도 동일한 무음 실패 패턴 |
| S5 | 🟡 Med | `api/routers/payments.py` | Toss 콜백 메시지 서명 검증 없음 (CSRF 토큰도 없음) |
| S6 | 🟡 Med | JWT refresh_token 만료 30일 | 권장 7~14일 대비 길다. 토큰 블랙리스트 없음(로그아웃 실질 불가) |
| S7 | 🟢 Low | `main.py:39~72 _apply_ctx_to_env` | ctx 값을 `os.environ`에 주입 — 메모리 노출. M2에서 ctx 직접 전달로 제거 예정 |

### 2-9. 에러 처리 품질

- `generator.py:4127 _parse_json_response` — JSON 파싱 실패 시 `None` 반환만, 원인 로그 없음
- `generator.py:6752 verify_draft` — 검증 실패 후 폴백이 조용함(어떤 게이트에서 실패했는지 불명확)
- `scraper.py:1169 run_dart_disclosure_scan` — API 실패 시 로깅만, 상위 전파 없음
- 파이프라인 레이어 전반에서 **빈 catch / 무음 fallback 패턴**이 품질 게이트 판단을 방해

### 2-10. 최근 커밋 경향 (최근 10개)

1. `3d71856` Merge #28 chore/pre-commit-hook
2. `0b01705` perf: max_turns 30→45 (HSD-344)
3. `7d98f98` chore(infra): gitleaks pre-commit hook
4. `4ae72bc` Merge #27 HSD-344
5. `d4599b2` feat: 품질 게이트 #7 출처 개수 검사 강화
6. `94d2491` Merge #26 HSD-348
7. `7454e26` refactor: Phase 15D/15E/15F 후처리 함수 정리
8. `79ec3bc` Merge #25 HSD-352
9. `b073eff` docs: HSD-323 수정 후 운영 정책 문서 업데이트
10. `50eb898` Merge #24 HSD-347

**경향**: 최근 활동은 `generator.py` 품질 게이트 강화와 infra(pre-commit)에 집중. **리팩토링 시도 없음**. Phase 24 M1 작업은 진행되고 있으나 M2 착수 신호 없음.

### 2-11. 강점과 약점 요약

**강점**
- Phase 1~23 파이프라인 2년+ 안정 운영
- M0 설계(schema.sql/openapi.yaml/user_context.py) 완결성 높음
- API 보안 기초(JWT, AES-256-GCM, bcrypt, 프로덕션 값 검증) 합리적
- CI 자동화와 gitleaks 보안 훅 확보

**약점**
- `generator.py` 기술 부채 — 27배 크기 초과, 테스트 0건
- 파이프라인 전체 테스트 커버리지 0% → 회귀 감지 불가
- 멀티유저 전환(M2) 0% — 배포 gating 요소
- 결제 라이브 전환 전 감사 필요(M3)
- 프론트 대시보드 부재(M4)

---

## 3. 후속 작업 목록

## 후속 작업 목록

### P0 — Critical

- [ ] **[품질] pytest CI 강제화 및 커버리지 게이트 도입**
  - 파일: `.github/workflows/publish.yml`, `api/pytest.ini`, `.github/workflows/` (신규 test.yml 검토)
  - 설명: 현재 테스트 실패가 merge를 막지 못한다. PR 트리거 워크플로우를 추가해 `api/` 디렉토리에서 `pytest --cov=api --cov-fail-under=60` 실행, 실패 시 머지 차단. 파이프라인(`generator.py`, `scraper.py`, `main.py`)도 최소 smoke test를 도입해 import/기본 분기 회귀만이라도 감지.

- [ ] **[보안] API 키·WP 비밀번호 복호화 무음 실패 제거**
  - 파일: `api/routers/pipeline.py` (라인 39~42, 54~58)
  - 설명: `except Exception: value = None`은 무엇이 실패했는지 기록하지 않는다. `logger.error`로 원인 로깅 + 사용자 응답 `HTTPException(500, "복호화 실패: 관리자에게 문의")`로 명확히 전파. 암호화 키 rotation 장애·손상된 레코드를 즉시 감지할 수 있게 한다.

- [ ] **[보안] CORS allow_methods / allow_headers 화이트리스트화**
  - 파일: `api/main.py` (라인 13~19)
  - 설명: 현재 `allow_methods=["*"]`, `allow_headers=["*"]`. `["GET","POST","PUT","DELETE","OPTIONS"]`와 `["Content-Type","Authorization"]`로 축소. 프리플라이트 응답 최소화로 공격 표면 감소.

- [ ] **[보안] 개발용 기본 시크릿 제거 및 필수화**
  - 파일: `api/core/config.py` (라인 4~9)
  - 설명: `JWT_SECRET_KEY`, `AES_SECRET_KEY`, `TOSS_SECRET_KEY` 기본값을 Pydantic `Field(...)` 필수 항목으로 변경. 로컬 개발은 `.env.example`에 지침을 명시. 현재 프로덕션 검증(라인 33~38)이 있지만 실수로 dev 기본값이 프로덕션에 복사되는 위험을 원천 차단.

- [ ] **[아키텍처] main.py `_run_pipeline_main()` 248줄 → step orchestrator로 분할**
  - 파일: `main.py` (라인 245~493)
  - 설명: CLAUDE.md 30줄 규칙을 8배 초과한다. 기존 `step_*` 함수를 리스트로 선언하고 순차 실행하는 orchestrator 루프로 교체. 각 step의 성공/실패 상태를 `run_log`에 기록. 리팩토링 전에 최소 end-to-end smoke test 1건 먼저 추가(회귀 방지).

### P1 — High

- [ ] **[아키텍처] generator.py 8,107줄 모듈 분할 계획 수립**
  - 파일: `generator.py` (전체), 신규 `generator/` 패키지 구조 설계
  - 설명: 즉시 리팩토링은 위험하므로 **1단계로 분할 계획 문서**(`docs/40_design/GENERATOR_REFACTOR_PLAN.md`) 작성. 제안 구조 예: `generator/tense.py`(시제 교정), `generator/interpretation.py`(해석 재작성), `generator/verification.py`(검증), `generator/gemini_analysis.py`, `generator/gpt_write.py`. 각 장함수(`_enforce_tense_correction` 140줄 @ 2497, `_enforce_interpretation_rewrite` 204줄 @ 3817, `verify_draft` 137줄 @ 6752)를 30줄 이하로 분해하는 세부 작업 태스크 나열.

- [ ] **[테스트] generator.py 핵심 유틸 함수 pytest 추가**
  - 파일: `generator.py`, 신규 `tests/test_generator_utils.py`
  - 설명: 리팩토링 전에 **behavior lock-in**을 위해 순수 함수(JSON 파서, 스코어링, 품질 게이트 단독 함수)부터 테스트 작성. 최소 10케이스. `_parse_json_response`, `_score_post_quality`, `_check_temporal_sanity` 등.

- [ ] **[M2] 파이프라인 UserContext 기반 멀티유저 전환 착수**
  - 파일: `main.py`, `generator.py`, `scraper.py`, `publisher.py`, `design/user_context.py`
  - 설명: `os.getenv("OPENAI_API_KEY")` 등 환경변수 접근을 `ctx.openai_api_key`로 교체. 기존 `__main__` 단독 실행 모드는 `UserContext.from_env()`로 하위 호환 유지(CLAUDE.md §7 규정 준수). Phase 24 M2 시작점. 각 파일별로 개별 PR 분리 권장.

- [ ] **[보안] 결제 콜백 서명 검증 및 재현공격 방지**
  - 파일: `api/routers/payments.py`
  - 설명: Toss `confirm`/`billing` 엔드포인트에 Toss 측 요청 서명(또는 idempotency key) 검증 로직 추가. 현재 결제 콜백은 인증 토큰에만 의존하므로, 동일 결제 키 재전송(replay) 및 악의적 금액 위조 위험이 있다. 테스트 모드 → 라이브 전환 **전 필수**.

- [ ] **[M1] 사용자 프로필 수정/탈퇴 엔드포인트 완성**
  - 파일: `api/routers/users.py` (현재 `GET /me` 35줄만 존재)
  - 설명: `PATCH /api/users/me`(비밀번호 변경, 이메일 변경), `DELETE /api/users/me`(탈퇴 + cascade). 탈퇴 시 `user_api_keys`, `user_wp_settings` 등 민감 레코드 완전 삭제 보장. `design/openapi.yaml`과 동기화.

- [ ] **[테스트] api/routers/pipeline.py, users.py 통합 테스트 추가**
  - 파일: `api/tests/test_pipeline.py`(신규), `api/tests/test_users.py`(신규)
  - 설명: 현재 테스트는 auth / settings / payments만 커버(커버리지 약 27%). pipeline 실행 흐름(BackgroundTask mock), 실행 이력 조회, 권한 분리 검증. 커버리지 60% 이상 목표.

- [ ] **[보안] JWT refresh_token 만료 단축 및 블랙리스트**
  - 파일: `api/core/config.py`, `api/core/security.py`, `api/routers/auth.py`
  - 설명: 30일 → 14일로 단축. `POST /api/auth/logout` 엔드포인트 신규 추가(블랙리스트 테이블 또는 Redis). 현재는 로그아웃 시 토큰이 여전히 유효해 탈취 시 완화 수단이 없다.

- [ ] **[에러 처리] generator.py 무음 fallback 패턴 제거**
  - 파일: `generator.py` (라인 4127 `_parse_json_response`, 라인 6752 `verify_draft` 등)
  - 설명: `except Exception: return None` 대신 구체 예외 정의(`ParseError`, `ValidationError`) + `logger.error(..., exc_info=True)` + 상위 전파. 품질 게이트 디버깅 시간을 단축한다.

### P2 — Medium

- [ ] **[M4] 프론트엔드 대시보드 MVP 구현**
  - 파일: `web/app/dashboard.html`, `web/assets/api.js`
  - 설명: 파이프라인 실행 버튼, API 키/WP 설정 폼, 최근 실행 이력 테이블. `assets/api.js`에 401 응답 감지 → refresh_token 재발급 → 실패 시 login 리다이렉트 플로우 구현(CLAUDE.md §8 규정).

- [ ] **[M3] 정기 청구/실패 재시도/환불 플로우**
  - 파일: `api/routers/payments.py`, 신규 `api/services/billing_scheduler.py`
  - 설명: 월 정기 청구 cron, 결제 실패 시 3회 지수 백오프 재시도, 환불 엔드포인트, 플랜 다운그레이드 로직. 사용자 메일 알림(결제 성공/실패/만료 임박).

- [ ] **[품질] scraper.py 소스별 단위 테스트**
  - 파일: `scraper.py`, 신규 `tests/test_scraper_sources.py`
  - 설명: `fetch_rss`, `fetch_web`, `run_dart_disclosure_scan`, `fetch_hankyung_consensus` 각 소스에 mock HTTP 응답 기반 테스트. 소스 사이트 구조 변경 시 조기 감지.

- [ ] **[보안] 파이프라인 실행 중 os.environ 주입 제거**
  - 파일: `main.py` (라인 39~72 `_apply_ctx_to_env`)
  - 설명: M2 리팩토링과 함께 진행. `os.environ` 전역 오염 제거 → UserContext를 모든 함수에 직접 전달. 동시 실행 시 키 충돌 위험 제거.

- [ ] **[품질] main.py detect_slot() 단순화**
  - 파일: `main.py` (라인 87~139)
  - 설명: 52줄 함수. DST 판정과 슬롯 매핑을 분리(`_is_dst()`, `_slot_from_hour()`). 테스트 가능성 향상.

- [ ] **[문서] M2 착수 전 UserContext 이행 가이드 작성**
  - 파일: `docs/40_design/M2_MIGRATION_GUIDE.md` (신규)
  - 설명: 기존 환경변수 키 → ctx 필드 매핑 표, 하위 호환 유지 전략, step-by-step 체크리스트. M2 착수 시 일관성을 담보한다.

- [ ] **[인프라] CI 테스트 워크플로우 신규**
  - 파일: `.github/workflows/test.yml` (신규)
  - 설명: PR 트리거, Python matrix, `cd api && pytest --cov=api --cov-report=xml`. P0 게이트와 연동.

- [ ] **[품질] 빈 catch 및 바로 pass 패턴 일괄 검토**
  - 파일: `generator.py`, `scraper.py`, `api/routers/*.py`
  - 설명: `except Exception: pass` 또는 `return None` 패턴을 grep으로 찾아 로그 추가/상위 전파로 교정. CLAUDE.md 전역 규칙 "빈 catch 블록 금지" 준수.

- [ ] **[품질] pathlib 경로 표준화**
  - 파일: `cost_tracker.py`, `main.py`, 기타 파일 경로 하드코딩 지점
  - 설명: `os.path.dirname(__file__)`와 절대 경로 문자열 혼재. `pathlib.Path` + `PROJECT_ROOT` 상수로 일관화. Railway와 로컬 환경 경로 차이로 인한 잠재 버그 방지.

- [ ] **[문서] CLAUDE.md Phase 진행 현황 업데이트**
  - 파일: `CLAUDE.md` (라인 247~256 Phase 표)
  - 설명: 현재 표는 "M0 진행 중, M1 대기"로 되어 있으나 실제로는 M0 완료·M1 70%·M2 미시작. 실제 진행률과 동기화하여 서브에이전트가 잘못된 전제로 작업 시작하는 것을 방지.

---

**문서 끝**. 본 분석은 코드 수정 없이 현황 진단만 수행했다. P0 항목은 착수 전 별도 승인 권장.
