# scripts/error_handler.py
"""
Tratamento básico de erros para serviços Docker.
"""

from typing import Callable, TypeVar
import time
from rich.console import Console

console = Console()
T = TypeVar('T')


def retry_on_failure(
    func: Callable[[], T],
    max_attempts: int = 3,
    delay: float = 1.0
) -> T:
    """
    Executa função com retry em caso de falha.

    Args:
        func: Função a executar
        max_attempts: Número máximo de tentativas
        delay: Delay entre tentativas em segundos

    Returns:
        Resultado da função

    Raises:
        Exception: Última exception se todas tentativas falharem
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts - 1:
                console.print(f"⚠️  Tentativa {attempt + 1} falhou, tentando novamente em {delay}s...")
                time.sleep(delay)
