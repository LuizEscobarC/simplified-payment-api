# scripts/prerequisites.py
"""
Módulo de validação de pré-requisitos.

Valida sistema, dependências e permissões necessárias
para execução dos scripts Docker.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
logger = logging.getLogger(__name__)

class PrerequisiteError(Exception):
    """Erro de pré-requisito não atendido."""
    pass

class PrerequisiteChecker:
    """Validador de pré-requisitos do sistema."""

    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def check_all(self, show_progress: bool = True) -> bool:
        """Executa todas as validações de pré-requisitos."""
        console.print("\n[bold cyan]═══ System Prerequisites Check ═══[/bold cyan]")

        checks = [
            ("system", self._check_system_requirements),
            ("docker", self._check_docker_installation),
            ("docker_daemon", self._check_docker_daemon),
            ("docker_permissions", self._check_docker_permissions),
            ("python", self._check_python_version),
            ("dependencies", self._check_python_dependencies),
            ("network", self._check_network_connectivity),
            ("disk_space", self._check_disk_space),
            ("permissions", self._check_file_permissions)
        ]

        all_passed = True

        for check_name, check_func in checks:
            if show_progress:
                console.print(f"\n[bold]{check_name.replace('_', ' ').title()}:[/bold]", end=" ")

            try:
                result = check_func()
                self.results[check_name] = result

                if result["status"] == "pass":
                    if show_progress:
                        console.print("[green]✓[/green]")
                    logger.debug(f"✓ {check_name}: {result.get('message', 'OK')}")
                elif result["status"] == "warning":
                    if show_progress:
                        console.print("[yellow]⚠[/yellow]")
                    self.warnings.append(f"{check_name}: {result.get('message', '')}")
                    logger.warning(f"⚠ {check_name}: {result.get('message', '')}")
                else:  # fail
                    if show_progress:
                        console.print("[red]✗[/red]")
                    self.errors.append(f"{check_name}: {result.get('message', '')}")
                    logger.error(f"✗ {check_name}: {result.get('message', '')}")
                    all_passed = False

            except Exception as e:
                if show_progress:
                    console.print("[red]✗[/red]")
                error_msg = f"Exception during {check_name}: {str(e)}"
                self.errors.append(error_msg)
                logger.error(f"✗ {error_msg}")
                all_passed = False

        # Resumo
        self._print_summary()

        return all_passed

    def _check_system_requirements(self) -> Dict:
        """Verifica requisitos básicos do sistema."""
        system = platform.system().lower()
        arch = platform.machine().lower()

        # Sistemas suportados
        supported_systems = ["linux", "darwin", "windows"]
        supported_archs = ["x86_64", "amd64", "arm64", "aarch64"]

        if system not in supported_systems:
            return {
                "status": "fail",
                "message": f"Unsupported OS: {system}. Supported: {', '.join(supported_systems)}"
            }

        if arch not in supported_archs:
            return {
                "status": "warning",
                "message": f"Architecture {arch} may not be fully supported. Recommended: x86_64/amd64"
            }

        return {
            "status": "pass",
            "message": f"{system.capitalize()} {arch} detected",
            "details": {
                "os": system,
                "arch": arch,
                "version": platform.version()
            }
        }

    def _check_docker_installation(self) -> Dict:
        """Verifica se Docker está instalado."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                version_line = result.stdout.strip()
                # Extrair versão (formato: Docker version 24.0.7, build afdd53b)
                version = version_line.split()[2].rstrip(',')

                # Verificar versão mínima
                min_version = "20.10.0"
                if self._compare_versions(version, min_version) < 0:
                    return {
                        "status": "warning",
                        "message": f"Docker version {version} is below recommended {min_version}"
                    }

                return {
                    "status": "pass",
                    "message": f"Docker {version} installed",
                    "details": {"version": version}
                }
            else:
                return {
                    "status": "fail",
                    "message": "Docker not found or not working"
                }

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {
                "status": "fail",
                "message": "Docker command not found. Please install Docker."
            }

    def _check_docker_daemon(self) -> Dict:
        """Verifica se Docker daemon está rodando."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                return {
                    "status": "pass",
                    "message": "Docker daemon is running"
                }
            else:
                return {
                    "status": "fail",
                    "message": "Docker daemon is not running. Please start Docker service."
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "fail",
                "message": "Docker daemon check timed out. Docker may not be running."
            }

    def _check_docker_permissions(self) -> Dict:
        """Verifica permissões do Docker."""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {
                    "status": "pass",
                    "message": "Docker permissions OK"
                }
            else:
                error_msg = result.stderr.lower()
                if "permission denied" in error_msg or "got permission denied" in error_msg:
                    return {
                        "status": "fail",
                        "message": "Docker permission denied. Add user to docker group or run with sudo."
                    }
                else:
                    return {
                        "status": "fail",
                        "message": f"Docker permission check failed: {error_msg}"
                    }

        except subprocess.TimeoutExpired:
            return {
                "status": "fail",
                "message": "Docker permission check timed out"
            }

    def _check_python_version(self) -> Dict:
        """Verifica versão do Python."""
        version = sys.version_info
        current_version = f"{version.major}.{version.minor}.{version.micro}"

        min_version = (3, 8, 0)
        recommended_version = (3, 10, 0)

        if version < min_version:
            return {
                "status": "fail",
                "message": f"Python {current_version} is below minimum {'.'.join(map(str, min_version))}"
            }

        if version < recommended_version:
            return {
                "status": "warning",
                "message": f"Python {current_version} works but {'.'.join(map(str, recommended_version))}+ recommended"
            }

        return {
            "status": "pass",
            "message": f"Python {current_version} OK",
            "details": {"version": current_version}
        }

    def _check_python_dependencies(self) -> Dict:
        """Verifica dependências Python."""
        required_packages = [
            "docker",
            "rich",
            # Não estou utilizando mysql no momento
            # "mysql.connector",
            "pathlib",
            "typing"
        ]

        missing_packages = []
        version_issues = []

        for package in required_packages:
            try:
                if package == "mysql.connector":
                    import mysql.connector as mysql_conn
                    version = getattr(mysql_conn, "__version__", "unknown")
                else:
                    module = __import__(package)
                    version = getattr(module, "__version__", "unknown")

                logger.debug(f"✓ {package} {version}")

            except ImportError:
                missing_packages.append(package)
            except Exception as e:
                version_issues.append(f"{package}: {str(e)}")

        if missing_packages:
            return {
                "status": "fail",
                "message": f"Missing packages: {', '.join(missing_packages)}"
            }

        if version_issues:
            return {
                "status": "warning",
                "message": f"Package issues: {', '.join(version_issues)}"
            }

        return {
            "status": "pass",
            "message": "All Python dependencies OK"
        }

    def _check_network_connectivity(self) -> Dict:
        """Verifica conectividade de rede."""
        test_urls = [
            "https://registry-1.docker.io",  # Docker Hub
            "https://hub.docker.com"         # Docker Hub website
        ]

        success_count = 0

        for url in test_urls:
            try:
                result = subprocess.run(
                    ["curl", "-I", "--max-time", "5", url],
                    capture_output=True,
                    timeout=10
                )

                if result.returncode == 0:
                    success_count += 1
                else:
                    logger.debug(f"Failed to connect to {url}")

            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug(f"Network check failed for {url}")

        if success_count == len(test_urls):
            return {
                "status": "pass",
                "message": "Network connectivity OK"
            }
        elif success_count > 0:
            return {
                "status": "warning",
                "message": f"Limited network connectivity ({success_count}/{len(test_urls)} URLs reachable)"
            }
        else:
            return {
                "status": "fail",
                "message": "No network connectivity. Check internet connection."
            }

    def _check_disk_space(self) -> Dict:
        """Verifica espaço em disco."""
        try:
            # Verificar espaço no diretório atual
            stat = os.statvfs(Path.cwd())

            # Espaço disponível em GB
            available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

            min_space_gb = 5.0  # 5GB mínimo

            if available_gb < min_space_gb:
                return {
                    "status": "fail",
                    "message": f"Insufficient disk space: {available_gb:.2f}GB available, need {min_space_gb}GB"
                }

            if available_gb < 10.0:  # Warning se menos de 10GB
                return {
                    "status": "warning",
                    "message": f"Low disk space: {available_gb:.2f}GB available, recommended 10GB+"
                }

            return {
                "status": "pass",
                "message": f"Disk space OK: {available_gb:.2f}GB available",
                "details": {"available_gb": available_gb}
            }

        except Exception as e:
            return {
                "status": "warning",
                "message": f"Could not check disk space: {str(e)}"
            }

    def _check_file_permissions(self) -> Dict:
        """Verifica permissões de arquivos importantes."""
        important_files = [
            "docker-compose.yml",
            "docker-compose-*.yml",
            "Dockerfile*",
            "setup*.sh",
            "scripts/"
        ]

        permission_issues = []

        for pattern in important_files:
            if "*" in pattern:
                # Padrão com wildcard
                import glob
                matches = glob.glob(pattern)
                for file_path in matches:
                    if not self._check_file_accessible(file_path):
                        permission_issues.append(file_path)
            else:
                # Arquivo específico
                if os.path.exists(pattern):
                    if not self._check_file_accessible(pattern):
                        permission_issues.append(pattern)

        if permission_issues:
            return {
                "status": "fail",
                "message": f"Permission issues with: {', '.join(permission_issues)}"
            }

        return {
            "status": "pass",
            "message": "File permissions OK"
        }

    def _check_file_accessible(self, file_path: str) -> bool:
        """Verifica se arquivo é acessível."""
        try:
            if os.path.isdir(file_path):
                os.listdir(file_path)
            else:
                with open(file_path, 'r') as f:
                    f.read(1)  # Tentar ler primeiro byte
            return True
        except (PermissionError, OSError):
            return False

    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compara duas versões semânticas."""
        def parse_version(v):
            return [int(x) for x in v.split('.') if x.isdigit()]

        v1_parts = parse_version(version1)
        v2_parts = parse_version(version2)

        # Preencher com zeros para comparar
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1

        return 0

    def _print_summary(self):
        """Imprime resumo dos resultados."""
        console.print("\n[bold]Summary:[/bold]")

        if not self.errors and not self.warnings:
            console.print("[green]✓ All prerequisites passed![/green]")
            return

        # Tabela de resultados
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Check", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Message", style="white")

        for check_name, result in self.results.items():
            status = result["status"]
            message = result.get("message", "")

            if status == "pass":
                status_display = "[green]✓[/green]"
            elif status == "warning":
                status_display = "[yellow]⚠[/yellow]"
            else:
                status_display = "[red]✗[/red]"

            table.add_row(
                check_name.replace("_", " ").title(),
                status_display,
                message
            )

        console.print(table)

        # Avisos
        if self.warnings:
            console.print(f"\n[yellow]Warnings ({len(self.warnings)}):[/yellow]")
            for warning in self.warnings:
                console.print(f"  • {warning}")

        # Erros
        if self.errors:
            console.print(f"\n[red]Errors ({len(self.errors)}):[/red]")
            for error in self.errors:
                console.print(f"  • {error}")

    def get_fix_suggestions(self) -> List[str]:
        """Retorna sugestões de correção baseadas nos erros."""
        suggestions = []

        for error in self.errors:
            error_lower = error.lower()

            if "docker" in error_lower and "not found" in error_lower:
                suggestions.append("Install Docker: https://docs.docker.com/get-docker/")
            elif "docker daemon" in error_lower and "not running" in error_lower:
                suggestions.append("Start Docker service: sudo systemctl start docker (Linux) or start Docker Desktop")
            elif "docker permission" in error_lower:
                suggestions.append("Add user to docker group: sudo usermod -aG docker $USER (then logout/login)")
            elif "python" in error_lower and "below minimum" in error_lower:
                suggestions.append("Upgrade Python to version 3.8+")
            elif "missing packages" in error_lower:
                suggestions.append("Install missing packages: pip install docker rich mysql-connector-python")
            elif "network connectivity" in error_lower:
                suggestions.append("Check internet connection and firewall settings")
            elif "disk space" in error_lower:
                suggestions.append("Free up disk space or use a different directory")
            elif "permission" in error_lower:
                suggestions.append("Check file permissions and ownership")

        return suggestions

def check_prerequisites(show_progress: bool = True) -> bool:
    """Função de conveniência para verificar pré-requisitos."""
    checker = PrerequisiteChecker()
    return checker.check_all(show_progress=show_progress)

def main():
    """Função principal para uso via linha de comando."""
    import argparse

    parser = argparse.ArgumentParser(description="Check system prerequisites for Docker setup")
    parser.add_argument("--quiet", "-q", action="store_true", help="Don't show progress")
    parser.add_argument("--fix", action="store_true", help="Show fix suggestions")

    args = parser.parse_args()

    checker = PrerequisiteChecker()
    success = checker.check_all(show_progress=not args.quiet)

    if args.fix and (checker.errors or checker.warnings):
        console.print("\n[bold]Fix Suggestions:[/bold]")
        suggestions = checker.get_fix_suggestions()
        for suggestion in suggestions:
            console.print(f"  • {suggestion}")

    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)