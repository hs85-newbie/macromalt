from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.database import create_tables
from routers import auth, payments, pipeline, users
from routers import settings as settings_router

app = FastAPI(title="macromalt API", version="1.0.0")

# [SEC1 수정] allow_origins=["*"] + allow_credentials=True 조합은 CORS 스펙 위반
# ALLOWED_ORIGINS 환경변수로 허용 도메인을 명시적으로 지정해야 함
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(settings_router.router)
app.include_router(pipeline.router)
app.include_router(payments.router)


@app.on_event("startup")
async def startup():
    await create_tables()


@app.get("/health")
async def health():
    return {"status": "ok"}


# 정적 파일 서빙 (web/ 폴더가 존재할 때만)
_WEB_DIR = Path(__file__).parent / "web"
if _WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")
