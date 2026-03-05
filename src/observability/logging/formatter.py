from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone


class _Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


_LEVEL_STYLES: dict[int, tuple[str, str]] = {
    logging.DEBUG: (_Colors.GRAY, " DEBUG   "),
    logging.INFO: (_Colors.BRIGHT_GREEN, " INFO    "),
    logging.WARNING: (_Colors.BRIGHT_YELLOW, " WARN    "),
    logging.ERROR: (_Colors.BRIGHT_RED, " ERROR   "),
    logging.CRITICAL: (_Colors.RED + _Colors.BOLD, " CRITICAL"),
}


class ConsoleFormatter(logging.Formatter):
    _SEPARATOR = f" {_Colors.DIM}│{_Colors.RESET} "

    def format(self, record: logging.LogRecord) -> str:
        from src.observability.logging.context import request_ctx

        ctx = request_ctx.get()

        ts = datetime.fromtimestamp(record.created, tz=timezone.utc)
        time_str = f"{_Colors.DIM}{ts.strftime('%H:%M:%S')}{_Colors.RESET}"

        color, label = _LEVEL_STYLES.get(
            record.levelno, (_Colors.WHITE, f" {record.levelname:<8s}")
        )
        level_str = f"{color}{_Colors.BOLD}{label}{_Colors.RESET}"

        short_name = record.name.removeprefix("iclinic.")
        logger_str = f"{_Colors.CYAN}{short_name:<14s}{_Colors.RESET}"

        rid_short = ctx.request_id[:8] if ctx.request_id else "--------"
        rid_str = f"{_Colors.MAGENTA}{rid_short}{_Colors.RESET}"

        message = record.getMessage()
        msg_str = f"{_Colors.BRIGHT_WHITE}{message}{_Colors.RESET}"

        sep = self._SEPARATOR
        line = (
            f"{time_str}{sep}{level_str}{sep}{logger_str}{sep}{rid_str}{sep}{msg_str}"
        )

        parts: list[str] = [line]

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            kvs = self._format_kvs(record.extra_data)
            if kvs:
                indent = f"{'':>11s}{_Colors.DIM}↳{_Colors.RESET} "
                parts.append(f"{indent}{kvs}")

        if record.levelno >= logging.WARNING:
            src = (
                f"{_Colors.DIM}"
                f"{record.pathname}:{record.lineno} in {record.funcName}()"
                f"{_Colors.RESET}"
            )
            parts.append(f"{'':>11s}{_Colors.DIM}@{_Colors.RESET} {src}")

        if record.exc_info and record.exc_info[0] is not None:
            divider = f"{_Colors.RED}{'─' * 60}{_Colors.RESET}"
            parts.append(f"{'':>11s}{divider}")
            tb_lines = traceback.format_exception(*record.exc_info)
            for tb_line in tb_lines:
                for sub in tb_line.rstrip("\n").split("\n"):
                    parts.append(f"{'':>11s}{_Colors.RED}{sub}{_Colors.RESET}")
            parts.append(f"{'':>11s}{divider}")

        return "\n".join(parts)

    @staticmethod
    def _format_kvs(data: dict, *, _depth: int = 0) -> str:
        """Flatten a dict into coloured key=value pairs."""
        segments: list[str] = []
        for key, value in data.items():
            if isinstance(value, dict):
                nested = ConsoleFormatter._format_kvs(value, _depth=_depth + 1)
                if nested:
                    segments.append(nested)
            elif value is not None:
                k = f"{_Colors.BLUE}{key}{_Colors.RESET}"
                v = f"{_Colors.WHITE}{value}{_Colors.RESET}"
                segments.append(f"{k}={v}")
        return "  ".join(segments)


class JSONFormatter(logging.Formatter):
    def __init__(self, service_name: str, environment: str) -> None:
        super().__init__()
        self._service_name = service_name
        self._environment = environment

    def format(self, record: logging.LogRecord) -> str:
        from src.observability.logging.context import request_ctx

        ctx = request_ctx.get()

        log_entry: dict = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self._service_name,
            "environment": self._environment,
            "request_id": ctx.request_id,
        }

        if ctx.user_id:
            log_entry["user_id"] = ctx.user_id
        if ctx.method:
            log_entry["method"] = ctx.method
        if ctx.path:
            log_entry["path"] = ctx.path
        if ctx.client_ip:
            log_entry["client_ip"] = ctx.client_ip

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry["data"] = record.extra_data

        if record.levelno >= logging.WARNING:
            log_entry["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stacktrace": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, default=str, ensure_ascii=False)
