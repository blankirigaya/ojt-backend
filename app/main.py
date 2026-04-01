# """
# FastAPI application factory.
# Configures middleware, exception handlers, lifespan, and registers all routers.
# """
import logging
from contextlib import asynccontextmanager

# from fastapi import FastAPI

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.db.session import init_db
from app.api.v1.router import api_router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before yielding, shutdown tasks after."""
    logger.info("🚀 Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    # In production, use Alembic migrations instead of create_all.
    # This is kept here for convenience in development / Docker first-run.
    if settings.DEBUG:
        await init_db()
        logger.info("✅ Database tables verified / created")

    yield  # App is running

    logger.info("🛑 Shutting down")

# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handlers ─────────────────────────────────────────────
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred"},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

app = create_app()

# ── Health check ──────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health():
    return {"status": "ok"}
