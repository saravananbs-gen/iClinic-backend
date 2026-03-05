from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.observability.logging.context import request_ctx
from src.observability.logging.logger import get_logger

logger = get_logger("error_handler")


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception:
            ctx = request_ctx.get()
            logger.critical(
                "Unhandled exception",
                exc_info=True,
                extra={
                    "extra_data": {
                        "request_id": ctx.request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "client_ip": ctx.client_ip,
                    }
                },
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "request_id": ctx.request_id,
                },
            )
