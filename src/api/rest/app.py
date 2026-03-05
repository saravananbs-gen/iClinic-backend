from fastapi import FastAPI
from contextlib import asynccontextmanager


from src.api.rest.routes.voice import router as voice_router
from src.api.rest.routes.auth import router as auth_router
from src.api.rest.routes.health import router as health_router
from src.api.rest.routes.dashboard import router as dashboard_router
from src.data.clients.checkpointer import checkpoint_pool, checkpointer
from src.constants.logging import SERVICE_NAME, ENVIRONMENT, LOG_LEVEL
from src.observability.logging import setup_logging, get_logger
from src.api.middleware.logging import RequestLoggingMiddleware
from src.api.middleware.error_handler import ExceptionHandlerMiddleware

logger = get_logger(__name__)


def create_app() -> FastAPI:
    setup_logging(
        service_name=SERVICE_NAME,
        environment=ENVIRONMENT,
        log_level=LOG_LEVEL,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Application starting up")
        await checkpoint_pool.open()
        await checkpointer.setup()
        logger.info("Application ready")
        yield
        logger.info("Application shutting down")
        await checkpoint_pool.close()

    app = FastAPI(title="Voice AI Clinic Assistant", lifespan=lifespan)

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ExceptionHandlerMiddleware)

    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(voice_router, prefix="/voice", tags=["Voice"])
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

    return app
