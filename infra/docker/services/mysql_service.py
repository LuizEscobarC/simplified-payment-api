"""
MySQL Service.

Gerencia o serviço MySQL do ecossistema.
Similar ao RedisService, mas para MySQL com replicação master-slave.
"""

from pathlib import Path
from typing import Optional
import time
import os

from rich.console import Console

from .base_service import BaseDockerService

console = Console()


class MySQLService(BaseDockerService):
    """Gerencia serviço MySQL com replicação."""

    def __init__(
        self,
        container_name: str = "payment-mysql"
    ):
        """
        Inicializa serviço MySQL.

        Args:
            container_name: Nome do container master
        """
        super().__init__(
            name="MySQL",
            container_name=container_name,
            image="mysql:8.0",
            ports=["3307:3306"],
            environment=[
                "MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}",
                "MYSQL_DATABASE=${MYSQL_DATABASE:-payment_db}",
                "MYSQL_USER=${MYSQL_USER:-payment_user}",
                "MYSQL_PASSWORD=${MYSQL_PASSWORD}"
            ],
            volumes=["mysql_data:/var/lib/mysql", "./mysql/my.cnf:/etc/mysql/conf.d/my.cnf"],
            networks=["payment-api-main"],
            healthcheck={
                "test": ["CMD", "mysqladmin", "ping", "-h", "localhost"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 3
            },
            command=["--default-authentication-plugin=mysql_native_password"]
        )

    def verify(self, max_attempts: int = 30) -> bool:
        """
        Verifica se MySQL está pronto.

        Args:
            max_attempts: Número máximo de tentativas

        Returns:
            True se MySQL está respondendo
        """
        console.print("⏳ Verificando MySQL...", style="cyan")

        for attempt in range(max_attempts):
            try:
                # Primeiro verifica se container está rodando
                if not self.is_container_running():
                    if attempt % 5 == 0:
                        console.print(".", end="", style="cyan")
                    time.sleep(2)
                    continue

                # Testa conexão MySQL executando um SELECT simples
                test_result = self.run_docker_command([
                    "exec", self.container_name,
                    "mysql", "-u", "root", f"-p{os.getenv('MYSQL_ROOT_PASSWORD')}", "-e", "SELECT 1;"
                ])

                if test_result.returncode == 0:
                    console.print("\n✅ MySQL pronto!", style="green")
                    return True

                if attempt % 5 == 0:
                    console.print(".", end="", style="cyan")

            except Exception:
                if attempt % 5 == 0:
                    console.print(".", end="", style="cyan")

            time.sleep(2)

        console.print(f"\n❌ MySQL não ficou pronto no tempo esperado", style="red")
        return False


# Exemplo de uso direto
if __name__ == "__main__":
    mysql = MySQLService()

    # Iniciar MySQL
    if mysql.start():
        console.print("🎉 MySQL iniciado com sucesso!", style="green")
    else:
        console.print("💥 Falha ao iniciar MySQL", style="red")