"""
MongoDB Service.

Gerencia o serviço MongoDB do ecossistema.
Similar ao RedisService, mas para MongoDB com sharding.
"""

from pathlib import Path
from typing import Optional
import time

from rich.console import Console

from .base_service import BaseDockerService

console = Console()


class MongoDBService(BaseDockerService):
    """Gerencia serviço MongoDB."""

    def __init__(
        self,
        container_name: str = "mongo"
    ):
        """
        Inicializa serviço MongoDB.

        Args:
            container_name: Nome do container MongoDB
        """
        super().__init__(
            name="MongoDB",
            container_name=container_name,
            image="mongo:7.0",
            ports=["27017:27017"],
            environment=[
                "MONGO_INITDB_ROOT_USERNAME=${MONGO_ROOT_USERNAME:-root}",
                "MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD:-root}"
            ],
            volumes=["mongo_data:/data/db"],
            networks=["payment-api-main"]
        )

    def verify(self, max_attempts: int = 30) -> bool:
        """
        Verifica se MongoDB está pronto.

        Args:
            max_attempts: Número máximo de tentativas

        Returns:
            True se pronto
        """
        console.print("⏳ Verificando MongoDB...", style="cyan")

        for attempt in range(max_attempts):
            try:
                # Verificar se container está rodando
                if not self.is_container_running():
                    if attempt % 5 == 0:
                        console.print(".", end="", style="cyan")
                    time.sleep(2)
                    continue

                # Testa conexão MongoDB
                test_result = self.run_docker_command([
                    "exec", self.container_name,
                    "mongosh", "--eval", "db.runCommand({ping: 1})"
                ])

                if test_result.returncode == 0 and "ok" in test_result.stdout:
                    console.print("\n✅ MongoDB pronto!", style="green")
                    return True

                if attempt % 5 == 0:
                    console.print(".", end="", style="cyan")

            except Exception:
                if attempt % 5 == 0:
                    console.print(".", end="", style="cyan")

            time.sleep(2)

        console.print(f"\n❌ MongoDB não ficou pronto no tempo esperado", style="red")
        return False


# Exemplo de uso direto
if __name__ == "__main__":
    mongo = MongoDBService()

    # Iniciar MongoDB
    if mongo.start():
        console.print("🎉 MongoDB iniciado com sucesso!", style="green")
    else:
        console.print("💥 Falha ao iniciar MongoDB", style="red")