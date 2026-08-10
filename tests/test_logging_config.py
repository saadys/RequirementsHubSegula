"""
Unit tests for backend/core/logging_config.py (GCP Json Formatter & dictConfig setup).
"""

import json
import logging
import sys
from io import StringIO
import pytest

from backend.core.GCPJsonFormatter import GCPJsonFormatter, setup_logging


def test_gcp_json_formatter_keys():
    """Vérifie que GCPJsonFormatter génère une ligne JSON valide avec les clés requises par GCP Cloud Logging."""
    formatter = GCPJsonFormatter()
    logger = logging.getLogger("test_logger")
    record = logger.makeRecord(
        name="test_logger",
        level=logging.INFO,
        fn="test_logging_config.py",
        lno=15,
        msg="Test log message: %s",
        args=("hello",),
        exc_info=None,
    )

    formatted_str = formatter.format(record)
    data = json.loads(formatted_str)

    assert data["severity"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["message"] == "Test log message: hello"
    assert "timestamp" in data
    assert "exception" not in data


def test_gcp_json_formatter_with_exception():
    """Vérifie que GCPJsonFormatter inclut la stack trace sous 'exception' en cas d'erreur."""
    formatter = GCPJsonFormatter()
    logger = logging.getLogger("test_logger_exc")

    try:
        raise ValueError("Erreur simulée")
    except ValueError:
        exc_info = sys.exc_info()

    record = logger.makeRecord(
        name="test_logger_exc",
        level=logging.ERROR,
        fn="test_logging_config.py",
        lno=30,
        msg="Une erreur est survenue",
        args=(),
        exc_info=exc_info,
    )

    formatted_str = formatter.format(record)
    data = json.loads(formatted_str)

    assert data["severity"] == "ERROR"
    assert data["message"] == "Une erreur est survenue"
    assert "exception" in data
    assert "ValueError: Erreur simulée" in data["exception"]


def test_setup_logging_json_mode(monkeypatch):
    """Vérifie la configuration de logging en mode JSON."""
    monkeypatch.setenv("LOG_FORMAT", "json")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    setup_logging()

    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0].formatter, GCPJsonFormatter)


def test_setup_logging_text_mode(monkeypatch):
    """Vérifie la configuration de logging en mode texte (dev)."""
    monkeypatch.setenv("LOG_FORMAT", "text")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    setup_logging()

    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 1
    assert not isinstance(root_logger.handlers[0].formatter, GCPJsonFormatter)


def test_real_stdout_emission_json_mode(monkeypatch, capsys):
    """Test réel de capture stdout en mode JSON GCP."""
    monkeypatch.setenv("LOG_FORMAT", "json")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    setup_logging()

    test_logger = logging.getLogger("backend.test.real")
    test_logger.info("Message de log réel pour GCP | model=gemini-1.5-flash duration_ms=120.50")

    captured = capsys.readouterr()
    stdout_lines = [line for line in captured.out.splitlines() if line.strip()]

    assert len(stdout_lines) >= 1
    # Choisir la dernière ligne émise
    last_line = stdout_lines[-1]
    parsed = json.loads(last_line)

    assert parsed["severity"] == "INFO"
    assert parsed["logger"] == "backend.test.real"
    assert "Message de log réel pour GCP" in parsed["message"]
    assert "timestamp" in parsed


def test_real_stdout_emission_with_exception_json_mode(monkeypatch, capsys):
    """Test réel de capture stdout avec exception en mode JSON GCP."""
    monkeypatch.setenv("LOG_FORMAT", "json")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    setup_logging()

    test_logger = logging.getLogger("backend.test.exception")

    try:
        raise KeyError("Clé de configuration manquante")
    except KeyError:
        test_logger.error("Échec critique de traitement", exc_info=True)

    captured = capsys.readouterr()
    stdout_lines = [line for line in captured.out.splitlines() if line.strip()]

    assert len(stdout_lines) >= 1
    last_line = stdout_lines[-1]
    parsed = json.loads(last_line)

    assert parsed["severity"] == "ERROR"
    assert parsed["logger"] == "backend.test.exception"
    assert parsed["message"] == "Échec critique de traitement"
    assert "exception" in parsed
    assert "KeyError: 'Clé de configuration manquante'" in parsed["exception"]
