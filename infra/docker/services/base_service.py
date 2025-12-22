# infra/docker/services/base_service.py
"""
Classe base simplificada para serviços Docker.

Fornece funcionalidades comuns para gerenciar containers Docker Compose.
"""

import subprocess
import time
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.console import Console

console = Console()


class BaseDockerService(ABC):
    """
    Classe base para serviços Docker Compose.

    Fornece métodos comuns para start, stop, verify, logs e cleanup.
    """

    def __init__(
        self,
        name: str,
        container_name: str = "",
        image: str = "",
        ports: Optional[List[str]] = None,
        environment: Optional[List[str]] = None,
        volumes: Optional[List[str]] = None,
        networks: Optional[List[str]] = None,
        depends_on: Optional[List[str]] = None,
        healthcheck: Optional[Dict[str, Any]] = None,
        command: Optional[List[str]] = None,
        compose_file: Optional[Path] = None
    ):
        """
        Inicializa serviço Docker.

        Args:
            name: Nome do serviço
            container_name: Nome do container
            image: Imagem Docker
            ports: Lista de mapeamentos de porta
            environment: Variáveis de ambiente
            volumes: Volumes
            networks: Redes
            depends_on: Dependências
            healthcheck: Configuração de healthcheck
            command: Comando customizado
            compose_file: Caminho para docker-compose.yml
        """
        self.name = name
        self.container_name = container_name or name.lower()
        self.image = image
        self.ports = ports or []
        self.environment = environment or []
        self.volumes = volumes or []
        self.networks = networks or []
        self.depends_on = depends_on or []
        self.healthcheck = healthcheck
        self.command = command or []

        # Define caminho do compose file
        if compose_file is None:
            self.compose_file = Path(__file__).parent.parent / "docker-compose.local.yml"
        else:
            self.compose_file = compose_file

    def _verify_http_endpoint(self, url: str, expected_status: int = 200, max_attempts: int = 10, accept_statuses: Optional[List[int]] = None) -> bool:
        """
        Verifica endpoint HTTP.

        Args:
            url: URL para verificar
            expected_status: Status esperado (padrão)
            max_attempts: Máximo de tentativas
            accept_statuses: Lista de status aceitáveis

        Returns:
            True se endpoint responde corretamente
        """
        if accept_statuses is None:
            accept_statuses = [expected_status]

        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code in accept_statuses:
                    return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def cleanup_existing(self) -> None:
        """Remove container existente se houver conflito."""
        try:
            # Forçar remoção do container
            result = self.run_docker_command(["rm", "-f", self.container_name])
            if result.returncode == 0:
                console.print(f"✓ Cleanup executado para {self.container_name}", style="yellow")
        except Exception as e:
            console.print(f"⚠️  Erro no cleanup: {e}", style="yellow")

    def run_compose_command(self, command: list, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """
        Executa comando docker-compose.

        Args:
            command: Lista com comando docker-compose
            cwd: Diretório de trabalho

        Returns:
            Resultado do subprocess
        """
        full_command = ["docker", "compose", "-f", str(self.compose_file)] + command
        return subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            cwd=cwd or self.compose_file.parent
        )

    def run_docker_command(self, command: list) -> subprocess.CompletedProcess:
        """
        Executa comando docker.

        Args:
            command: Lista com comando docker

        Returns:
            Resultado do subprocess
        """
        full_command = ["docker"] + command
        return subprocess.run(
            full_command,
            capture_output=True,
            text=True
        )

    def is_container_running(self) -> bool:
        """
        Verifica se container está rodando.

        Returns:
            True se container está up
        """
        result = self.run_docker_command([
            "inspect", "-f", "{{.State.Running}}", self.container_name
        ])

        return result.returncode == 0 and result.stdout.strip() == "true"

    def start(self, wait: bool = True) -> bool:
        """
        Inicia serviço via Docker.

        Args:
            wait: Aguardar serviço ficar pronto

        Returns:
            True se iniciou com sucesso
        """
        console.print(f"🚀 Iniciando {self.name}...", style="blue")

        self.cleanup_existing()

        # Criar networks se necessário
        for network in self.networks:
            self._ensure_network_exists(network)

        try:
            # Construir comando docker run
            cmd = ["run", "-d", "--name", self.container_name]

            # Adicionar portas
            for port in self.ports:
                cmd.extend(["-p", port])

            # Adicionar environment
            for env in self.environment:
                cmd.extend(["-e", env])

            # Adicionar volumes
            for volume in self.volumes:
                cmd.extend(["-v", volume])

            # Adicionar networks
            for network in self.networks:
                cmd.extend(["--network", network])

            # Adicionar healthcheck se existir
            if self.healthcheck:
                health_cmd = self.healthcheck.get("test", [])
                if health_cmd:
                    cmd.extend(["--health-cmd", " ".join(health_cmd[1:])])  # Remove CMD-SHELL
                    cmd.extend(["--health-interval", self.healthcheck.get("interval", "30s")])
                    cmd.extend(["--health-timeout", self.healthcheck.get("timeout", "10s")])
                    cmd.extend(["--health-retries", str(self.healthcheck.get("retries", 3))])

            # Adicionar imagem
            cmd.append(self.image)

            # Adicionar comando customizado
            if self.command:
                cmd.extend(self.command)

            result = self.run_docker_command(cmd)

            if result.returncode != 0:
                console.print(f"❌ Erro ao iniciar {self.name}: {result.stderr}", style="red")
                return False

            console.print(f"✅ {self.name} iniciado", style="green")

            if wait:
                return self.verify()

            return True

        except Exception as e:
            console.print(f"❌ Erro ao iniciar {self.name}: {e}", style="red")
            return False

    def _ensure_network_exists(self, network_name: str) -> None:
        """
        Garante que a rede Docker existe.

        Args:
            network_name: Nome da rede
        """
        try:
            result = self.run_docker_command(["network", "ls", "--format", "{{.Name}}"])
            if network_name not in result.stdout.split():
                self.run_docker_command(["network", "create", network_name])
                console.print(f"✓ Rede {network_name} criada", style="green")
        except Exception as e:
            console.print(f"⚠️  Erro ao verificar/criar rede {network_name}: {e}", style="yellow")

    def stop(self) -> bool:
        """
        Para serviço.

        Returns:
            True se parou com sucesso
        """
        console.print(f"🛑 Parando {self.name}...", style="yellow")

        try:
            # Parar container
            result = self.run_docker_command(["stop", self.container_name])

            if result.returncode != 0:
                console.print(f"❌ Erro ao parar {self.name}: {result.stderr}", style="red")
                return False

            # Remover container
            self.run_docker_command(["rm", self.container_name])

            console.print(f"✅ {self.name} parado", style="green")
            return True

        except Exception as e:
            console.print(f"❌ Erro ao parar {self.name}: {e}", style="red")
            return False

        except Exception as e:
            console.print(f"❌ Erro ao parar {self.name}: {e}", style="red")
            return False

    @abstractmethod
    def verify(self, max_attempts: int = 30) -> bool:
        """
        Verifica se serviço está pronto.

        Args:
            max_attempts: Número máximo de tentativas

        Returns:
            True se serviço está pronto
        """
        pass

    def logs(self, follow: bool = False, tail: int = 100) -> None:
        """
        Exibe logs do serviço.

        Args:
            follow: Seguir logs em tempo real
            tail: Número de linhas a exibir
        """
        cmd = ["logs", self.get_service_name()]

        if follow:
            cmd.append("-f")

        cmd.extend(["--tail", str(tail)])

        try:
            result = self.run_compose_command(cmd)
            if result.returncode == 0:
                print(result.stdout)
            else:
                console.print(f"❌ Erro ao exibir logs: {result.stderr}", style="red")
        except Exception as e:
            console.print(f"❌ Erro ao exibir logs: {e}", style="red")

    def restart(self) -> bool:
        """
        Reinicia serviço.

        Returns:
            True se reiniciou com sucesso
        """
        if self.stop():
            time.sleep(2)
            return self.start()
        return False