from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:

    return logging.getLogger(f"iclinic.{name}")


def get_agent_logger() -> logging.Logger:

    return logging.getLogger("iclinic.agent")
