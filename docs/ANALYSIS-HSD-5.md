# ANALYSIS-HSD-5: 프로젝트 전체 점검 및 게시글 퀄리티 고도화 제안

- **이슈 ID**: HSD-5
- **작성일**: 2026-04-08
- **분석 범위**: 프로젝트 전체 (Phase 1~24)
- **분석 관점**: 코드 품질 + 보안 + 게시글 퀄리티 상승

---

## 1. 현황 요약

### 1.1 프로젝트 개요

macromalt는 **한국 개인투자자 대상 AI 기반 금융 블로그 자동화 플랫폼**이다.  
3단계 교차검증(Gemini 분석 → GPT 작성 → Gemini 팩트체크) 파이프라인으로  
1회 실행에 Post1(심층분석) 최대 10개 + Post2(종목픽) 최대 3개를 자동 생성·발행한다.

### 1.2 핵심 파일 규모

| 파일 | 줄 수 | 상태 |
|------|------:|------|
| `generator.py` | 8,104 | ⚠ 과대 — 분리 필요 |
| `scraper.py` | 2,067 | ⚠ 과대 |
| `main.py` | 499 | 양호 |
| `publisher.py` | 306 | 양호 |

### 1.3 Phase 진행 현황

| Phase | 상태 | 내용 |
|-------|------|------|
| 1~23 | ✅ 완료 | 파이프라인 자동화 |
| 24-M0 | ✅ 완료 | 설계 문서 (schema.sql, openapi.yaml, user_context.py) |
| 24-M1 | 🔄 진행 중 | FastAPI 백엔드 (auth, users, settings, pipeline, payments) |
| 24-M2 | ⏳ 대기 | 파이프라인 멀티유저 전환 |
| 24-M3 | ⏳ 대기 | Toss 결제 연동 |
| 24-M4 | ⏳ 대기 | 프론트엔드 대시보드 |

---

## 2. 발견 이슈 목록

### 🔴 P0 — 보안 (즉시 수정)

#### 이슈 #1: API 설정 하드코딩된 시크릿

- **파일**: `api/core/config.py` (라인 6, 10, 12-13)
- **내용**:
  ```python
  JWT_SECRET_KEY = "dev-secret-change-in-production"
  AES_SECRET_KEY = "dev-aes-key-32bytes-change-prod!"
  TOSS_SECRET_KEY = "test_sk_placeholder"
  TOSS_CLIENT_KEY = "test_ck_placeholder"
  ```
- **위험**: 개발용 기본값이 프로덕션에 그대로 배포될 경우 JWT 위변조 및 AES 복호화 가능
- **수정 방향**: `default=None`으로 변경 + 누락 시 명시적 `ValueError` 발생

---

#### 이슈 #2: CORS wildcard 허용

- **파일**: `api/main.py` (라인 12-18)
- **내용**: `allow_origins=["*"]` — 모든 출처에서 API 호출 허용
- **위험**: CSRF/XSS 공격 가능성
- **수정 방향**: 프로덕션 도메인을 `settings.ALLOWED_ORIGINS` 환경변수로 관리

---

#### 이슈 #3: 결제 API 오류 응답 그대로 노출

- **파일**: `api/routers/payments.py` (라인 87-91, 130-134)
- **내용**: Toss 결제 API 실패 시 `resp.text` 원문을 클라이언트에 반환
- **위험**: 내부 API 오류 메시지 및 민감 정보 노출 가능
- **수정 방향**: 사용자 노출 메시지와 내부 로그 분리

---

### 🟠 P1 — 코드 품질 (이번 스프린트 내 수정)

#### 이슈 #4: generator.py 과대 파일 (8,104줄)

