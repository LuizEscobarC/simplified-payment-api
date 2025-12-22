#!/usr/bin/env python3
"""
Orquestrador Automático de Setup.

Inicia todos os serviços necessários para o projeto de API de pagamentos.
Usa as classes de serviço para gerenciar Docker containers automaticamente.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from enum import Enum

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

# Adicionar caminho para importar serviços
sys.path.append(str(Path(__file__).parent))

from services.redis_service import RedisService
from services.mysql_service import MySQLService
from services.mongodb_service import MongoDBService
from services.laravel_service import LaravelService
from services.nginx_service import NginxService
from services.monitoring_service import ElasticsearchService, LogstashService, KibanaService, PrometheusService
from services.git_hooks_service import GitHooksService
from scripts.prerequisites import PrerequisiteChecker
from scripts.env_manager import LaravelEnvManager
from scripts import DockerNetworkManager

console = Console()


class ServiceState(Enum):
    """Estados possíveis de um serviço."""
    PENDING = "pending"
    STARTING = "starting"
    VERIFYING = "verifying"
    READY = "ready"
    FAILED = "failed"


class ServiceOrchestrator:
    """Orquestra o startup de todos os serviços."""

    def __init__(self, include_monitoring: bool = False):
        """Inicializa orquestrador."""
        # Gerenciador de redes customizadas
        self.network_manager = DockerNetworkManager()

        self.services = {
            'redis': RedisService(),
            'mysql': MySQLService(),
            'mongodb': MongoDBService(),
            'laravel': LaravelService(),
            'nginx': NginxService(),
            'git-hooks': GitHooksService()
        }

        if include_monitoring:
            self.services.update({
                'elasticsearch': ElasticsearchService(),
                'logstash': LogstashService(),
                'kibana': KibanaService(),
                'prometheus': PrometheusService()
            })

        # Estado de cada serviço
        self.service_states = {name: ServiceState.PENDING for name in self.services.keys()}
        self.include_monitoring = include_monitoring

    def check_prerequisites(self) -> bool:
        """
        Verifica pré-requisitos do sistema antes de iniciar serviços.

        Returns:
            True se todos os pré-requisitos estão OK
        """
        console.print("🔍 Verificando pré-requisitos do sistema...", style="bold cyan")

        checker = PrerequisiteChecker()
        success = checker.check_all(show_progress=True)

        if not success:
            console.print("\n❌ Pré-requisitos não atendidos!", style="bold red")
            console.print("💡 Sugestões de correção:", style="yellow")

            suggestions = checker.get_fix_suggestions()
            for suggestion in suggestions:
                console.print(f"   • {suggestion}", style="yellow")

            console.print("\n🔄 Execute novamente após corrigir os problemas.", style="cyan")
            return False

        console.print("✅ Todos os pré-requisitos verificados com sucesso!", style="bold green")

        # Validação obrigatória das variáveis de ambiente
        console.print("\n🔍 Verificando variáveis de ambiente obrigatórias...", style="bold cyan")

        # Caminho absoluto para o arquivo .env
        project_root = Path(__file__).parent.parent.parent
        env_file_path = project_root / "infra" / "docker" / ".env"
        env_manager = LaravelEnvManager(env_file=str(env_file_path))
        env_success = env_manager.setup_laravel_env()

        if not env_success:
            console.print("\n❌ Variáveis de ambiente obrigatórias não configuradas!", style="bold red")
            console.print("💡 Sugestões de correção:", style="yellow")
            console.print("   • Copie .env.example para .env: cp .env.example .env", style="yellow")
            console.print("   • Configure todas as variáveis obrigatórias no arquivo .env", style="yellow")
            console.print("\n🔄 Execute novamente após corrigir os problemas.", style="cyan")
            return False

        console.print("✅ Variáveis de ambiente validadas com sucesso!", style="bold green")
        return True

    def update_service_state(self, service_name: str, state: ServiceState) -> None:
        """
        Atualiza o estado de um serviço.

        Args:
            service_name: Nome do serviço
            state: Novo estado
        """
        self.service_states[service_name] = state
        console.print(f"📊 {service_name.upper()} -> {state.value}", style="cyan")

    def start_service_with_state_machine(self, service_name: str, progress: Progress, task_id) -> bool:
        """
        Inicia um serviço usando padrão de máquina de estados.

        Args:
            service_name: Nome do serviço
            progress: Instância do Progress
            task_id: ID da tarefa no progress

        Returns:
            True se serviço iniciou com sucesso
        """
        service = self.services[service_name]

        try:
            # Estado: STARTING
            self.update_service_state(service_name, ServiceState.STARTING)
            progress.update(task_id, description=f"Iniciando {service_name.upper()}...")

            # Tentar iniciar o serviço
            if not service.start(wait=False):
                self.update_service_state(service_name, ServiceState.FAILED)
                progress.update(task_id, description=f"❌ {service_name.upper()} falhou ao iniciar")
                return False

            # Estado: VERIFYING
            self.update_service_state(service_name, ServiceState.VERIFYING)
            progress.update(task_id, description=f"Verificando {service_name.upper()}...")

            # Aguardar e verificar se está pronto
            if service.verify():
                self.update_service_state(service_name, ServiceState.READY)
                progress.update(task_id, description=f"✅ {service_name.upper()} pronto")
                return True
            else:
                self.update_service_state(service_name, ServiceState.FAILED)
                progress.update(task_id, description=f"❌ {service_name.upper()} falhou na verificação")
                return False

        except Exception as e:
            self.update_service_state(service_name, ServiceState.FAILED)
            progress.update(task_id, description=f"💥 {service_name.upper()} erro: {str(e)[:30]}...")
            return False

    def start_all_services(self, skip_prerequisites: bool = False) -> bool:
        """
        Inicia todos os serviços em ordem usando padrão de máquina de estados.

        Ordem: Pré-requisitos -> Redes -> Redis -> MySQL -> MongoDB -> Laravel -> Nginx
        Cada serviço passa por: PENDING -> STARTING -> VERIFYING -> READY/FAILED

        Returns:
            True se todos iniciaram com sucesso
        """
        console.print("🚀 Iniciando orquestração automática de serviços...", style="bold blue")

        # 0. Verificar pré-requisitos do sistema
        if not skip_prerequisites and not self.check_prerequisites():
            return False

        # 1. Criar redes customizadas (sempre obrigatório)
        console.print("\n🌐 Preparando redes customizadas...", style="cyan")
        if not self.network_manager.create_all_networks():
            console.print("❌ Falha ao criar redes customizadas", style="red")
            return False

        # 2. Atualizar arquivos docker-compose
        console.print("\n📝 Atualizando configurações de rede...", style="cyan")
        if not self.network_manager.update_compose_files():
            console.print("⚠️  Alguns arquivos docker-compose podem não ter sido atualizados", style="yellow")

        # Ordem de inicialização (dependências)
        startup_order = ['redis', 'mysql', 'mongodb', 'laravel', 'nginx']

        if self.include_monitoring:
            startup_order.extend(['elasticsearch', 'logstash', 'kibana', 'prometheus'])

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:

            overall_task = progress.add_task("Iniciando serviços...", total=len(startup_order))

            for service_name in startup_order:
                # Criar tarefa específica para este serviço
                service_task = progress.add_task(f"Preparando {service_name.upper()}...", total=1)

                # Iniciar serviço usando máquina de estados
                success = self.start_service_with_state_machine(service_name, progress, service_task)

                if not success:
                    progress.update(overall_task, description="❌ Alguns serviços falharam")
                    return False

                progress.update(service_task, completed=1)
                progress.update(overall_task, advance=1)

                # Pequena pausa entre serviços para estabilização
                time.sleep(2)

        return self._verify_all_services()

    def _verify_all_services(self) -> bool:
        """Verifica se todos os serviços estão funcionando."""
        console.print("\n🔍 Verificando status final dos serviços...", style="blue")

        all_ok = True
        for name, service in self.services.items():
            if hasattr(service, 'verify'):
                if service.verify(max_attempts=10):
                    console.print(f"✅ {name.upper()} verificado", style="green")
                else:
                    console.print(f"❌ {name.upper()} falhou na verificação", style="red")
                    all_ok = False

        return all_ok

    def show_status(self) -> None:
        """Exibe o status de todos os serviços e redes."""
        console.print("📊 Status dos Serviços e Redes", style="bold blue")
        console.print("=" * 50, style="blue")

        # Status das redes
        console.print("\n🌐 Redes Docker Customizadas:", style="cyan")
        self.network_manager.show_network_status()

        # Status dos serviços
        console.print("\n🔧 Serviços:", style="cyan")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Serviço", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Porta", style="yellow")
        table.add_column("Container", style="white")

        for name, service in self.services.items():
            status = self._check_service_status(name, service)
            port = getattr(service, 'port', 'N/A')
            container = getattr(service, 'container_name', 'N/A')
            table.add_row(name.upper(), status, str(port), container)

        console.print(table)

    def stop_all_services(self) -> bool:
        """Para todos os serviços."""
        console.print("🛑 Parando todos os serviços...", style="yellow")

        success = True
        for name, service in self.services.items():
            try:
                if not service.stop():
                    success = False
            except Exception as e:
                console.print(f"❌ Erro ao parar {name.upper()}: {e}", style="red")
                success = False

        return success

    def _check_service_status(self, service_name: str, service) -> str:
        """
        Verifica o status real de um serviço.

        Args:
            service_name: Nome do serviço
            service: Instância do serviço

        Returns:
            String com status formatado
        """
        try:
            # Primeiro verifica se está no status armazenado
            if service_name in self.status:
                return self.status[service_name]

            # Se não tem status armazenado, verifica se o container está rodando
            if hasattr(service, 'container_name'):
                import subprocess
                result = subprocess.run(
                    ["docker", "ps", "--filter", f"name={service.container_name}", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0 and result.stdout.strip():
                    status = result.stdout.strip()
                    if "Up" in status:
                        return "✅ Rodando"
                    else:
                        return f"⚠️  {status}"

            return "❌ Parado"

        except Exception as e:
            return f"❌ Erro: {str(e)}"

    def show_status(self):
        """Exibe status de todos os serviços e redes usando máquina de estados."""
        # Status das redes
        console.print("\n🌐 Redes Customizadas:", style="bold blue")
        self.network_manager.show_network_status()

        # Status dos serviços
        table = Table(title="📊 Status dos Serviços")
        table.add_column("Serviço", style="cyan", no_wrap=True)
        table.add_column("Estado", style="magenta")

        for name, state in self.service_states.items():
            service = self.services[name]
            container = getattr(service, 'container_name', 'N/A')
            
            # Mapeia estado para emoji
            state_emoji = {
                ServiceState.PENDING: "⏳",
                ServiceState.STARTING: "🚀",
                ServiceState.VERIFYING: "🔍",
                ServiceState.READY: "✅",
                ServiceState.FAILED: "❌"
            }.get(state, "❓")
            
            table.add_row(f"{name.upper()}", f"{state_emoji} {state.value}")

        console.print(table)

    def cleanup_all(self):
        """Limpa containers existentes."""
        console.print("🧹 Limpando containers existentes...", style="yellow")

        for name, service in self.services.items():
            try:
                service.cleanup_existing()
                console.print(f"✅ {name.upper()} limpo", style="green")
            except Exception as e:
                console.print(f"⚠️  Erro ao limpar {name.upper()}: {e}", style="yellow")


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Orquestrador de Serviços para API de Pagamentos")
    parser.add_argument("action", choices=["start", "stop", "status", "cleanup", "hooks"],
                       help="Ação a executar")
    parser.add_argument("--no-wait", action="store_true",
                       help="Não aguardar serviços ficarem prontos")
    parser.add_argument("--monitoring", action="store_true",
                       help="Incluir serviços de monitoramento (ELK + Prometheus)")
    parser.add_argument("--skip-prerequisites", action="store_true",
                       help="Pular verificação de pré-requisitos do sistema")

    args = parser.parse_args()

    orchestrator = ServiceOrchestrator(include_monitoring=args.monitoring)

    if args.action == "start":
        success = orchestrator.start_all_services(skip_prerequisites=args.skip_prerequisites)
        if success:
            console.print("\n🎉 Todos os serviços iniciados com sucesso!", style="bold green")
            console.print("💡 Você pode acessar:", style="blue")
            console.print("   - Redis: localhost:6379", style="white")
            console.print("   - MySQL: localhost:3306 (user: root, pass: root)", style="white")
            console.print("   - MongoDB: localhost:27017", style="white")
            console.print("   - Laravel API: http://localhost/api", style="white")
            console.print("   - Nginx: http://localhost", style="white")
            if orchestrator.include_monitoring:
                console.print("   - Elasticsearch: localhost:9200", style="white")
                console.print("   - Logstash: localhost:9600", style="white")
                console.print("   - Kibana: localhost:5601", style="white")
                console.print("   - Prometheus: localhost:9090", style="white")
        else:
            console.print("\n💥 Falha ao iniciar alguns serviços!", style="bold red")
            orchestrator.show_status()
            sys.exit(1)

    elif args.action == "stop":
        if orchestrator.stop_all_services():
            console.print("✅ Todos os serviços parados", style="green")
        else:
            console.print("❌ Erro ao parar serviços", style="red")
            sys.exit(1)

    elif args.action == "status":
        orchestrator.show_status()

    elif args.action == "cleanup":
        orchestrator.cleanup_all()

    elif args.action == "hooks":
        hooks_service = GitHooksService()
        if hooks_service.start():
            console.print("✅ Git hooks configurados com sucesso!", style="green")
        else:
            console.print("❌ Falha ao configurar Git hooks!", style="red")
            sys.exit(1)


if __name__ == "__main__":
    main()