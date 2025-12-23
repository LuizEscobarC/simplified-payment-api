"""
Queue Service.

Gerencia o serviço de filas (Horizon) da aplicação Laravel.
"""

from pathlib import Path
from typing import Optional
import time
import subprocess

from rich.console import Console

from .base_service import BaseDockerService
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from scripts.env_manager import LaravelEnvManager

console = Console()


class QueueService(BaseDockerService):
    """Gerencia serviço de filas Laravel."""

    def __init__(
        self,
        container_name: str = "payment-queue",
        compose_file: Optional[Path] = None
    ):
        """
        Inicializa serviço de filas.

        Args:
            container_name: Nome do container de filas
            compose_file: Arquivo docker-compose (padrão: docker-compose.app.yml)
        """
        if compose_file is None:
            compose_file = Path(__file__).parent.parent / "docker-compose.app.yml"

        self.compose_file = compose_file
        self.service_name = "queue"

        super().__init__(
            name="Queue (Horizon)",
            container_name=container_name,
            compose_file=compose_file
        )

    def start(self, wait: bool = True) -> bool:
        """
        Inicia serviço de filas via docker-compose.

        Args:
            wait: Se True, aguarda serviço ficar pronto

        Returns:
            True se iniciou com sucesso
        """
        try:
            console.print(f"🐳 Iniciando {self.name} via docker-compose...", style="blue")

            # Comando docker-compose up
            cmd = [
                "docker-compose",
                "-f", str(self.compose_file),
                "up", "-d", self.service_name
            ]

            result = subprocess.run(
                cmd,
                cwd=self.compose_file.parent,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                console.print(f"❌ Erro ao iniciar {self.name}: {result.stderr}", style="red")
                return False

            console.print(f"✅ {self.name} iniciado", style="green")

            if wait:
                return self.wait_for_ready()

            return True

        except Exception as e:
            console.print(f"❌ Erro ao iniciar {self.name}: {e}", style="red")
            return False

    def verify(self, max_attempts: int = 60) -> bool:
        """
        Verifica se o serviço de filas está respondendo.

        Args:
            max_attempts: Máximo de tentativas

        Returns:
            True se serviço está funcionando
        """
        console.print(f"🔍 Verificando {self.name}...", style="blue")

        # Verifica se container está rodando
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True
            )

            if "Up" not in result.stdout:
                console.print(f"❌ Container {self.container_name} não está rodando", style="red")
                return False

        except Exception as e:
            console.print(f"❌ Erro ao verificar container: {e}", style="red")
            return False

        # Verifica se Horizon está rodando via supervisorctl
        try:
            result = subprocess.run(
                ["docker", "exec", self.container_name, "supervisorctl", "-s", "http://127.0.0.1:9001", "-s", "http://127.0.0.1:9001", "status", "horizon"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0 or "RUNNING" not in result.stdout:
                console.print(f"❌ Horizon não está rodando no container", style="red")
                return False

        except Exception as e:
            console.print(f"❌ Erro ao verificar Horizon: {e}", style="red")
            return False

        console.print(f"✅ {self.name} verificado", style="green")
        return True

    def stop(self) -> bool:
        """
        Para o serviço.

        Returns:
            True se parou com sucesso
        """
        try:
            console.print(f"🛑 Parando {self.name}...", style="yellow")

            cmd = [
                "docker-compose",
                "-f", str(self.compose_file),
                "down", self.service_name
            ]

            result = subprocess.run(
                cmd,
                cwd=self.compose_file.parent,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                console.print(f"❌ Erro ao parar {self.name}: {result.stderr}", style="red")
                return False

            console.print(f"✅ {self.name} parado", style="green")
            return True

        except Exception as e:
            console.print(f"❌ Erro ao parar {self.name}: {e}", style="red")
            return False

    def restart(self) -> bool:
        """
        Reinicia o serviço.

        Returns:
            True se reiniciou com sucesso
        """
        if not self.stop():
            return False

        return self.start()

    def logs(self, follow: bool = False, lines: int = 50) -> None:
        """
        Mostra logs do serviço.

        Args:
            follow: Se True, segue os logs em tempo real
            lines: Número de linhas a mostrar
        """
        try:
            cmd = [
                "docker-compose",
                "-f", str(self.compose_file),
                "logs"
            ]

            if follow:
                cmd.append("-f")

            cmd.extend(["--tail", str(lines), self.service_name])

            subprocess.run(cmd, cwd=self.compose_file.parent)

        except Exception as e:
            console.print(f"❌ Erro ao mostrar logs: {e}", style="red")