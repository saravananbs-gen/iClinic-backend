from __future__ import annotations

import logging
import sys

from src.observability.logging.formatter import ConsoleFormatter, JSONFormatter

_NOISY_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "httpcore",
    "httpx",
    "sqlalchemy.engine",
    "asyncpg",
    "watchfiles",
)

_DEV_ENVIRONMENTS = {"development", "dev", "local"}


def setup_logging(
    *,
    service_name: str = "iclinic-backend",
    environment: str = "development",
    log_level: str = "INFO",
) -> None:

    level = getattr(logging, log_level.upper(), logging.INFO)

    if environment.lower() in _DEV_ENVIRONMENTS:
        formatter = ConsoleFormatter()
    else:
        formatter = JSONFormatter(
            service_name=service_name,
            environment=environment,
        )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console_handler)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    for name in ("iclinic", "iclinic.request", "iclinic.agent"):
        logging.getLogger(name).setLevel(level)

    logging.getLogger("iclinic").info(
        "Logging initialised",
        extra={
            "extra_data": {
                "service": service_name,
                "environment": environment,
                "log_level": log_level,
            }
        },
    )
