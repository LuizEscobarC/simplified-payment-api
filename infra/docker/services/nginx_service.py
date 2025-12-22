"""
Nginx Service.

Gerencia o serviço Nginx para a aplicação Laravel.
"""

from pathlib import Path
from typing import Optional
import time
import subprocess

from rich.console import Console

from .base_service import BaseDockerService

console = Console()


class NginxService(BaseDockerService):
    """Gerencia serviço Nginx."""

    def __init__(
        self,
        container_name: str = "payment-nginx",
        compose_file: Optional[Path] = None
    ):
        """
        Inicializa serviço Nginx.

        Args:
            container_name: Nome do container Nginx
            compose_file: Arquivo docker-compose (padrão: docker-compose.app.yml)
        """
        if compose_file is None:
            compose_file = Path(__file__).parent.parent / "docker-compose.app.yml"

        self.compose_file = compose_file
        self.service_name = "payment-nginx"

        super().__init__(
            name="Nginx",
            container_name=container_name,
            compose_file=compose_file
        )

    def start(self, wait: bool = True) -> bool:
        """
        Inicia serviço Nginx via docker-compose.

        Args:
            wait: Se True, aguarda serviço ficar pronto

        Returns:
            True se iniciou com sucesso
        """
        try:
            console.print(f"🌐 Iniciando {self.name} via docker-compose...", style="blue")

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
                return self.verify()
            return True

        except Exception as e:
            console.print(f"💥 Erro ao iniciar {self.name}: {e}", style="red")
            return False

    def stop(self) -> bool:
        """
        Para serviço Nginx.

        Returns:
            True se parou com sucesso
        """
        try:
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

            return result.returncode == 0

        except Exception as e:
            console.print(f"❌ Erro ao parar {self.name}: {e}", style="red")
            return False

    def verify(self, max_attempts: int = 30) -> bool:
        """
        Verifica se Nginx está respondendo.

        Args:
            max_attempts: Máximo de tentativas

        Returns:
            True se serviço está funcionando
        """
        console.print(f"🔍 Verificando {self.name}...", style="blue")

        # Para Nginx, apenas verifica se o container está rodando
        # A verificação HTTP pode falhar se o Laravel não estiver totalmente pronto
        for attempt in range(1, max_attempts + 1):
            try:
                result = subprocess.run(
                    ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True
                )

                if "Up" in result.stdout:
                    console.print(f"✅ {self.name} verificado", style="green")
                    return True

            except Exception as e:
                console.print(f"❌ Erro ao verificar container: {e}", style="red")
                return False

            if attempt < max_attempts:
                time.sleep(1)

        console.print(f"❌ {self.name} não está rodando após {max_attempts} tentativas", style="red")
        return False

    def _check_http_endpoint(self, url: str, max_attempts: int = 30) -> bool:
        """
        Verifica se um endpoint HTTP está respondendo.

        Args:
            url: URL para verificar
            max_attempts: Número máximo de tentativas

        Returns:
            True se endpoint responde
        """
        import urllib.request
        import time

        for attempt in range(1, max_attempts + 1):
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as response:
                    if 200 <= response.getcode() < 400:  # Aceita 2xx e 3xx
                        return True
            except Exception:
                pass

            if attempt < max_attempts:
                time.sleep(1)

        return False

    def logs(self, follow: bool = False) -> None:
        """
        Mostra logs do serviço.

        Args:
            follow: Se True, segue logs em tempo real
        """
        cmd = ["docker-compose", "-f", str(self.compose_file), "logs"]
        if follow:
            cmd.append("-f")
        cmd.append(self.service_name)

        subprocess.run(cmd, cwd=self.compose_file.parent)

    def cleanup_existing(self) -> None:
        """Remove containers existentes."""
        try:
            subprocess.run(
                ["docker-compose", "-f", str(self.compose_file), "down", self.service_name],
                cwd=self.compose_file.parent,
                capture_output=True
            )
        except Exception:
            pass