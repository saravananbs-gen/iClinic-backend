from fastapi import FastAPI
from contextlib import asynccontextmanager


from src.api.rest.routes.voice import router as voice_router
from src.api.rest.routes.auth import router as auth_router
from src.api.rest.routes.health import router as health_router
from src.data.clients.checkpointer import checkpoint_pool, checkpointer


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await checkpoint_pool.open()
        await checkpointer.setup()
        yield
        await checkpoint_pool.close()

    app = FastAPI(title="Voice AI Clinic Assistant", lifespan=lifespan)

    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(voice_router, prefix="/voice", tags=["Voice"])
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])

    return app
