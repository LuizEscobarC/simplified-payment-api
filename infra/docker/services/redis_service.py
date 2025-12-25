"""
Redis Global Service.

Gerencia o serviço Redis global do ecossistema ET.
Substitui a parte do setup.sh que gerencia o Redis.
"""

from pathlib import Path
from typing import Optional
import time
import os

from rich.console import Console

from .base_service import BaseDockerService

console = Console()


class RedisService(BaseDockerService):
    """Gerencia serviço Redis global."""

    def __init__(
        self,
        container_name: str = "payment-redis"
    ):
        """
        Inicializa serviço Redis.

        Args:
            container_name: Nome do container Redis
        """
        # Ler senha do Redis das variáveis de ambiente
        self.redis_password = os.getenv('REDIS_PASSWORD')

        super().__init__(
            name="Redis",
            container_name=container_name,
            image="redis:7-alpine",
            ports=["6377:6379"],
            volumes=["redis_data:/data", "./redis/redis.conf:/usr/local/etc/redis/redis.conf"],
            command=["redis-server", "/usr/local/etc/redis/redis.conf"],
            environment=[f"REDIS_PASSWORD={self.redis_password}"],
            networks=["payment-api-main"],
            healthcheck={
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "10s",
                "timeout": "3s",
                "retries": 3
            },
            compose_file=Path(__file__).parent.parent / "docker-compose.cache.yml"
        )

    def verify(self, max_attempts: int = 30) -> bool:
        """
        Verifica se Redis está pronto.

        Args:
            max_attempts: Número máximo de tentativas

        Returns:
            True se Redis está respondendo
        """
        console.print("⏳ Verificando Redis...", style="cyan")

        for attempt in range(1, max_attempts + 1):
            try:
                # Verificar se container está rodando
                if not self.is_container_running():
                    if attempt % 5 == 0:
                        console.print(".", end="", style="cyan")
                    time.sleep(1)
                    continue

                # Verificar healthcheck
                health_result = self.run_docker_command([
                    "exec", self.container_name, "redis-cli", "-a", self.redis_password, "ping"
                ])

                if health_result.returncode == 0 and "PONG" in health_result.stdout:
                    console.print("\n✅ Redis está pronto!", style="green")
                    return True

            except Exception:
                pass

            # Aguardar antes de próxima tentativa
            if attempt % 5 == 0:
                console.print(".", end="", style="cyan")
            time.sleep(1)

        console.print(f"\n❌ Redis timeout após {max_attempts}s", style="red")
        return False

    def start(self, wait: bool = True) -> bool:
        """
        Inicia serviço via Docker Compose.

        Args:
            wait: Aguardar serviço ficar pronto

        Returns:
            True se iniciou com sucesso
        """
        console.print(f"🚀 Iniciando {self.name} via Docker Compose...", style="blue")

        try:
            # Usar docker-compose para iniciar o serviço
            result = self.run_compose_command(["up", "-d", "payment-redis"])

            if result.returncode != 0:
                console.print(f"❌ Falha ao iniciar {self.name}: {result.stderr}", style="red")
                return False

            console.print(f"✅ {self.name} iniciado!", style="green")

            if wait:
                return self.verify()
            return True

        except Exception as e:
            console.print(f"❌ Erro ao iniciar {self.name}: {e}", style="red")
            return False

    def stop(self) -> bool:
        """
        Para serviço via Docker Compose.

        Returns:
            True se parou com sucesso
        """
        console.print(f"🛑 Parando {self.name}...", style="yellow")

        try:
            result = self.run_compose_command(["down"])

            if result.returncode != 0:
                console.print(f"❌ Falha ao parar {self.name}: {result.stderr}", style="red")
                return False

            console.print(f"✅ {self.name} parado!", style="green")
            return True

        except Exception as e:
            console.print(f"❌ Erro ao parar {self.name}: {e}", style="red")
            return False


# Exemplo de uso direto
if __name__ == "__main__":
    redis = RedisService()
    
    # Iniciar Redis
    if redis.start():
        print("Redis iniciado com sucesso!")
        
        # Verificar
        if redis.verify():
            print("Redis verificado!")
    else:
        print("Falha ao iniciar Redis")