- **파일**: `generator.py`
- **내용**: 단일 파일에 81개 함수 포함. 테마 선정, 분석 생성, 팩트체크, 반복 완화, 이력 관리가 혼재
- **영향**: 수정 범위 파악 어려움, 테스트 격리 불가, LLM 컨텍스트 초과로 읽기 제한 발생
- **수정 방향**:
  ```
  generator/
  ├── __init__.py         (공개 API 재수출)
  ├── themes.py           (gemini_select_themes, _build_history_context)
  ├── post1.py            (generate_deep_analysis)
  ├── post2.py            (generate_stock_picks_report)
  ├── verifier.py         (Gemini 팩트체크 로직)
  ├── dedup.py            (fingerprint + 반복 완화 엔진)
  └── history.py          (publish_history 저장/로드)
  ```

---

#### 이슈 #5: 빈/광역 Exception 처리 다수

- **파일**: `generator.py` (라인 518, 1210), `macro_data.py` (라인 144, 222), `api/routers/pipeline.py` (라인 41, 57), `scraper.py` (라인 401, 433)
- **내용**:
  ```python
  except Exception: pass        # generator.py
  except Exception: return None # macro_data.py
  except Exception: return True # scraper.py
  ```
- **영향**: 오류 발생 시 원인 추적 불가, 파이프라인이 잘못된 데이터로 계속 실행
- **수정 방향**: 구체적 예외 타입 명시 + `logger.error(exc_info=True)` 반드시 추가

---

#### 이슈 #6: 재시도 로직 부재 (외부 API 호출)

