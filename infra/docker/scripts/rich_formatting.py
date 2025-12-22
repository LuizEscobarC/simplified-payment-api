# scripts/rich_formatting.py
"""
Utilitários básicos de formatação com Rich para serviços Docker.
"""

from rich.console import Console

console = Console()


def print_success(message: str):
    """Exibe mensagem de sucesso."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """Exibe mensagem de erro."""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str):
    """Exibe mensagem de aviso."""
    console.print(f"[yellow]![/yellow] {message}")


