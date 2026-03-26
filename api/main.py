"""macromalt FastAPI 앱 — M1에서 구현 완성"""
from fastapi import FastAPI

app = FastAPI(title="macromalt API", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "ok"}
