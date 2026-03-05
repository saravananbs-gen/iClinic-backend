from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str | None = None
    method: str | None = None
    path: str | None = None
    client_ip: str | None = None


request_ctx: ContextVar[RequestContext] = ContextVar(
    "request_ctx", default=RequestContext()
)
