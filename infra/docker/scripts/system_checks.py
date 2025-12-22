# scripts/system_checks.py
"""
Verificações básicas de sistema para Docker.
"""

import os
import grp
from rich.console import Console

console = Console()


def check_docker_group() -> bool:
    """
    Verifica se o usuário atual está no grupo docker.

    Returns:
        bool: True se estiver no grupo docker
    """
    try:
        docker_group = grp.getgrnam('docker')
        current_user_groups = os.getgroups()
        return docker_group.gr_gid in current_user_groups
    except KeyError:
        return False


def require_docker_permissions():
    """
    Valida se o usuário tem permissões para executar Docker.
    Sai do programa se não tiver permissões.
    """
    is_root = os.geteuid() == 0
    in_docker_group = check_docker_group()

