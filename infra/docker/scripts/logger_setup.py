# scripts/logger_setup.py
"""
Configuração básica de logging para serviços Docker.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_basic_logging(level: str = "INFO", log_file: Optional[Path] = None):
    """
    Configuração básica de logging.

    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Arquivo para salvar logs (opcional)
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Limpar handlers existentes
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler se especificado
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna logger configurado.

    Args:
        name: Nome do logger

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
