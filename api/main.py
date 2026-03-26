from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import create_tables
from routers import auth, payments, pipeline, settings, users

app = FastAPI(title="macromalt API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(settings.router)
app.include_router(pipeline.router)
app.include_router(payments.router)


@app.on_event("startup")
async def startup():
    await create_tables()


@app.get("/health")
async def health():
    return {"status": "ok"}
