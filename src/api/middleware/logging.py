from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.observability.logging.context import RequestContext, request_ctx
from src.observability.logging.logger import get_logger

logger = get_logger("request")

_SKIP_PATHS: set[str] = {"/health", "/health/", "/metrics", "/metrics/"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex

        ctx = RequestContext(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )
        token = request_ctx.set(ctx)

        start = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            if isinstance(status_code, int) and "response" in dir():
                response.headers["X-Request-ID"] = request_id

            if request.url.path not in _SKIP_PATHS:
                log_data = {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.query_params) or None,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": ctx.client_ip,
                    "user_agent": request.headers.get("user-agent"),
                }

                if 500 <= status_code < 600:
                    logger.error(
                        "Request failed",
                        extra={"extra_data": log_data},
                    )
                elif 400 <= status_code < 500:
                    logger.warning(
                        "Client error",
                        extra={"extra_data": log_data},
                    )
                else:
                    logger.info(
                        "Request completed",
                        extra={"extra_data": log_data},
                    )

            request_ctx.reset(token)
