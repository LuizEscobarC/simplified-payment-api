"""
Laravel Application Service.

Gerencia o serviço da aplicação Laravel.
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


class LaravelService(BaseDockerService):
    """Gerencia serviço da aplicação Laravel."""

    def __init__(
        self,
        container_name: str = "payment-api",
        compose_file: Optional[Path] = None
    ):
        """
        Inicializa serviço Laravel.

        Args:
            container_name: Nome do container Laravel
            compose_file: Arquivo docker-compose (padrão: docker-compose.app.yml)
        """
        if compose_file is None:
            compose_file = Path(__file__).parent.parent / "docker-compose.app.yml"

        self.compose_file = compose_file
        self.service_name = "app"

        super().__init__(
            name="Laravel",
            container_name=container_name,
            compose_file=compose_file
        )

    def start(self, wait: bool = True) -> bool:
        """
        Inicia serviço Laravel via docker-compose.

        Args:
            wait: Se True, aguarda serviço ficar pronto

        Returns:
            True se iniciou com sucesso
        """
        try:
            console.print(f"🐳 Iniciando {self.name} via docker-compose...", style="blue")

            # Copiar .env da aplicação para o diretório docker
            api_env = self.compose_file.parent.parent / "api" / ".env"
            docker_env = self.compose_file.parent / ".env"
            if api_env.exists():
                import shutil
                shutil.copy2(api_env, docker_env)
                console.print(f"✅ .env copiado de {api_env} para {docker_env}", style="green")

            # Validar arquivo .env antes de iniciar
            env_manager = LaravelEnvManager(docker_env)
            if not env_manager.setup_laravel_env():
                console.print(f"❌ Falha na configuração do ambiente Laravel", style="red")
                return False

            # Comando docker-compose up
            result = self.run_compose_command(["up", "-d", self.service_name])

            if result.returncode != 0:
                console.print(f"❌ Erro ao iniciar {self.name}: {result.stderr}", style="red")
                return False

            console.print(f"✅ {self.name} iniciado", style="green")

            # Aguardar container estar totalmente pronto antes do entrypoint
            console.print("⏳ Aguardando container Laravel ficar pronto...", style="cyan")
            time.sleep(5)  # Aguardar 5 segundos para container inicializar
            
            # Verificar se container está respondendo
            if not self._wait_for_container_ready():
                console.print(f"❌ Container {self.name} não ficou pronto", style="red")
                return False

            # Executar entrypoint externamente
            if not self._run_entrypoint():
                console.print(f"❌ Falha ao executar entrypoint do {self.name}", style="red")
                return False

            if wait:
                return self.verify()
            return True

        except Exception as e:
            console.print(f"💥 Erro ao iniciar {self.name}: {e}", style="red")
            return False

    def _run_entrypoint(self) -> bool:
        """
        Executa o entrypoint Python dentro do container Laravel.

        Returns:
            True se entrypoint executou com sucesso
        """
        try:
            console.print("🚀 Executando entrypoint Laravel...", style="blue")

            # Aguardar um pouco mais para garantir que o container está estável
            time.sleep(2)

            # Executar entrypoint do host
            entrypoint_path = self.compose_file.parent / "entrypoint.py"
            cmd = [
                "python3", str(entrypoint_path),
                "--container", self.container_name
            ]

            console.print(f"📋 Executando: {' '.join(cmd)}", style="dim")

            result = subprocess.run(
                cmd,
                cwd=self.compose_file.parent,
                capture_output=False,  # Mostrar output do entrypoint
                text=True
            )

            if result.returncode != 0:
                console.print(f"❌ Entrypoint falhou com código {result.returncode}", style="red")
                return False

            console.print("✅ Entrypoint executado com sucesso", style="green")
            return True

        except Exception as e:
            console.print(f"❌ Erro ao executar entrypoint: {e}", style="red")
            return False

    def stop(self) -> bool:
        """
        Para serviço Laravel.

        Returns:
            True se parou com sucesso
        """
        try:
            result = self.run_compose_command(["down", self.service_name])

            if result.returncode != 0:
                console.print(f"❌ Erro ao parar {self.name}: {result.stderr}", style="red")
                return False

            console.print(f"✅ {self.name} parado", style="green")
            return True

        except Exception as e:
            console.print(f"❌ Erro ao parar {self.name}: {e}", style="red")
            return False

    def _wait_for_container_ready(self, max_attempts: int = 30) -> bool:
        """
        Aguarda container Laravel ficar pronto para receber comandos.

        Args:
            max_attempts: Máximo de tentativas

        Returns:
            True se container está pronto
        """
        console.print("⏳ Verificando se container está pronto...", style="cyan")

        for attempt in range(max_attempts):
            try:
                # Verifica se container está rodando
                result = subprocess.run(
                    ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True
                )

                if "Up" not in result.stdout:
                    if attempt % 5 == 0:
                        console.print(".", end="", style="cyan")
                    time.sleep(2)
                    continue

                # Verifica se podemos executar comandos no container
                result = subprocess.run(
                    ["docker", "exec", self.container_name, "test", "-d", "/var/www/html"],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    console.print("\n✅ Container Laravel pronto!", style="green")
                    return True

                if attempt % 5 == 0:
                    console.print(".", end="", style="cyan")

            except Exception:
                if attempt % 5 == 0:
                    console.print(".", end="", style="cyan")

            time.sleep(2)

        console.print(f"\n❌ Container Laravel não ficou pronto após {max_attempts * 2}s", style="red")
        return False

    def verify(self, max_attempts: int = 60) -> bool:
        """
        Verifica se Laravel está respondendo.

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

        # Verifica se PHP-FPM está respondendo (porta interna)
        # Como é container, vamos verificar se o processo está rodando
        try:
            result = subprocess.run(
                ["docker", "exec", self.container_name, "pgrep", "php-fpm"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                console.print(f"❌ PHP-FPM não está rodando no container", style="red")
                return False

        except Exception as e:
            console.print(f"❌ Erro ao verificar PHP-FPM: {e}", style="red")
            return False

        console.print(f"✅ {self.name} verificado", style="green")
        return True

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