- **파일**: `publisher.py` (WordPress REST API), `macro_data.py` (BOK/FRED/KOSIS/IMF), `images.py` (Unsplash API)
- **내용**: 모든 외부 API 호출이 단일 시도(1-shot)로만 동작
- **영향**: 일시적 네트워크 장애 시 전체 파이프라인 중단
- **수정 방향**: `requirements.txt`에 이미 포함된 `tenacity` 라이브러리로 지수 백오프 재시도 적용
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
  def _call_wp_api(...): ...
  ```

---

#### 이슈 #7: 로거 설정 중복

- **파일**: `main.py` (라인 124-132), `scraper.py` (라인 45-53)
- **내용**: 두 파일에서 동일한 `logging.basicConfig()` 호출
- **영향**: 로그 핸들러 중복 등록 → 같은 로그가 2회 출력될 수 있음
- **수정 방향**: `main.py`에서만 `basicConfig` 호출, 나머지는 `getLogger("macromalt")` 사용

---

#### 이슈 #8: `_apply_ctx_to_env()` 패턴 — 환경변수 직접 오염

- **파일**: `main.py` (라인 42-66)
- **내용**: UserContext에서 받은 API 키를 `os.environ`에 직접 기록하는 함수
  ```python
  def _apply_ctx_to_env(ctx):
      os.environ["OPENAI_API_KEY"] = ctx.openai_api_key or ""
      ...
  ```
- **영향**: 멀티유저 환경에서 사용자 A의 키가 사용자 B에게 노출될 수 있음 (글로벌 상태 공유)
- **수정 방향**: `ctx`를 함수 파라미터로 직접 전달하는 방식으로 전환 (M2 작업 시 반드시 해결)

---

### 🟡 P2 — 개선 사항 (다음 스프린트)

#### 이슈 #9: 의존성 버전 범위 미고정

- **파일**: `requirements.txt`
- **내용**: `openai>=2.0.0`, `google-genai>=1.0.0`, `yfinance>=1.2.0` — 상한 없음
- **위험**: 메이저 버전 업그레이드 시 API 호환성 파손
- **수정 방향**: `openai>=2.0.0,<3.0.0` 형식으로 upper bound 명시

---

#### 이슈 #10: 비용 요금표 하드코딩

- **파일**: `cost_tracker.py` (라인 25-34)
- **내용**: GPT-4o, Gemini 요금이 코드에 직접 하드코딩
- **영향**: 요금 변동 시 코드 수정 필요, 오운영 비용 계산 오류 가능
- **수정 방향**: `cost_rates.json` 또는 `editorial_config.py` 내 별도 상수로 분리

---

#### 이슈 #11: api/routers/pipeline.py — BackgroundTask 오류 추적 불가

- **파일**: `api/routers/pipeline.py`
- **내용**: `BackgroundTask`로 실행되는 파이프라인 오류가 RunLog에 기록되지 않으면 사용자가 실패 원인 확인 불가
- **수정 방향**: try/except 블록에서 `RunLog.status = "failed"`, `RunLog.error_msg = str(e)` 업데이트 보장

---

#### 이슈 #12: publish_history.json — 경쟁 조건 위험

- **파일**: `generator.py` (save_publish_history 함수)
- **내용**: 멀티유저 환경에서 여러 사용자가 동시에 파이프라인을 실행하면 동일 파일에 동시 쓰기 발생
- **수정 방향**: DB(RunLog 테이블) 기반으로 이력 관리 전환 (M2 작업 시)

---

## 3. 게시글 퀄리티 상승 — 고도화 제안

### 3.1 현재 콘텐츠 파이프라인 강점

- **3단계 교차검증** (Gemini 분석 → GPT 작성 → Gemini 팩트체크): 단일 모델 대비 팩트 오류 감소
- **반복 완화 엔진** (theme/axes/ticker fingerprint): 동일 테마 반복 방지
- **슬롯 분기** (morning/evening/us_open): 시장 시간대별 적합한 각도 설정
- **편집 철학 코드화** (`editorial_config.py`): 조건부 확신형, 단기/중기 병기, 리스크 섹션 필수화

---

### 고도화 제안 #A — 출처 신뢰도 스코어링 시스템

- **현황**: 뉴스 `date_tier`(recent/extended/old)만 구분하며, 소스별 신뢰도 차등이 없음
- **문제**: 루머성 블로그와 공식 DART 공시가 동일한 가중치로 프롬프트에 주입됨
- **제안**:
  ```python
  # sources.json에 신뢰도 티어 추가
  {
    "name": "DART 전자공시",
    "trust_tier": "A",   # A: 공시/정부 | B: 주요 언론 | C: 전문 미디어 | D: 일반
    ...
  }
  ```
  Gemini 분석 프롬프트에서 Tier A/B 소스의 데이터에 더 높은 확신도 부여 지시
- **기대 효과**: 근거 품질 향상, "~에 따르면" 출처 표기의 신뢰성 상승
- **후속 이슈 제목**: `feat: 뉴스 소스 신뢰도 티어 시스템 구현`

---

### 고도화 제안 #B — 수치 자동 검증 레이어

- **현황**: Gemini 팩트체크가 텍스트 수준에서 이루어지며, 숫자 정확성 검증이 미흡함
- **문제**: GPT가 생성한 PER, ROE, 수익률 수치가 실제 yfinance/pykrx 데이터와 다를 수 있음
- **제안**:
  1. `generate_stock_picks_report()` 내에서 종목 ticker를 추출
  2. yfinance/pykrx로 실제 재무 지표 조회
  3. 생성된 글의 수치와 실제 수치를 비교하는 별도 검증 단계 추가
  4. 오차 > 10% 시 Gemini 재작성 요청 (현재 MAX_RETRIES=1 활용)
- **기대 효과**: 수치 오류로 인한 신뢰도 손상 방지
- **후속 이슈 제목**: `feat: Post2 재무 수치 자동 검증 레이어 추가`

---

### 고도화 제안 #C — Few-shot 예시 자동 업데이트 파이프라인

- **현황**: `data/few_shot/examples.json`이 정적 파일로 관리되며, 수동 업데이트 필요
- **문제**: 운영자가 수동으로 우수 글을 선정하지 않으면 예시가 점점 outdated
- **제안**:
  1. knowledge_base에 `quality_score` 컬럼 추가 (WordPress 조회수 연동)
  2. 주간 스케줄로 조회수 상위 N개 글을 few_shot/examples.json에 자동 반영
  3. `scripts/update_few_shot.py` 신규 작성
- **기대 효과**: 예시 글이 독자 반응 기반으로 자동 진화 → 글 방향성 품질 향상
- **후속 이슈 제목**: `feat: WordPress 조회수 기반 few-shot 예시 자동 업데이트`

---

### 고도화 제안 #D — SEO 메타 자동 최적화

- **현황**: `seo_title`은 GPT가 생성하지만, meta description, 키워드 밀도는 미관리
- **문제**: `docs/50_SEO/MACROMALT_SEO_MONETIZATION_SSOT_v1.md`에 schema.org Article 주입이 계획되어 있으나 미구현
- **제안**:
  1. GPT 작성 단계에 meta_description (120-160자), focus_keyword (1개) 필드 추가
  2. `publisher.py`에서 Yoast SEO REST API로 메타 자동 주입
  3. schema.org `Article` JSON-LD를 WordPress `<head>` 에 삽입 (functions.php 또는 플러그인)
- **기대 효과**: 구글 검색 CTR 향상, Rich Snippet 노출 기회 확보
- **후속 이슈 제목**: `feat: SEO 메타 자동 주입 (meta_description + schema.org Article)`

---

### 고도화 제안 #E — 콘텐츠 반복 감지 강화 (semantic similarity)

- **현황**: fingerprint 기반 반복 완화 엔진이 theme/axes/ticker 카테고리 수준에서만 작동
- **문제**: 테마가 달라도 결론 문장이 반복("~를 주시할 필요가 있다", "~에 주목해야 한다")되는 현상
- **제안**:
  1. knowledge_base에 핵심 결론 문장 임베딩 저장 (OpenAI text-embedding-3-small 활용)
  2. 신규 글 생성 전 cosine similarity 체크 (임계값 0.85 이상이면 경고)
  3. Gemini 분석 프롬프트에 "최근 N일 내 사용된 결론 패턴" 주입
- **기대 효과**: 문장 수준 반복 방지 → 독자 이탈률 감소
- **후속 이슈 제목**: `feat: 결론 문장 semantic similarity 기반 반복 방지`

---

### 고도화 제안 #F — 발행 전 품질 게이트 자동화

- **현황**: Gemini 팩트체크가 존재하지만, 최소 길이/구조 요건 검사가 없음
- **문제**: 간혹 길이 미달이거나 리스크 섹션이 누락된 채 Draft 발행됨
- **제안**:
  ```python
  # publisher.py 발행 전 검사
  def _quality_gate(post: dict) -> list[str]:
      issues = []
      if len(post["content"]) < 8000:
          issues.append("본문 8,000자 미달")
      if "⚠ 리스크 요인" not in post["content"]:
          issues.append("리스크 섹션 누락")
      if "단기(1~3개월)" not in post["content"]:
          issues.append("투자 시계 단기 미기재")
      if "중기(3~12개월)" not in post["content"]:
          issues.append("투자 시계 중기 미기재")
      return issues
  ```
  이슈 발생 시 Gemini 재작성 요청 또는 관리자 알림
- **기대 효과**: 구조적 품질 기준선 자동 보장
- **후속 이슈 제목**: `feat: 발행 전 콘텐츠 품질 게이트 구현`

---

### 고도화 제안 #G — 테마 다양성 모니터링 대시보드

- **현황**: 테마 선정 이력이 publish_history.json (최근 5건)에만 저장됨
- **문제**: 중장기적으로 어떤 섹터/테마가 과다 반복되고 있는지 파악 불가
- **제안**:
  1. RunLog + PublishedPost 테이블에서 주간/월간 theme 분포 집계 API 추가
  2. 관리자 대시보드(web/)에 "테마 다양성 히트맵" 위젯 추가
  3. 특정 섹터가 7일 내 편집 철학 비중(65/35)을 벗어나면 Slack/이메일 알림
- **기대 효과**: 편집 편향 조기 감지, 섹터 균형 유지
- **후속 이슈 제목**: `feat: 테마 다양성 모니터링 및 알림`

---

### 고도화 제안 #H — 한국어 가독성 최적화 (읽기 레벨 분석)

- **현황**: 글 품질 기준이 길이/구조에 집중되어 있으며, 독자 가독성 측정이 없음
- **문제**: 전문 용어 과밀 사용 시 타겟 독자(중급 개인투자자) 이탈 가능
- **제안**:
  1. 생성된 글에서 전문 용어 밀도 측정 (DART 재무 용어 사전 활용)
  2. 용어 밀도 > 임계값 시 GPT에 "괄호 설명 누락 용어 보완" 지시 추가
  3. Flesch-Kincaid 한국어 적용판(KFL Score) 또는 평균 문장 길이 측정
- **기대 효과**: editorial_config.py 전문 용어 괄호 병기 원칙 실질적 준수율 향상
- **후속 이슈 제목**: `feat: 한국어 가독성 분석 및 자동 보완 지시 추가`

---

## 4. 우선순위 요약

| 우선순위 | 이슈 번호 | 분류 | 제목 | 예상 공수 |
|---------|----------|------|------|---------|
| P0 | #1 | 보안 | API 설정 하드코딩된 시크릿 제거 | 0.5일 |
| P0 | #2 | 보안 | CORS wildcard → 도메인 명시 | 0.5일 |
| P0 | #3 | 보안 | 결제 API 오류 응답 노출 차단 | 0.5일 |
| P1 | #4 | 품질 | generator.py 모듈 분리 | 2일 |
| P1 | #5 | 품질 | 광역 Exception 처리 개선 | 1일 |
| P1 | #6 | 품질 | 외부 API 재시도 로직 (tenacity) | 1일 |
| P1 | #7 | 품질 | 로거 설정 중복 제거 | 0.5일 |
| P1 | #8 | 보안 | _apply_ctx_to_env 패턴 제거 | M2 작업 시 |
| P2 | #9 | 품질 | 의존성 버전 upper bound 추가 | 0.5일 |
| P2 | #10 | 품질 | 비용 요금표 분리 | 0.5일 |
| P2 | #11 | 품질 | BackgroundTask 오류 추적 | 1일 |
| P2 | #12 | 품질 | publish_history → DB 전환 | M2 작업 시 |
| 게시글 | #A | 퀄리티 | 출처 신뢰도 티어 시스템 | 1일 |
| 게시글 | #B | 퀄리티 | 재무 수치 자동 검증 레이어 | 2일 |
| 게시글 | #C | 퀄리티 | Few-shot 자동 업데이트 | 1.5일 |
| 게시글 | #D | 퀄리티 | SEO 메타 자동 주입 | 1일 |
| 게시글 | #E | 퀄리티 | 결론 문장 semantic 반복 방지 | 2일 |
| 게시글 | #F | 퀄리티 | 발행 전 품질 게이트 | 1일 |
| 게시글 | #G | 퀄리티 | 테마 다양성 모니터링 | 1.5일 |
| 게시글 | #H | 퀄리티 | 한국어 가독성 분석 | 1일 |

---

## 5. 즉시 착수 권장 작업 (빠른 효과)

1. **#1~#3 보안 수정**: config.py 기본값 제거, CORS 도메인 명시 — 1일 이내 완료 가능
2. **#F 발행 전 품질 게이트**: publisher.py에 20줄 추가로 구조적 품질 보장 — 즉시 착수 가능
3. **#6 재시도 로직**: tenacity 이미 requirements.txt에 포함 — 적용 비용 최소
4. **#D SEO 메타 주입**: GPT 프롬프트에 필드 2개 추가 + publisher.py 연동 — 명확한 ROI

---

*이 문서는 후속 Paperclip 이슈 생성의 기준 문서로 사용한다.*
