# macromalt — Claude 개발 가이드 (하네스)

> 이 파일은 모든 Claude 에이전트(서브에이전트 포함)가 반드시 읽고 따라야 하는
> 코딩 표준, 아키텍처 규칙, 검증 기준이다.
> 코드 리뷰어가 없으므로 이 가이드가 품질의 유일한 기준이다.

---

## 1. 프로젝트 구조

```
macromalt/               ← 기존 파이프라인 (Phase 1~23, 수정 최소화)
  ├── main.py            핵심 파이프라인 오케스트레이터
  ├── generator.py       OpenAI/Gemini 콘텐츠 생성
  ├── publisher.py       WordPress 발행
  ├── scraper.py         뉴스 수집
  ├── cost_tracker.py    비용 추적
  ├── .env               환경변수 (절대 커밋 금지)
  ├── design/            M0 설계 문서 (스키마, API 계약서)
  ├── api/               FastAPI 백엔드 (Phase 24 신규)
  └── web/               프론트엔드 (Phase 24 신규)
```

---

## 2. 브랜치 전략

```
main    → 프로덕션 (Railway 자동 배포)
dev     → 일반 개발 작업
feature/phase24-m1-backend   ← M1 전용
feature/phase24-m2-pipeline  ← M2 전용
feature/phase24-m3-payment   ← M3 전용
feature/phase24-m4-frontend  ← M4 전용
```

- 모든 작업은 해당 feature 브랜치에서 시작
- 테스트 통과 후 dev → main 머지
- **main에 직접 커밋 금지**

---

## 3. 커밋 메시지 규칙

```
<type>(<scope>): <요약>

type:
  feat     새 기능
  fix      버그 수정
  refactor 리팩토링 (기능 변경 없음)
  test     테스트 추가/수정
  docs     문서 수정
  chore    빌드/설정 변경

scope: m0 | m1 | m2 | m3 | m4 | pipeline | infra

예시:
  feat(m1): JWT 인증 라우터 구현 (register/login/refresh)
  fix(m2): UserContext API 키 복호화 누락 수정
  test(m1): auth 라우터 pytest 6케이스 추가
```

---

## 4. api/ 코딩 표준 (FastAPI)

### 4-1. 디렉토리 구조

```
api/
├── main.py              앱 진입점, CORS, 라우터 등록
├── core/
│   ├── config.py        환경변수 (pydantic-settings BaseSettings)
│   ├── database.py      SQLAlchemy async 세션 팩토리
│   ├── security.py      JWT, bcrypt, AES-256-GCM
│   └── deps.py          get_current_user() 의존성
├── models/
│   └── models.py        SQLAlchemy ORM 모델
├── schemas/
│   └── schemas.py       Pydantic v2 요청/응답 스키마
├── routers/
│   ├── auth.py
│   ├── users.py
│   ├── settings.py
│   ├── pipeline.py
│   └── payments.py
├── tests/
│   ├── conftest.py      pytest fixtures (TestClient, DB)
│   └── test_*.py        각 라우터별 테스트
├── requirements.txt
├── Procfile             Railway 실행 명령
└── railway.toml         Railway 설정
```

### 4-2. 필수 패턴

```python
# ✅ 올바른 라우터 패턴
from fastapi import APIRouter, Depends, HTTPException, status
from api.core.deps import get_current_user
from api.models.models import User

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=schemas.UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

```python
# ✅ 에러 처리 표준
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="사용자를 찾을 수 없습니다"
)

# ❌ 금지
raise Exception("error")
print("error")
```

```python
# ✅ 환경변수 접근
from api.core.config import settings
db_url = settings.DATABASE_URL

# ❌ 금지
import os
db_url = os.getenv("DATABASE_URL")
```

### 4-3. 보안 필수 사항

- **API 키, WP 비밀번호**: AES-256-GCM으로 암호화 후 DB 저장 (평문 금지)
- **JWT**: access_token 만료 1시간, refresh_token 30일
- **비밀번호**: bcrypt 해시 저장 (평문 금지)
- **CORS**: 프로덕션에서 허용 오리진 명시적 지정 (wildcard 금지)

---

## 5. 테스트 기준 (머지 전 필수)

```bash
# api/ 테스트 실행
cd api && pytest tests/ -v

