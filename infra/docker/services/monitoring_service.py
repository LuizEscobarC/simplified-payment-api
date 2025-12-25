#!/usr/bin/env python3
"""
Serviço Elasticsearch para orquestração Docker.
"""

import time
from typing import Optional

from .base_service import BaseDockerService


class ElasticsearchService(BaseDockerService):
    """Serviço Elasticsearch."""

    def __init__(self):
        """Inicializa serviço Elasticsearch."""
        super().__init__(
            name="elasticsearch",
            container_name="payment-elasticsearch",
            image="elasticsearch:8.11.4",
            ports=["9200:9200", "9300:9300"],
            environment=[
                "discovery.type=single-node",
                "xpack.security.enabled=false",
                "ES_JAVA_OPTS=-Xms512m -Xmx512m"
            ],
            volumes=["elasticsearch_data:/usr/share/elasticsearch/data"],
            networks=["payment-api-main"],
            healthcheck={
                "test": ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            },
            compose_file=Path(__file__).parent.parent / "docker-compose.monitoring.yml"
        )

    def verify(self, max_attempts: int = 10) -> bool:
        """Verifica se Elasticsearch está respondendo."""
        return self._verify_http_endpoint(
            "http://localhost:9200/_cluster/health",
            expected_status=200,
            max_attempts=max_attempts
        )

    def start(self, wait: bool = True) -> bool:
        """
        Inicia serviço via Docker Compose.

        Args:
            wait: Aguardar serviço ficar pronto

        Returns:
            True se iniciou com sucesso
        """
        from pathlib import Path
        from rich.console import Console

        console = Console()
        console.print(f"🚀 Iniciando {self.name} via Docker Compose...", style="blue")

        try:
            # Usar docker-compose para iniciar o serviço
            result = self.run_compose_command(["up", "-d", "elasticsearch"])

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
        from pathlib import Path
        from rich.console import Console

        console = Console()
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


class LogstashService(BaseDockerService):
    """Serviço Logstash."""

    def __init__(self):
        """Inicializa serviço Logstash."""
        super().__init__(
            name="logstash",
            container_name="payment-logstash",
            image="logstash:8.11.4",
            ports=["5044:5044", "5000:5000", "9600:9600"],
            volumes=[
                "./monitoring/logstash.conf:/usr/share/logstash/pipeline/logstash.conf",
                "./monitoring/logstash.yml:/usr/share/logstash/config/logstash.yml"
            ],
            networks=["payment-api-main"],
            compose_file=Path(__file__).parent.parent / "docker-compose.monitoring.yml"
        )

    def verify(self, max_attempts: int = 10) -> bool:
        """Verifica se Logstash está respondendo."""
        return self._verify_http_endpoint(
            "http://localhost:9600",
            expected_status=200,
            max_attempts=max_attempts
        )

    def start(self, wait: bool = True) -> bool:
        """
        Inicia serviço via Docker Compose.

        Args:
            wait: Aguardar serviço ficar pronto

        Returns:
            True se iniciou com sucesso
        """
        from pathlib import Path
        from rich.console import Console

        console = Console()
        console.print(f"🚀 Iniciando {self.name} via Docker Compose...", style="blue")

        try:
            # Usar docker-compose para iniciar o serviço
            result = self.run_compose_command(["up", "-d", "logstash"])

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
        from pathlib import Path
        from rich.console import Console

        console = Console()
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


class KibanaService(BaseDockerService):
    """Serviço Kibana."""

    def __init__(self):
        """Inicializa serviço Kibana."""
        super().__init__(
            name="kibana",
            container_name="payment-kibana",
            image="kibana:8.11.4",
            ports=["5601:5601"],
            environment=["ELASTICSEARCH_HOSTS=http://elasticsearch:9200"],
            networks=["payment-api-main"],
            healthcheck={
                "test": ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            },
            compose_file=Path(__file__).parent.parent / "docker-compose.monitoring.yml"
        )

    def verify(self, max_attempts: int = 10) -> bool:
        """Verifica se Kibana está respondendo."""
        return self._verify_http_endpoint(
            "http://localhost:5601/api/status",
            expected_status=200,
            max_attempts=max_attempts,
            accept_statuses=[200, 503]  # 503 = inicializando, 200 = pronto
        )

    def start(self, wait: bool = True) -> bool:
        """
        Inicia serviço via Docker Compose.

        Args:
            wait: Aguardar serviço ficar pronto

        Returns:
            True se iniciou com sucesso
        """
        from pathlib import Path
        from rich.console import Console

        console = Console()
        console.print(f"🚀 Iniciando {self.name} via Docker Compose...", style="blue")

        try:
            # Usar docker-compose para iniciar o serviço
            result = self.run_compose_command(["up", "-d", "kibana"])

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
        from pathlib import Path
        from rich.console import Console

        console = Console()
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


class PrometheusService(BaseDockerService):
    """Serviço Prometheus."""

    def __init__(self):
        """Inicializa serviço Prometheus."""
        super().__init__(
            name="prometheus",
            container_name="payment-prometheus",
            image="prom/prometheus:latest",
            ports=["9090:9090"],
            volumes=[
                "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml",
                "prometheus_data:/prometheus"
            ],
            command=[
                "--config.file=/etc/prometheus/prometheus.yml",
                "--storage.tsdb.path=/prometheus",
                "--web.console.libraries=/etc/prometheus/console_libraries",
                "--web.console.templates=/etc/prometheus/consoles",
                "--storage.tsdb.retention.time=200h",
                "--web.enable-lifecycle"
            ],
            networks=["payment-api-main"],
            compose_file=Path(__file__).parent.parent / "docker-compose.monitoring.yml"
        )

    def verify(self, max_attempts: int = 10) -> bool:
        """Verifica se Prometheus está respondendo."""
        return self._verify_http_endpoint(
            "http://localhost:9090/-/healthy",
            expected_status=200,
            max_attempts=max_attempts
        )

    def start(self, wait: bool = True) -> bool:
        """
        Inicia serviço via Docker Compose.

        Args:
            wait: Aguardar serviço ficar pronto

        Returns:
            True se iniciou com sucesso
        """
        from pathlib import Path
        from rich.console import Console

        console = Console()
        console.print(f"🚀 Iniciando {self.name} via Docker Compose...", style="blue")

        try:
            # Usar docker-compose para iniciar o serviço
            result = self.run_compose_command(["up", "-d", "prometheus"])

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
        from pathlib import Path
        from rich.console import Console

        console = Console()
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