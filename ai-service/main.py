"""
=============================================================
Verity AI — Unified Python FastAPI Backend
Replaces Node.js backend entirely.
Endpoints:
  Auth   : /api/auth/*
  Upload : /api/upload/*
  Verify : /api/verify/*
  Manager: /api/manager/*
  History: /api/history/*
  Health : /api/health
=============================================================
"""

import os
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
load_dotenv()

from app.config.sqlite_db import init_db
from app.config.logger import get_logger
from app.config.settings import settings
from app.routers import auth, upload, verify, manager, history, health, zkp, eligibility, websocket, loan_verification
from app.middleware.monitoring import MonitoringMiddleware
from prometheus_client import make_asgi_app

logger = get_logger("verity-ai")

# ── Startup / Shutdown ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(" Verity AI Backend starting...")
    await init_db()
    logger.info(f" OCR Provider: Google Cloud Vision API")
    yield
    logger.info(" Verity AI Backend shutting down.")


# ── FastAPI App ────────────────────────────────────────────
app = FastAPI(
    title="Verity AI",
    description="AI-powered Bank Loan Document Verification — Unified Python Backend",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ───────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Monitoring Middleware ──────────────────────────────────
if settings.prometheus_enabled:
    app.add_middleware(MonitoringMiddleware)

# ── Static files (uploaded documents) ────────────────────
upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

# ── Route Registration ─────────────────────────────────────
app.include_router(health.router,   prefix="/api/health",   tags=["Health"])
app.include_router(auth.router,     prefix="/api/auth",     tags=["Auth"])
app.include_router(upload.router,   prefix="/api/upload",   tags=["Upload"])
app.include_router(verify.router,   prefix="/api/verify",   tags=["Verify"])
app.include_router(zkp.router,      prefix="/api/zkp",      tags=["ZKP"])
app.include_router(eligibility.router, prefix="/api/eligibility", tags=["Eligibility"])
app.include_router(loan_verification.router, prefix="/api/loans", tags=["Loans"])
app.include_router(manager.router,  prefix="/api/manager",  tags=["Manager"])
app.include_router(history.router,  prefix="/api/history",  tags=["History"])
app.include_router(websocket.router, prefix="/api",         tags=["WebSocket"])

# ── Prometheus Metrics Endpoint ────────────────────────────
if settings.prometheus_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


# ── Run directly ───────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 5000)),
        reload=True,
        log_level="info",
    )