# 통과 기준: 모든 테스트 GREEN
# 최소 테스트 항목:
#   - POST /api/auth/register → 201
#   - POST /api/auth/login    → 200 (JWT 반환)
#   - GET  /api/users/me      → 200 (인증 필요)
#   - GET  /api/users/me      → 401 (토큰 없을 때)
#   - 각 라우터 최소 2케이스 (정상 + 에러)
```

---

## 6. DB 규칙

- **로컬 개발**: SQLite (`api/local.db`)
- **프로덕션**: PostgreSQL (Railway `DATABASE_URL` 자동 주입)
- **마이그레이션**: Alembic 사용 (수동 스키마 변경 금지)
- **모델 변경 시**: 반드시 Alembic revision 생성 후 커밋

```python
# database.py 패턴
DATABASE_URL = settings.DATABASE_URL
# SQLite: "sqlite+aiosqlite:///./local.db"
# PostgreSQL: "postgresql+asyncpg://..."

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

---

## 7. pipeline/ 수정 규칙 (M2 전용)

- **기존 파이프라인 회귀 금지**: main.py 수정 후 반드시 단독 실행 테스트
- **UserContext 패턴**:

```python
# design/user_context.py 참조
from design.user_context import UserContext

async def run_pipeline(ctx: UserContext):
    # ctx.openai_api_key, ctx.gemini_api_key 사용
    # ctx.wp_url, ctx.wp_username, ctx.wp_password 사용
    ...
```

- `os.getenv("OPENAI_API_KEY")` → `ctx.openai_api_key` 으로 전환
- 기존 단독 실행 모드(`__main__`) 유지 (하위 호환)

---

## 8. web/ 코딩 표준

- **스택**: Vanilla JS + TailwindCSS CDN (프레임워크 없음)
- **API 호출**: `fetch()` + JWT Bearer 헤더
- **토큰 관리**: `localStorage` 저장 (`access_token`, `refresh_token`)
- **에러 처리**: 401 응답 시 자동 refresh → 실패 시 login 페이지 이동

---

## 9. Railway 배포 설정

```
# api/Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT

# api/railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
```

Railway 환경변수 (Settings → Variables에서 설정):
```
DATABASE_URL     (Railway PostgreSQL 자동 주입)
JWT_SECRET_KEY   (랜덤 32바이트 hex)
AES_SECRET_KEY   (랜덤 32바이트 hex)
TOSS_SECRET_KEY  (Toss 테스트 시크릿 키)
ENVIRONMENT      production
```

---

## 10. 작업 완료 체크리스트 (머지 전)

각 모듈 완료 시 아래 항목을 모두 확인:

- [ ] pytest 전체 GREEN
- [ ] `uvicorn` 로컬 실행 후 `/health` 엔드포인트 200 응답
- [ ] `.env` 또는 시크릿 파일 커밋 여부 확인 (절대 금지)
- [ ] 하드코딩된 URL, 키, 비밀번호 없음
- [ ] 커밋 메시지 규칙 준수
- [ ] feature 브랜치 → dev 머지 PR 생성

---

## 11. 현재 Phase 진행 현황

| Phase | 상태 | 내용 |
|-------|------|------|
| 1~23 | ✅ 완료 | 파이프라인 자동화 (macromalt/) |
| 24-M0 | 🔄 진행 중 | 설계 문서 작성 |
| 24-M1 | ⏳ 대기 | FastAPI 백엔드 |
| 24-M2 | ⏳ 대기 | 파이프라인 멀티유저 전환 |
| 24-M3 | ⏳ 대기 | Toss 결제 (테스트 모드) |
| 24-M4 | ⏳ 대기 | 프론트엔드 |

---

## 12. 주요 참고 문서

- `design/schema.sql` — DB 테이블 정의
- `design/openapi.yaml` — API 엔드포인트 계약서
- `design/user_context.py` — UserContext 데이터클래스
- `docs/88_etc/REPORT/REPORT_MONETIZATION_TRANSITION_PLAN_V1.md` — 수익화 전환 계획
- `docs/88_etc/REPORT/REPORT_TECHNICAL_KNOWHOW_V1.md` — 기술 노하우 종합
