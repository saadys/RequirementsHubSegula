"""
Structured Logging Configuration module conforming to Twelve-Factor App (Factor XI: Logs to stdout).

Supports GCP Cloud Logging (JSON mode in production) and human-readable text mode (in development).
"""

import datetime
import json
import logging
import logging.config
import os
import sys


class GCPJsonFormatter(logging.Formatter):
    """
    Formateur JSON natif conforme aux conventions de GCP Cloud Logging.
    Convertit chaque LogRecord Python en une ligne JSON unique avec les champs standardisés GCP.
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp_iso = datetime.datetime.fromtimestamp(
            record.created, tz=datetime.timezone.utc
        ).isoformat()

        log_payload = {
            "severity": record.levelname,
            "timestamp": timestamp_iso,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload, ensure_ascii=False)


def setup_logging(log_level: str | None = None, log_format: str | None = None) -> None:
    """
    Construit et applique la configuration de logging via logging.config.dictConfig.
    Centralise et unifie le logger racine, le logger backend ainsi que uvicorn sur sys.stdout.
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    if log_format is None:
        is_cloud_run = bool(os.getenv("K_SERVICE"))
        env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
        if is_cloud_run or env in ("production", "prod"):
            default_format = "json"
        else:
            default_format = "text"
        log_format = os.getenv("LOG_FORMAT", default_format).lower()

    formatter_key = "gcp_json" if log_format == "json" else "text"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "gcp_json": {
                "()": "backend.core.GCPJsonFormatter.GCPJsonFormatter",
            },
            "text": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": formatter_key,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["stdout"],
                "level": log_level,
            },
            "backend": {
                "handlers": ["stdout"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["stdout"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["stdout"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["stdout"],
                "level": log_level,
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(config)
